"""Data alerts: evaluate a rule on a governed series and email the result.

This file is used in TWO places, so it imports nothing from the app (standard library + a Snowpark session):
  1. the app (Check now, the preview, Send test email);
  2. the stored procedure AA_RUN_ALERTS, whose body IS this file's text (alerts.proc_ddl), run hourly by the task
     AA_ALERTS_TASK.
The check SQL is built by the app from the semantic view when the alert is saved and stored with it; nothing here
writes SQL from user text. Emails go through SYSTEM$SEND_EMAIL with a notification integration.
"""
import datetime as dt
import html
import json
import uuid

CORE_VERSION = "alerts-core-2"
DEFAULT_INTEGRATION = "AA_EMAIL_INT"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------------------------------------------------------------------------------------------ small helpers
def _num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def _date(v):
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def fmt(v, kind):
    if v is None:
        return "no value"
    if kind == "percent":
        return f"{v * 100:.1f}%"
    a = abs(v)
    s = f"{a / 1e9:.2f}B" if a >= 1e9 else f"{a / 1e6:.2f}M" if a >= 1e6 else f"{a / 1e3:.1f}K" if a >= 1e4 else f"{a:,.0f}" if a >= 100 else f"{a:,.2f}"
    return ("-" if v < 0 else "") + ("$" if kind == "currency" else "") + s


def _n(v):
    x = _num(v)
    return "?" if x is None else (f"{x:g}")


def period_label(d, grain):
    if d is None:
        return ""
    if grain == "month":
        return d.strftime("%b %Y")
    if grain == "week":
        return "week of " + d.strftime("%d %b %Y").lstrip("0")
    return d.strftime("%a %d %b %Y")


def _year_before(d, grain):
    if grain == "week":
        return d - dt.timedelta(weeks=52)
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        return d.replace(year=d.year - 1, day=28)


def _tz(name):
    """The alert's time zone; zoneinfo, else pytz (Snowflake's Python sandbox may lack the tz database)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name or "UTC")
    except Exception:
        try:
            import pytz
            return pytz.timezone(name or "UTC")
        except Exception:
            return dt.timezone.utc


# ------------------------------------------------------------------------------------------------ the rule
def threshold_text(spec):
    k = spec.get("kind")
    r = spec.get("rule")
    if r == "threshold":
        v = _num(spec.get("value"))
        return f"{spec.get('op', 'below')} {fmt(v, k) if v is not None else '… (enter a value)'}"
    if r == "change":
        pt = " pt" if k == "percent" else "%"
        d = {"down": "falls", "up": "rises", "either": "moves"}.get(spec.get("direction"), "moves")
        unit = {"day": "day", "week": "week", "month": "month"}.get(spec.get("grain"), "period")
        base = f"the same {unit} last year" if spec.get("compare") == "year" else f"the previous {unit}"
        return f"{d} by {_n(spec.get('pct'))}{pt} or more vs {base}"
    if r == "plan":
        return f"{'below' if spec.get('plan_dir', 'below') == 'below' else 'above'} plan by {_n(spec.get('pct'))}% or more"
    if r == "freshness":
        return f"has no new data for more than {spec.get('days')} day(s)"
    return ""


def describe(spec):
    """The alert as one plain sentence (shown in the form, the list and the email)."""
    flt = "; ".join(f"{k} = {', '.join(v)}" for k, v in (spec.get("filter_labels") or {}).items())
    where = f" for {flt}" if flt else ""
    if spec.get("rule") == "freshness":
        return f"{spec.get('metric_label')}{where} {threshold_text(spec)}"
    per = {"day": "latest full day", "week": "latest full week", "month": "latest full month"}.get(spec.get("grain"), "latest period")
    return f"{spec.get('metric_label')}{where} in the {per} {'is ' if spec.get('rule') in ('threshold', 'plan') else ''}" \
           f"{threshold_text(spec)}"


MONEY_WORDS = ("sales", "revenue", "margin", "cost", "profit", "amount", "price", "spend", "value", "income", "cogs")


def _kind(spec, values):
    """The unit to show. A ratio-looking metric whose values are not fractions is an amount (GROSS_MARGIN $)."""
    k = spec.get("kind") or "number"
    if k == "percent" and any(v is not None and abs(v) > 1.5 for v in values):
        lab = str(spec.get("metric_label") or "").lower()
        return "currency" if any(w in lab for w in MONEY_WORDS) else "number"
    return k


def _complete(series, grain, today):
    """Only finished periods: today's data (or this week / month so far) is still arriving, so comparing it with a
    full day a year ago would raise false alerts."""
    def end(d):
        if grain == "month":
            return (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        return d + dt.timedelta(days=7 if grain == "week" else 1)
    return [x for x in series if end(x[0]) <= today]


def _base_before(d, grain):
    """Same period last year: same weekday a year ago for days and weeks (retail calendar), same month for months."""
    if grain == "day":
        return d - dt.timedelta(days=364)
    if grain == "week":
        return d - dt.timedelta(weeks=52)
    return _year_before(d, grain)


def _chg_text(ch, kind):
    return f"{ch * 100:+.1f} pt" if kind == "percent" else f"{ch * 100:+.1f}%"


def evaluate(spec, rows, now_utc=None):
    """rows = check SQL result (PERIOD, M0[, M1]). Returns the outcome; never sends anything.
    Also returns 'headline' (what happened, in words) and 'facts' (label, value) for the email and the app."""
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    grain, rule = spec.get("grain", "day"), spec.get("rule")
    today = now_utc.astimezone(_tz((spec.get("schedule") or {}).get("tz"))).date()
    series = []
    for r in rows:
        low = {str(k).lower(): v for k, v in r.items()}
        d = _date(low.get("period"))
        if d is not None:
            series.append((d, _num(low.get("m0")), _num(low.get("m1"))))
    series.sort(key=lambda x: x[0])
    have_all = [x for x in series if x[1] is not None]
    kind = _kind(spec, [x[1] for x in have_all])
    name = spec.get("metric_label") or "The metric"
    flt = "; ".join(f"{k} = {', '.join(v)}" for k, v in (spec.get("filter_labels") or {}).items()) or "All data"
    out = {"status": "ok", "value": None, "compare": None, "period": None, "period_label": "", "key": "",
           "detail": "", "fired": False, "kind": kind, "headline": "", "facts": []}
    if rule == "freshness":
        if not have_all:
            out.update(status="fired", fired=True, key="stale:none", headline=f"No {name} data at all",
                       detail="The check returned no data for this alert's filters.",
                       facts=[["Filters", flt], ["Your rule", threshold_text(spec)]])
            return out
        d = have_all[-1][0]
        age = (today - d).days
        lim = int(spec.get("days") or 1)
        out.update(value=have_all[-1][1], compare=age, period=d.isoformat(), period_label=period_label(d, "day"),
                   key=f"stale:{d.isoformat()}", fired=age > lim,
                   detail=f"Latest data is from {d:%d %b %Y}, {age} day(s) ago (limit {lim}).",
                   headline=(f"No new {name} data for {age} days" if age > lim else f"{name} data is up to date"),
                   facts=[["Latest data", f"{d:%a %d %b %Y}"], ["Days without new data", str(age)],
                          ["Filters", flt], ["Your rule", threshold_text(spec)]])
        out["status"] = "fired" if out["fired"] else "ok"
        return out
    have = _complete(have_all, grain, today)
    if not have:
        out.update(status="no_data", detail="No finished period with data yet (filters may exclude everything).")
        return out
    d, v, p = have[-1]
    unit = {"day": "day", "week": "week", "month": "month"}.get(grain, "period")
    out.update(value=v, period=d.isoformat(), period_label=period_label(d, grain))
    facts = [[f"{name}, {period_label(d, grain)}", fmt(v, kind)]]
    if _num(spec.get("value" if rule == "threshold" else "pct")) is None:
        out.update(status="incomplete", detail="The alert has no limit yet: enter the value to compare with.")
        return out
    if rule == "threshold":
        t = _num(spec.get("value"))
        below = spec.get("op", "below") == "below"
        out["compare"] = t
        out["fired"] = (v < t) if below else (v > t)
        prev = have[-2] if len(have) > 1 else None
        out["headline"] = (f"{name} is {fmt(v, kind)}, {'below' if below else 'above'} your limit of {fmt(t, kind)}"
                           if out["fired"] else f"{name} is {fmt(v, kind)}, within your limit of {fmt(t, kind)}")
        facts.append(["Your limit", f"{'below' if below else 'above'} {fmt(t, kind)}"])
        if prev:
            facts.append([f"Previous {unit} ({period_label(prev[0], grain)})", fmt(prev[1], kind)])
        out["detail"] = f"{fmt(v, kind)} vs limit {fmt(t, kind)}"
    elif rule == "change":
        if spec.get("compare") == "year":
            want = _base_before(d, grain)
            base_row = next((x for x in have if x[0] == want), None)
            base_name = f"same {unit} last year"
        else:
            base_row = have[-2] if len(have) > 1 else None
            base_name = f"previous {unit}"
        if not base_row or base_row[1] is None:
            out.update(status="no_data", detail=f"No value for the {base_name} to compare with.")
            return out
        b = base_row[1]
        if kind != "percent" and b == 0:
            out.update(status="no_data", detail="The comparison value is zero.")
            return out
        ch = v - b if kind == "percent" else (v - b) / abs(b)
        t = (_num(spec.get("pct")) or 0) / 100.0
        dirn = spec.get("direction", "either")
        out["compare"] = b
        out["fired"] = (ch <= -t) if dirn == "down" else (ch >= t) if dirn == "up" else (abs(ch) >= t)
        moved = "fell" if ch < 0 else "rose"
        size = f"{abs(ch) * 100:.1f} pt" if kind == "percent" else f"{abs(ch) * 100:.1f}%"
        out["headline"] = f"{name} {moved} {size} vs the {base_name}"
        facts += [[f"{base_name.capitalize()} ({period_label(base_row[0], grain)})", fmt(b, kind)],
                  ["Change", _chg_text(ch, kind)]]
        out["detail"] = f"{fmt(v, kind)} vs {fmt(b, kind)} on {period_label(base_row[0], grain)} ({_chg_text(ch, kind)})"
    elif rule == "plan":
        if p is None or p == 0:
            out.update(status="no_data", detail="No plan value for this period.")
            return out
        gap = (v - p) / abs(p)
        t = (_num(spec.get("pct")) or 0) / 100.0
        out["compare"] = p
        out["fired"] = (gap <= -t) if spec.get("plan_dir", "below") == "below" else (gap >= t)
        out["headline"] = f"{name} is {abs(gap) * 100:.1f}% {'below' if gap < 0 else 'above'} plan"
        facts += [["Plan", fmt(p, kind)], ["Vs plan", f"{gap * 100:+.1f}%"]]
        out["detail"] = f"{fmt(v, kind)} vs plan {fmt(p, kind)} ({gap * 100:+.1f}%)"
    facts += [["Filters", flt], ["Your rule", threshold_text({**spec, "kind": kind})]]
    out["facts"] = facts
    out["status"] = "fired" if out["fired"] else "ok"
    out["key"] = f"{rule}:{out['period']}"
    return out


# ------------------------------------------------------------------------------------------------ schedule
def last_slot(schedule, now_utc):
    """The most recent moment the alert was due (UTC)."""
    s = schedule or {}
    tz = _tz(s.get("tz"))
    now = now_utc.astimezone(tz)
    freq, hour = s.get("freq", "daily"), int(s.get("hour", 8))
    if freq == "hourly":
        slot = now.replace(minute=0, second=0, microsecond=0)
    elif freq == "weekly":
        wd = int(s.get("weekday", 0))
        slot = now.replace(hour=hour, minute=0, second=0, microsecond=0) - dt.timedelta(days=(now.weekday() - wd) % 7)
        if slot > now:
            slot -= dt.timedelta(days=7)
    else:
        slot = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            slot -= dt.timedelta(days=1)
    return slot.astimezone(dt.timezone.utc)


def is_due(schedule, last_check_iso, now_utc):
    if not last_check_iso:
        return True
    try:
        last = dt.datetime.fromisoformat(str(last_check_iso).replace("Z", "+00:00"))
        if last.tzinfo is None:
            last = last.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return True
    return last < last_slot(schedule, now_utc)


def schedule_text(s):
    s = s or {}
    tz = s.get("tz") or "UTC"
    if s.get("freq") == "hourly":
        return "Every hour"
    if s.get("freq") == "weekly":
        return f"Weekly, {WEEKDAYS[int(s.get('weekday', 0))]} {int(s.get('hour', 8)):02d}:00 ({tz})"
    return f"Daily {int(s.get('hour', 8)):02d}:00 ({tz})"


# ------------------------------------------------------------------------------------------------ email
def email(spec, res, test=False, app_url=""):
    """Subject + HTML body: what happened in one line, the numbers in a small table, a button to the dashboard.
    Table layout and inline styles only, so it renders the same in Outlook and Gmail."""
    e = html.escape
    k = res.get("kind") or spec.get("kind")
    fired = bool(res.get("fired"))
    head = res.get("headline") or describe(spec)
    big = fmt(res.get("value"), k) if spec.get("rule") != "freshness" else f"{res.get('compare')} days"
    subj = ("[TEST] " if test else "") + ("Alert: " if fired else "Alert check: ") + head
    accent, soft, label = ("#b4321f", "#fdf1ef", "ALERT") if fired else ("#1a7341", "#eef8f1", "NO ALERT")
    rows = "".join(
        f'<tr><td style="padding:8px 12px;border-top:1px solid #e6eaf0;color:#5b6675;font-size:13px">{e(str(a))}</td>'
        f'<td style="padding:8px 12px;border-top:1px solid #e6eaf0;font-size:13px;font-weight:600;text-align:right">'
        f'{e(str(b))}</td></tr>' for a, b in (res.get("facts") or []))
    btn = (f'<a href="{e(app_url)}" style="display:inline-block;background:#1f6fd1;color:#ffffff;text-decoration:none;'
           f'font-weight:600;font-size:14px;padding:10px 18px;border-radius:6px">Open {e(spec.get("dashboard_name") or "the dashboard")}</a>'
           if app_url else "")
    test_note = ('<tr><td style="padding:8px 24px;background:#fff6dd;color:#7a5300;font-size:12px">Test email sent from '
                 'the alert form. Scheduled alerts look the same.</td></tr>') if test else ""
    body = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;'
        'font-family:Segoe UI,Arial,sans-serif;color:#1b2430"><tr><td align="center" style="padding:20px 10px">'
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;'
        'border:1px solid #dde3ea;border-radius:10px;overflow:hidden">'
        '<tr><td style="background:#0d2a4a;color:#ffffff;padding:14px 24px;font-size:13px;font-weight:600">'
        'Analytics Accelerator &middot; Data alert</td></tr>' + test_note +
        f'<tr><td style="padding:22px 24px 6px"><span style="display:inline-block;background:{soft};color:{accent};'
        f'font-size:11px;font-weight:700;letter-spacing:.06em;padding:3px 8px;border-radius:4px">{label}</span>'
        f'<div style="font-size:20px;font-weight:700;line-height:1.3;margin-top:10px">{e(head)}</div>'
        f'<div style="font-size:13px;color:#5b6675;margin-top:4px">{e(res.get("period_label") or "")}</div></td></tr>'
        f'<tr><td style="padding:10px 24px 4px"><div style="font-size:34px;font-weight:800;color:{accent}">{e(big)}</div>'
        f'<div style="font-size:13px;color:#5b6675">{e(spec.get("metric_label") or "")}</div></td></tr>'
        '<tr><td style="padding:14px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border:1px solid #e6eaf0;border-radius:8px;border-collapse:separate">{rows}</table></td></tr>'
        + (f'<tr><td style="padding:4px 24px 18px">{btn}</td></tr>' if btn else "") +
        '<tr><td style="padding:14px 24px;background:#f7f9fc;border-top:1px solid #e6eaf0;color:#6b7684;font-size:12px;'
        f'line-height:1.5">Checked {e(schedule_text(spec.get("schedule")))} on the governed semantic view '
        f'{e(spec.get("sv") or "")}. You get one email per breach. Pause or change this alert in the app under '
        '<b>My alerts</b>.</td></tr></table></td></tr></table>')
    return subj[:200], body


def integration_name(session, schema):
    try:
        rows = session.sql(f"SELECT SETTING_VALUE FROM {schema}.AA_APP_SETTINGS WHERE SETTING_KEY = ? "
                           "ORDER BY SET_AT DESC LIMIT 1", params=["alert_email_integration"]).collect()
        if rows:
            v = _row(rows[0]).get("setting_value")
            if v:
                return str(v)
    except Exception:
        pass
    return DEFAULT_INTEGRATION


def send_email(session, schema, recipients, subject, body):
    integ = integration_name(session, schema)
    session.sql("CALL SYSTEM$SEND_EMAIL(?, ?, ?, ?, 'text/html')",
                params=[integ, ",".join(recipients), subject, body]).collect()
    return integ


# ------------------------------------------------------------------------------------------------ the run
def _row(r):
    d = r.as_dict() if hasattr(r, "as_dict") else dict(r)
    return {str(k).lower(): v for k, v in d.items()}


def check_one(session, alert, now_utc=None):
    spec = alert["spec"] if isinstance(alert["spec"], dict) else json.loads(alert["spec"] or "{}")
    rows = [_row(r) for r in session.sql(alert["check_sql"]).collect()]
    return spec, evaluate(spec, rows, now_utc)


def run_alerts(session, schema, only_id=None, force=False, trigger="schedule", now_utc=None, send=True, app_url=""):
    """Check the alerts that are due (or one alert, or all with force) and email the ones that fire.
    Each alert emails once per period: the same breach is not emailed again on the next check."""
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    where, params = "WHERE DELETED = FALSE", []
    if only_id:
        where += " AND ALERT_ID = ?"
        params.append(only_id)
    alerts = [_row(r) for r in session.sql(
        f"SELECT ALERT_ID, TO_VARCHAR(SPEC) AS SPEC, CHECK_SQL, ACTIVE, LAST_CHECK_AT, LAST_FIRED_KEY "
        f"FROM {schema}.AA_ALERTS {where}", params=params).collect()]
    summary = []
    for a in alerts:
        if not only_id and not a.get("active"):
            continue
        try:
            spec = json.loads(a.get("spec") or "{}")
        except ValueError:
            spec = {}
        if not (force or only_id) and not is_due(spec.get("schedule"), a.get("last_check_at"), now_utc):
            continue
        emailed, err = False, ""
        try:
            spec, res = check_one(session, {"spec": spec, "check_sql": a["check_sql"]}, now_utc)
        except Exception as exc:
            res = {"status": "error", "detail": str(exc)[:400], "fired": False, "key": "", "value": None,
                   "compare": None, "period_label": ""}
        if res.get("fired"):
            if res.get("key") == a.get("last_fired_key"):
                err = "Already emailed for this period."
            elif send and spec.get("recipients"):
                try:
                    subj, body = email(spec, res, app_url=app_url)
                    send_email(session, schema, spec["recipients"], subj, body)
                    emailed = True
                except Exception as exc:
                    err = "Email not sent: " + str(exc)[:300]
            elif not spec.get("recipients"):
                err = "No recipients."
        stamp = now_utc.isoformat(timespec="seconds")
        session.sql(
            f"INSERT INTO {schema}.AA_ALERT_RUNS (RUN_ID, ALERT_ID, CHECKED_AT, TRIGGER_KIND, STATUS, PERIOD_LABEL, "
            "VALUE, COMPARE_VALUE, FIRED, EMAILED, MESSAGE) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?",
            params=[uuid.uuid4().hex[:12], a["alert_id"], stamp, trigger, res.get("status"),
                    res.get("period_label") or "", res.get("value"), _num(res.get("compare")),
                    bool(res.get("fired")), emailed, ((res.get("detail") or "") + (" · " + err if err else ""))[:900]]
        ).collect()
        fired_key = res.get("key") if emailed else a.get("last_fired_key")
        session.sql(
            f"UPDATE {schema}.AA_ALERTS SET LAST_CHECK_AT = ?, LAST_STATUS = ?, LAST_VALUE = ?, LAST_MESSAGE = ?, "
            "LAST_FIRED_KEY = ?, LAST_FIRED_AT = IFF(?, ?, LAST_FIRED_AT) WHERE ALERT_ID = ?",
            params=[stamp, res.get("status"), res.get("value"), (res.get("detail") or "")[:900], fired_key or "",
                    emailed, stamp, a["alert_id"]]).collect()
        summary.append({"alert_id": a["alert_id"], "status": res.get("status"), "fired": bool(res.get("fired")),
                        "emailed": emailed, "note": err, "detail": res.get("detail")})
    return summary


def main(session, alert_id=None, force=False, trigger="schedule"):
    """Stored-procedure entry point (AA_RUN_ALERTS)."""
    schema = SCHEMA  # noqa: F821  (set by alerts.proc_ddl in the procedure body)
    return run_alerts(session, schema, alert_id or None, bool(force), trigger or "schedule", app_url=APP_URL)  # noqa: F821
