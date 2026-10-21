"""Business sign-off (UAT) inside the app: tile review, the fix-and-re-check loop with the builder, page sign-off,
and the cross-dashboard lists (Change requests for builders, Waiting for my sign-off for reviewers).

Automatic validation proves the numbers match the base tables. Business sign-off records that a named person agreed
each tile answers its business question, and signed each page off. Every action is a row in AA_UAT_SIGNOFFS
(append-only, the newest row per tile or page wins):

  reviewer: accepted ("Looks right") | rejected ("Needs change", a change request)
  builder:  fixed ("Fixed – please re-check") | replied (an answer without a fix)

An acceptance is tied to a fingerprint of the numbers the reviewer saw, so it re-opens by itself when the tile's
numbers, fields or layout change. A change request stays open until the builder marks it fixed or replies, and
closes only when the reviewer looks again.

Nothing is blocked: a page can be signed off with open mismatches or tiles not reviewed, but then a reason is
required and it is recorded as "Signed off with notes", never plain "Signed off".
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Optional

REVIEWER_DECISIONS = ("accepted", "rejected")
BUILDER_DECISIONS = ("fixed", "replied")
TILE_DECISIONS = REVIEWER_DECISIONS + BUILDER_DECISIONS
PAGE_DECISIONS = ("approved", "approved_notes", "rejected")

TILE_LABEL = {"accepted": "Looks right", "rejected": "Needs change", "fixed": "Fixed – please re-check",
              "replied": "Builder replied", "pending": "To review", "changed": "Changed – please re-check"}
PAGE_LABEL = {"approved": "Signed off", "approved_notes": "Signed off with notes", "rejected": "Sent back for changes",
              "changed": "Changed – sign off again", "ready": "Ready to sign off", "in_review": "In progress",
              "not_started": "Not started"}
LABEL = {**TILE_LABEL, **PAGE_LABEL}         # overall status uses page words
REASONS = ["Known timing difference", "Plan / target restated", "Rounding", "Data team owns the fix"]


def page_sig(page: dict, tile_sigs: dict[str, Optional[str]]) -> str:
    """What a page sign-off covers: its tiles and fields (not requirements or titles' wording) and their numbers."""
    comps = [{k: c.get(k) for k in ("component_id", "type", "metric_id", "metric2_id", "metrics", "dimension",
                                     "dimension2", "dimensions")} for c in page.get("components") or []]
    body = json.dumps({"c": comps, "s": sorted((k, v or "") for k, v in tile_sigs.items())}, sort_keys=True)
    return hashlib.sha1(body.encode()).hexdigest()[:16]


def latest(entries: list[dict]) -> dict[tuple, dict]:
    """Newest entry per (kind, page, tile). Entries arrive newest first."""
    out: dict[tuple, dict] = {}
    for e in entries:
        key = (e.get("kind"), e.get("page_id"), e.get("tile_key") or "")
        out.setdefault(key, e)
    return out


def _brief(e: Optional[dict]) -> Optional[dict]:
    if not e:
        return None
    return {"decision": e.get("decision"), "comment": e.get("comment") or "", "by": e.get("created_by") or "",
            "at": str(e.get("created_at") or "")}


def tile_story(history: list[dict], sig: Optional[str]) -> dict:
    """State of one tile from its entries (newest first): the state, the open change request and its thread."""
    if not history or history[0].get("decision") not in TILE_DECISIONS:
        return {"state": "pending", "last": None, "request": None, "thread": []}
    e = history[0]
    d = e["decision"]
    if d == "accepted":
        state = "accepted" if (e.get("tile_sig") or "") == (sig or "") else "changed"
    else:
        state = d                                  # a request stays open until the reviewer looks again
    request, thread = None, []
    if d in ("rejected", "fixed", "replied"):
        for i, x in enumerate(history):
            if x.get("decision") == "rejected":
                request = _brief(x)
                thread = [_brief(y) for y in reversed(history[:i + 1])]
                break
    return {"state": state, "last": _brief(e), "request": request, "thread": thread}


def status(spec: dict, tiles: dict[str, dict], entries: list[dict], data_tile: Any) -> dict:
    """Business sign-off picture for the Validation tab and the tile notes.
    tiles = validation results per cid (status, sig, checks); data_tile(page, comp) -> True for tiles that hold data."""
    by_tile: dict[str, list[dict]] = {}
    for e in entries:
        if e.get("kind") == "tile":
            by_tile.setdefault(e.get("tile_key") or "", []).append(e)
    last = latest(entries)
    pages, n_pages, n_signed, any_rejected = [], 0, 0, False
    for pg in spec.get("pages") or []:
        rows, sigs = [], {}
        for c in pg.get("components") or []:
            if not data_tile(pg, c):
                continue
            cid = f"{pg['page_id']}/{c['component_id']}"
            t = tiles.get(cid) or {}
            sigs[cid] = t.get("sig")
            story = tile_story(by_tile.get(cid) or [], t.get("sig"))
            lst = story["last"] or {}
            rows.append({"cid": cid, "title": c.get("title") or c["type"], "question": c.get("question") or "",
                         "requirement": ((spec.get("requirements") or {}).get(cid) or ""),
                         "validation": t.get("status_eff") or t.get("status") or "none",
                         "check": _check_brief(t), "state": story["state"],
                         "by": lst.get("by"), "at": lst.get("at"), "comment": lst.get("comment") or "",
                         "request": story["request"], "thread": story["thread"]})
        psig = page_sig(pg, sigs)
        pe = last.get(("page", pg["page_id"], ""))
        accepted = sum(1 for r in rows if r["state"] == "accepted")
        reviewed = sum(1 for r in rows if r["state"] in ("accepted", "rejected", "fixed", "replied"))
        open_findings = sum(1 for r in rows if r["validation"] in ("mismatch", "review"))
        if pe and pe.get("decision") in PAGE_DECISIONS:
            pstate = pe["decision"] if pe.get("page_sig") == psig else "changed"
        elif rows and accepted == len(rows):
            pstate = "ready"
        elif any(r["state"] != "pending" for r in rows):
            pstate = "in_review"
        else:
            pstate = "not_started"
        n_pages += 1
        if pstate in ("approved", "approved_notes"):
            n_signed += 1
        any_rejected = any_rejected or pstate == "rejected"
        pages.append({"page_id": pg["page_id"], "label": pg["label"], "state": pstate, "sig": psig,
                      "tiles": rows, "accepted": accepted, "reviewed": reviewed, "total": len(rows),
                      "open_findings": open_findings,
                      "rejected_tiles": sum(1 for r in rows if r["state"] == "rejected"),
                      "recheck": sum(1 for r in rows if r["state"] in ("fixed", "replied", "changed")),
                      "to_review": sum(1 for r in rows if r["state"] == "pending"),
                      "signed_by": (pe or {}).get("created_by"), "signed_at": (pe or {}).get("created_at"),
                      "comment": (pe or {}).get("comment") or ""})
    if not n_pages:
        overall = "not_started"
    elif any_rejected:
        overall = "rejected"
    elif n_signed == n_pages:
        overall = "approved_notes" if any(p["state"] == "approved_notes" for p in pages) else "approved"
    elif n_signed or any(p["state"] != "not_started" for p in pages):
        overall = "in_review"
    else:
        overall = "not_started"
    return {"status": overall, "label": PAGE_LABEL[overall], "pages_signed": n_signed, "pages_total": n_pages,
            "pages": pages, "next": next_step(pages), "reasons": REASONS,
            "open_requests": sum(p["rejected_tiles"] for p in pages)}


def _check_brief(t: dict) -> dict:
    """What the automatic check found, in one line the reviewer can read: the biggest gap on the tile."""
    st = t.get("status_eff") or t.get("status") or "none"
    out = {"status": st, "text": "", "detail": ""}
    if st == "none":
        out["text"] = "Not checked yet"
        return out
    if st == "pass":
        out["text"] = "Matches source"
        return out
    if st == "accepted":
        out["text"] = "Difference accepted"
    elif st == "review":
        out["text"] = "Check needed"
    elif st == "na":
        out["text"] = "Can't be checked"
    worst = None
    for c in t.get("checks") or []:
        for r in c.get("rows") or []:
            if r.get("ok") is False:
                try:
                    a, b = float(r.get("dashboard")), float(r.get("independent"))
                    gap = abs(a - b) / abs(b) if b else (0.0 if a == b else 1.0)
                except (TypeError, ValueError):
                    a = b = None
                    gap = 1.0
                if worst is None or gap > worst[0]:
                    worst = (gap, r, a, b)
        if c.get("status") in ("mismatch", "review") and not out["detail"]:
            out["detail"] = c.get("summary") or ""
    if worst:
        gap, r, a, b = worst
        if st == "mismatch":
            out["text"] = f"Differs by {_pct(gap)}"
        label = " · ".join(str(x) for x in (r.get("label"), r.get("column")) if x)
        if a is not None:
            out["detail"] = f"{label + ': ' if label else ''}Dashboard {_num(a)} · Source {_num(b)}"
    elif st == "mismatch":
        out["text"] = "Differs from source"
    return out


def _pct(x: float) -> str:
    p = x * 100
    return f"{p:.2f}%" if p < 0.1 else f"{p:.1f}%" if p < 10 else f"{p:.0f}%"


def _num(v: float) -> str:
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"


def next_step(pages: list[dict]) -> dict:
    """The one thing to do next, in plain words, and which of the 4 steps the reviewer is on."""
    if not pages:
        return {"step": 1, "text": "Add tiles to the dashboard first."}
    unchecked = sum(1 for p in pages for r in p["tiles"] if r["validation"] == "none")
    if unchecked:
        return {"step": 1, "text": f"Check the numbers first: {unchecked} tile(s) are not checked yet. "
                                   "Click Validate all pages above."}
    to_review = sum(p["to_review"] for p in pages)
    recheck = sum(p["recheck"] for p in pages)
    waiting = sum(p["rejected_tiles"] for p in pages)
    parts = []
    if recheck:
        parts.append(f"re-check {recheck} tile(s) the builder fixed or changed")
    if to_review:
        parts.append(f"review {to_review} tile(s)")
    unsigned = [p["label"] for p in pages if p["state"] not in ("approved", "approved_notes", "rejected")]
    if parts:
        txt = " and ".join(parts).capitalize()
        if unsigned:
            txt += f", then sign off {_names(unsigned)}"
        txt += "."
        if waiting:
            txt += f" {waiting} change request(s) are with the builder."
        return {"step": 2, "text": txt + " Tiles where the numbers differ need a short reason to approve."}
    if unsigned:
        txt = f"Sign off {_names(unsigned)}."
        if waiting:
            txt += f" {waiting} change request(s) are still with the builder: you can wait, or sign off with notes."
        return {"step": 3, "text": txt}
    if any(p["state"] == "rejected" for p in pages):
        return {"step": 3, "text": "A page was sent back for changes. Once the builder has fixed it, sign it off again."}
    return {"step": 4, "text": "All pages are signed off. The dashboard is ready to publish."}


def _names(labels: list[str]) -> str:
    q = [f"the {x} page" for x in labels[:3]]
    more = f" and {len(labels) - 3} more" if len(labels) > 3 else ""
    return (", ".join(q[:-1]) + " and " + q[-1] if len(q) > 1 else q[0]) + more


def check_tile(decision: str, comment: str, validation_status: str) -> str:
    if decision not in REVIEWER_DECISIONS:
        raise ValueError("Choose Looks right or Needs change.")
    if decision == "rejected" and not comment:
        raise ValueError("Say what needs to change.")
    if decision == "accepted" and validation_status == "mismatch" and not comment:
        raise ValueError("The numbers on this tile differ from the source: give the reason it is OK to approve.")
    return decision


def check_builder(decision: str, comment: str, state: str) -> str:
    """The builder answers a change request: fixed (note optional) or a reply (text required)."""
    if decision not in BUILDER_DECISIONS:
        raise ValueError("Choose Mark as fixed or Reply.")
    if state not in ("rejected", "fixed", "replied"):
        raise ValueError("There is no open change request on this tile.")
    if decision == "replied" and not comment:
        raise ValueError("Write the reply for the reviewer.")
    return decision


def check_page(decision: str, comment: str, page: dict) -> str:
    """A page can always be signed off; with open findings or tiles not accepted it needs a reason and is recorded
    as Signed off with notes."""
    if decision not in PAGE_DECISIONS:
        raise ValueError("Choose Sign off or Send back.")
    gaps = page["open_findings"] or page["accepted"] < page["total"]
    if decision == "rejected" and not comment:
        raise ValueError("Say why the page is sent back.")
    if decision != "rejected" and gaps:
        if not comment:
            raise ValueError("This page has open items: give the reason you sign it off anyway.")
        return "approved_notes"
    if decision == "approved_notes" and not comment:
        raise ValueError("Add the notes for Signed off with notes.")
    return decision


# ------------------------------------------------------------------------------ cross-dashboard lists
def _days(at: str, today: dt.date) -> Optional[int]:
    try:
        return (today - dt.date.fromisoformat(str(at)[:10])).days
    except ValueError:
        return None


def inbox(entries: list[dict], owners: dict[str, dict], me: str, today: Optional[dt.date] = None) -> dict:
    """Every tile with a change request in flight, across all saved dashboards.
    entries = tile rows from AA_UAT_SIGNOFFS (newest first, any dashboard);
    owners = dashboard_id -> {"name", "owner"}; me = the signed-in person ('' = unknown, treated as everyone).
    Returns rows plus the badge counts: open requests on my dashboards, fixes waiting for my re-check."""
    today = today or dt.date.today()
    me_u = (me or "").upper()
    hist: dict[tuple, list[dict]] = {}
    for e in entries:
        if e.get("kind") != "tile" or not e.get("dashboard_id") or e["dashboard_id"] not in owners:
            continue
        hist.setdefault((e["dashboard_id"], e.get("tile_key") or ""), []).append(e)
    rows, closed = [], 0
    for (did, cid), h in hist.items():
        story = tile_story(h, h[0].get("tile_sig"))       # the stored fingerprint: no re-check here
        d = owners[did]
        if story["state"] == "accepted":
            if any(x.get("decision") == "rejected" for x in h) and (_days(h[0].get("created_at"), today) or 99) <= 30:
                closed += 1
            continue
        if story["state"] not in ("rejected", "fixed", "replied") or not story["request"]:
            continue
        req = story["request"]
        owner = (d.get("owner") or "")
        rows.append({"dashboard_id": did, "dashboard_name": d.get("name") or did, "owner": owner,
                     "page_id": cid.split("/")[0], "page_label": h[0].get("page_label") or "",
                     "cid": cid, "tile_title": h[0].get("tile_title") or cid.split("/")[-1],
                     "state": story["state"], "label": TILE_LABEL[story["state"]],
                     "request": req, "last": story["last"], "thread": story["thread"],
                     "age_days": _days(req["at"], today),
                     "mine_owner": not me_u or owner.upper() == me_u,
                     "mine_reviewer": not me_u or (req["by"] or "").upper() == me_u})
    rows.sort(key=lambda r: (r["dashboard_name"].lower(), -(r["age_days"] or 0)))
    return {"rows": rows, "closed_30d": closed,
            "badge_requests": sum(1 for r in rows if r["state"] == "rejected" and r["mine_owner"]),
            "badge_recheck": sum(1 for r in rows if r["state"] in ("fixed", "replied") and r["mine_reviewer"])}
