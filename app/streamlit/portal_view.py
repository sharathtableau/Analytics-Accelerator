"""Dashboard portal: the viewer-only front door of the Analytics Accelerator.

Builders author and publish dashboards in the builder app. Everyone else (for example the ELT team) opens
this portal: a catalog of the dashboards published for them, grouped by audience. Opening a card shows the
finished, read-only dashboard. Nothing in this module can build, edit or publish anything.
"""
from __future__ import annotations

import html

import streamlit as st

AUDIENCE_ORDER = ("executives", "managers", "daily_operations", "weekly_business_review")
AUDIENCE_LABEL = {
    "executives": "Executives",
    "managers": "Managers",
    "daily_operations": "Daily operations",
    "weekly_business_review": "Weekly business review",
}
AUDIENCE_BLURB = {
    "executives": "One-page brief: results vs plan, trajectory and what needs a decision.",
    "managers": "Scorecard by region, exceptions and drill-down.",
    "daily_operations": "Live status, today's pace and the worklist.",
    "weekly_business_review": "The weekly review pack.",
}

CSS = """
<style>
header[data-testid='stHeader']{display:none}
.block-container{max-width:1180px!important;padding:40px 32px 64px!important}
.stApp{background:#f5f8fc}
.pt, .pt *{font-family:Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.pt-top{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:6px}
.pt-title{margin:0;font-size:30px;line-height:1.15;font-weight:700;color:#0b2440;letter-spacing:0}
.pt-sub{margin:6px 0 0;font-size:15px;color:#5b6b82}
.pt-who{font-size:13px;color:#5b6b82;white-space:nowrap}
.pt-group{margin:34px 0 4px;font-size:13px;font-weight:600;color:#11567f;text-transform:uppercase;letter-spacing:.06em}
.pt-blurb{margin:0 0 14px;font-size:14px;color:#5b6b82}
.pt-thumb{display:block;width:100%;height:auto;border-radius:8px;background:#f5f8fc;border:1px solid #e3e9f2;margin:0 0 14px}
.pt-aud{margin:0 0 4px;font-size:12px;font-weight:600;color:#11567f;text-transform:uppercase;letter-spacing:.06em}
.pt-name{margin:0 0 6px;font-size:17px;line-height:1.3;font-weight:600;color:#0b2440;min-height:2.6em}
.pt-meta{margin:0 0 12px;font-size:13px;color:#5b6b82}
.pt-note{margin:0 0 14px;font-size:13px;color:#33465e}
.pt-empty{margin-top:48px;padding:40px 24px;text-align:center;background:#fff;border:1px solid #e3e9f2;border-radius:10px;color:#5b6b82;font-size:15px}
.pt-flash{margin:14px 0 0;padding:10px 14px;background:#fff6e5;border:1px solid #f1d9a8;border-radius:8px;color:#6b4b00;font-size:14px}
div[data-testid='stVerticalBlockBorderWrapper']{padding:6px;background:#fff;border:1px solid #e3e9f2!important;border-radius:10px!important;box-shadow:0 1px 2px rgba(16,29,46,.04)}
div[data-testid='stVerticalBlockBorderWrapper']:hover{border-color:#29b5e8!important;box-shadow:0 8px 24px -16px rgba(17,86,127,.45)}
div[data-testid='stVerticalBlockBorderWrapper'] button{border-radius:6px;font-weight:600;border:1px solid #11567f;color:#11567f;background:#fff}
div[data-testid='stVerticalBlockBorderWrapper'] button:hover{background:#11567f;color:#fff;border-color:#11567f}
.stTextInput input{border-radius:6px}
button[data-testid='stBaseButton-primary'],button[kind='primary']{background:#11567f!important;border:1px solid #11567f!important;color:#fff!important;border-radius:6px!important;font-weight:600}
button[data-testid='stBaseButton-primary']:hover,button[kind='primary']:hover{background:#0b2440!important;border-color:#0b2440!important}
</style>
"""


_BR, _DP, _LN, _OK, _BAD = "#29b5e8", "#11567f", "#cfd9e6", "#0f9d6e", "#d64545"


def _thumb(aud: str) -> str:
    """A small schematic of the dashboard layout for each audience (decorative, not data)."""
    b = []
    if aud == "executives":                       # KPI cards + trajectory line
        for i in range(3):
            x = 12 + i * 94
            b.append(f"<rect x='{x}' y='12' width='86' height='34' rx='5' fill='#fff' stroke='{_LN}'/>"
                     f"<rect x='{x + 8}' y='20' width='34' height='5' rx='2' fill='{_LN}'/>"
                     f"<rect x='{x + 8}' y='30' width='52' height='8' rx='2' fill='{_DP}'/>")
        b.append(f"<rect x='12' y='56' width='276' height='54' rx='5' fill='#fff' stroke='{_LN}'/>"
                 f"<polyline points='22,98 62,88 102,90 142,76 182,70 222,62 276,66' fill='none' stroke='{_BR}' stroke-width='3'/>"
                 f"<polyline points='22,100 62,94 102,92 142,86 182,82 222,78 276,76' fill='none' stroke='{_LN}' stroke-width='2' stroke-dasharray='4 3'/>")
    elif aud == "managers":                       # scorecard rows with RAG
        b.append(f"<rect x='12' y='12' width='276' height='98' rx='5' fill='#fff' stroke='{_LN}'/>")
        for i, col in enumerate((_OK, _BAD, _OK, "#e0a100")):
            y = 22 + i * 22
            b.append(f"<circle cx='28' cy='{y + 6}' r='5' fill='{col}'/><rect x='42' y='{y + 2}' width='64' height='8' rx='2' fill='{_LN}'/>"
                     f"<rect x='130' y='{y}' width='{50 + (i * 37) % 60}' height='12' rx='3' fill='{_BR}'/>"
                     f"<rect x='250' y='{y + 2}' width='28' height='8' rx='2' fill='{_DP}'/>")
    elif aud == "daily_operations":               # status tiles + pace bars
        for i in range(4):
            x = 12 + i * 70
            col = (_OK, _OK, _BAD, _OK)[i]
            b.append(f"<rect x='{x}' y='12' width='64' height='30' rx='5' fill='#fff' stroke='{_LN}'/>"
                     f"<circle cx='{x + 14}' cy='27' r='5' fill='{col}'/><rect x='{x + 26}' y='24' width='28' height='7' rx='2' fill='{_DP}'/>")
        b.append(f"<rect x='12' y='52' width='276' height='58' rx='5' fill='#fff' stroke='{_LN}'/>")
        for i in range(12):
            h = 14 + (i * 17) % 32
            b.append(f"<rect x='{24 + i * 21}' y='{104 - h}' width='13' height='{h}' rx='2' fill='{_BR if i < 8 else _LN}'/>")
    else:                                         # generic: bars
        b.append(f"<rect x='12' y='12' width='276' height='98' rx='5' fill='#fff' stroke='{_LN}'/>")
        for i in range(10):
            h = 18 + (i * 23) % 56
            b.append(f"<rect x='{26 + i * 26}' y='{100 - h}' width='16' height='{h}' rx='2' fill='{_BR}'/>")
    return "<svg class='pt-thumb' viewBox='0 0 300 122' xmlns='http://www.w3.org/2000/svg'>" + "".join(b) + "</svg>"


LOADER_CSS = """
<style>
.pt-load{position:fixed;inset:0;z-index:999999;display:grid;place-items:center;background:rgba(245,248,252,.94);
  -webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);animation:pt-fade .2s ease both}
.pt-load-card{width:min(520px,calc(100vw - 48px));padding:30px 32px;background:#fff;border:1px solid #e3e9f2;border-radius:12px;
  box-shadow:0 24px 60px -30px rgba(9,25,45,.45);font-family:Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.pt-load-k{margin:0 0 6px;font-size:12px;font-weight:600;color:#11567f;text-transform:uppercase;letter-spacing:.06em}
.pt-load-n{margin:0 0 18px;font-size:20px;line-height:1.3;font-weight:700;color:#0b2440}
.pt-load-bar{position:relative;height:6px;border-radius:6px;background:#e3e9f2;overflow:hidden}
.pt-load-bar:after{content:"";position:absolute;top:0;left:-40%;width:40%;height:100%;border-radius:6px;
  background:linear-gradient(90deg,#29b5e8,#11567f);animation:pt-slide 1.15s ease-in-out infinite}
.pt-load-s{margin:14px 0 0;font-size:13.5px;color:#5b6b82}
.pt-load-s span{display:inline-block;animation:pt-step 6s steps(1) infinite}
@keyframes pt-slide{0%{left:-40%}100%{left:100%}}
@keyframes pt-fade{from{opacity:0}to{opacity:1}}
</style>
"""


def loader_html(name: str) -> str:
    """Full-screen 'opening' state shown the moment a dashboard is clicked, until it is drawn."""
    return (LOADER_CSS + "<div class='pt-load'><div class='pt-load-card'><p class='pt-load-k'>Opening dashboard</p>"
            f"<p class='pt-load-n'>{html.escape(name or 'Dashboard')}</p><div class='pt-load-bar'></div>"
            "<p class='pt-load-s'>Running live queries on the governed semantic view…</p></div></div>")


def _label(aud: str) -> str:
    return AUDIENCE_LABEL.get(aud) or (aud or "Other").replace("_", " ").capitalize()


def render(published: list[dict], viewer: str, flash: str = "", base_url: str = "", portal_url: str = "",
           sharing=None) -> None:
    """sharing: optional dict with can_share(d) -> bool, roles() -> list[str], on_save(did) callback."""
    """Draw the catalog. Clicking Open sets ?view=<dashboard_id>; the caller reacts on the next run."""
    st.markdown(CSS, unsafe_allow_html=True)
    who = f"Signed in as {html.escape(viewer)}" if viewer else ""
    st.markdown(
        "<div class='pt'><div class='pt-top'><div><div class='pt-title'>Analytics Accelerator Portal</div>"
        "<p class='pt-sub'>Published dashboards for your team. Open one to see the live, governed numbers.</p></div>"
        f"<div class='pt-who'>{who}</div></div></div>", unsafe_allow_html=True)
    if flash:
        st.markdown(f"<div class='pt'><div class='pt-flash'>{html.escape(flash)}</div></div>", unsafe_allow_html=True)

    if not published:
        st.markdown("<div class='pt'><div class='pt-empty'>No dashboards have been published for you yet.</div></div>",
                    unsafe_allow_html=True)
        return

    q = st.text_input("Search dashboards", key="pt_search", placeholder="Search dashboards",
                      label_visibility="collapsed").strip().lower()
    items = [d for d in published if not q or q in (d.get("name") or "").lower()
             or q in _label(d.get("audience")).lower()]
    if not items:
        st.markdown("<div class='pt'><div class='pt-empty'>No dashboard matches that search.</div></div>",
                    unsafe_allow_html=True)
        return

    groups: dict[str, list[dict]] = {}
    for d in items:
        groups.setdefault(d.get("audience") or "other", []).append(d)
    order = [a for a in AUDIENCE_ORDER if a in groups] + sorted(a for a in groups if a not in AUDIENCE_ORDER)

    for aud in order:
        st.markdown(f"<div class='pt'><div class='pt-group'>{html.escape(_label(aud))}</div>"
                    f"<p class='pt-blurb'>{html.escape(AUDIENCE_BLURB.get(aud, ''))}</p></div>", unsafe_allow_html=True)
        rows = groups[aud]
        for i in range(0, len(rows), 3):
            cols = st.columns(3, gap="medium")
            for col, d in zip(cols, rows[i:i + 3]):
                with col:
                    with st.container(border=True):
                        by = (d.get("published_by") or "").strip()
                        meta = f"Version {d.get('version')} · {d.get('published_at') or ''}" + (f" · by {by}" if by else "")
                        st.markdown(
                            f"<div class='pt'>{_thumb(aud)}"
                            f"<p class='pt-name'>{html.escape(d.get('name') or 'Untitled dashboard')}</p>"
                            f"<p class='pt-meta'>{html.escape(meta)}</p></div>", unsafe_allow_html=True)
                        did = d["dashboard_id"]
                        b1, b2 = st.columns([3, 2], gap="small")
                        with b1:
                            st.button("Open dashboard", key=f"pt_open_{did}", use_container_width=True,
                                      on_click=_open, args=(did,))
                        with b2:
                            with st.popover("Share", use_container_width=True):
                                _share_panel(d, base_url, portal_url, sharing)


def _share_panel(d: dict, base_url: str, portal_url: str, sharing=None) -> None:
    """Who can see this dashboard (editable by the person who published it), and links to hand to them."""
    did = d["dashboard_id"]
    st.markdown(f"<div class='pt'><p class='pt-name' style='min-height:0'>{html.escape(d.get('name') or '')}</p></div>",
                unsafe_allow_html=True)
    roles = [str(r).upper() for r in (d.get("shared_roles") or [])]
    users = [str(u) for u in (d.get("shared_users") or [])]
    if sharing and sharing["can_share"](d):
        st.caption("Share with")
        options = sorted(set(sharing["roles"]()) | set(roles))
        st.multiselect("Roles", options, default=roles, key=f"pt_roles_{did}", placeholder="Choose roles",
                       help="Each role chosen here gets the Analytics Accelerator Portal.")
        st.text_input("Only these users (optional)", value=", ".join(users), key=f"pt_users_{did}",
                      placeholder="e.g. JDOE, ASMITH",
                      help="Snowflake user names, comma-separated. When set, only these people see this dashboard.")
        st.button("Save sharing", key=f"pt_save_{did}", type="primary", use_container_width=True,
                  on_click=sharing["on_save"], args=(did,))
    else:
        who = []
        if roles:
            who.append("Roles: " + ", ".join(roles))
        if users:
            who.append("Only these users: " + ", ".join(users))
        st.caption("Shared with")
        st.markdown("<div class='pt'><p class='pt-meta'>" + html.escape("  ·  ".join(who) or
                    "Everyone who can open the Analytics Accelerator Portal") + "</p></div>", unsafe_allow_html=True)
        st.caption(f"Sharing is changed by the person who published it ({d.get('published_by') or 'the builder'}).")
    if base_url:
        st.caption("Link straight to this dashboard")
        st.code(f"{base_url}?view={did}", language=None)
    if portal_url:
        st.caption("Analytics Accelerator Portal in Snowsight (the dashboard is in its catalog)")
        st.code(portal_url, language=None)

def _open(did: str) -> None:
    st.query_params["view"] = did
