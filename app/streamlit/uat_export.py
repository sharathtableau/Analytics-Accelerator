"""UAT workbook export: the dashboard's validation evidence in Sharath's corporate UAT format.

Tabs
  Test Cases         corporate template (header block, black header bar, one row per tile check, Pass/Fail fill)
  Expected Results   corporate template, one block per tile: Dashboard (semantic view) vs Base tables (independent
                     SQL), reconciliation summary + verdict, and a row-by-row variance block with live formulas
  Requirement Trace  business question -> page -> tile -> fields -> checks -> status
  Sign-off           one row per page: reviewer, decision, date, comment (filled in the app or by hand)
  SQL Appendix       both SQL statements per tile
Everything comes from the stored validation report; nothing is recomputed here.
"""
from __future__ import annotations

import datetime as dt
import io
from typing import Any, Optional

from xlsx_lite import Alignment, Color, Font, PatternFill, Workbook      # no openpyxl needed inside Snowflake

CHECK_NAMES = {"QA-01": "Source recompute", "QA-02": "Display arithmetic", "QA-03": "Reconciles to total",
               "QA-04": "Join integrity", "QA-05": "Period logic", "QA-06": "Data health", "QA-07": "Filters applied",
               "QA-08": "Narrative grounded"}
EXPECTED = {
    "QA-01": "Every value on the tile equals the value re-derived with independent SQL on the base tables "
             "(relative tolerance 1e-6).",
    "QA-02": "Every % change, share, total and step shown is recomputed from the queried values and matches.",
    "QA-03": "For an additive metric, the segments shown add up to the headline total.",
    "QA-04": "Lookup keys are unique (no double counting) and fact rows find their lookup row.",
    "QA-05": "Current, prior and year-ago periods are complete and correctly bounded; coverage matches the base tables.",
    "QA-06": "Data is fresh, the series has no gaps, no material blank categories, no impossible negatives.",
    "QA-07": "Every active filter reaches the tile and the independent query.",
    "QA-08": "Every figure in the AI summary matches a computed fact.",
}
RESULT = {"pass": "Pass", "mismatch": "Fail", "review": "Review", "na": "Not checked", "accepted": "Accepted"}
FILL = {"Pass": "FF92D050", "Fail": "FFFF0000", "Review": "FFFFC000", "Not checked": "FFD9D9D9",
        "Accepted": "FFBDD7EE", "Approved": "FF92D050", "Approved with notes": "FFC6E0B4", "Rejected": "FFFF0000",
        "Changed since sign-off": "FFFFC000"}
CONSIDERATIONS = ("Testing considerations:\n"
                  "• Security—are the appropriate roles/authorizations being tested?\n"
                  "• Reporting—are there any test cases/scenarios to verify reporting?\n"
                  "• Compliance—are there any forms/customer-facing documents that need to be printed/verified?\n"
                  "• Data—who is needed to generate test data for this change?")


def _f(size=12, bold=True, color="FF000000", name="Arial"):
    return Font(name=name, size=size, bold=bold, color=color)


def _fill(hex_color):
    return PatternFill(fill_type="solid", fgColor=hex_color)


def _wrap(h=None, v="top"):
    return Alignment(horizontal=h, vertical=v, wrap_text=True)


def _num(v) -> Optional[float]:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------------------------------------ Test Cases
def _test_cases(wb, meta, rows):
    ws = wb.create_sheet("Test Cases")
    for col, w in {"A": 6.5, "B": 23.0, "C": 48.88, "D": 30.11, "E": 31.44, "F": 45.0, "G": 31.44, "H": 21.33,
                   "I": 28.0}.items():
        ws.column_dimensions[col].width = w
    for r, h in {1: 15.6, 2: 28.5, 4: 15.6, 5: 15.6, 6: 15.75, 7: 14.25, 9: 14.4, 10: 15.6, 11: 75.0, 15: 75.0,
                 16: 33.75}.items():
        ws.row_dimensions[r].height = h
    ws["B1"] = f"###{meta['reference']} "
    ws["B1"].font = _f()
    ws.merge_cells("B2:I2")
    ws["B2"] = meta["title"]
    ws["B2"].font = _f()
    ws["B2"].alignment = Alignment(horizontal="left")
    ws.merge_cells("B4:I4")
    ws["B4"] = f"Testers: {meta['testers']}"
    ws["B4"].font = _f()
    ws["B4"].alignment = _wrap()
    ws["B5"], ws["C5"] = "Test Environment:", meta["environment"]
    ws["E5"], ws["F5"] = "Validation Environment", meta["semantic_view"]
    for ref in ("B5", "C5", "E5", "F5"):
        ws[ref].font = _f()
    ws["E5"].alignment = Alignment(horizontal="right")
    for r, label, val in ((6, "Testing Started:", meta["started"]), (7, "Testing Completed:", meta["completed"])):
        ws[f"B{r}"], ws[f"C{r}"] = label, val
        for ref in (f"B{r}", f"C{r}"):
            ws[ref].font = _f()
            ws[ref].alignment = _wrap("left")
        ws[f"C{r}"].number_format = "mm/dd/yyyy"
    for r, text in ((9, f"Description: {meta['description']}"), (10, f"Recipients: {meta['recipients']}"),
                    (11, CONSIDERATIONS), (15, meta["rules"])):
        ws.merge_cells(f"B{r}:I{r}")
        ws[f"B{r}"] = text
        ws[f"B{r}"].font = _f()
        ws[f"B{r}"].alignment = _wrap("left")
    heads = ["Scenario/Steps", "Test", "Super User/Team Responsible", "Data Set (Page, tile, period, filters)",
             "Expected Result", "Actual Result", "Pass/Fail", "Comments"]
    cols = list("BCDEFGHI")
    for c, h in zip(cols, heads):
        ws[f"{c}16"] = h
        ws[f"{c}16"].font = _f(name="Times New Roman", color="FFFFFFFF")
        ws[f"{c}16"].fill = _fill("FF000000")
        ws[f"{c}16"].alignment = _wrap()
    for i, row in enumerate(rows):
        r = 17 + i
        ws.row_dimensions[r].height = 79.5
        test = (row[1] or "").split(". ")[0][:160]
        vals = [i + 1, f"{row[0]}\n{test}".strip()] + row[2:]
        for c, v in zip(cols, vals):
            cell = ws[f"{c}{r}"]
            cell.value = v
            cell.font = _f(11, False, name="Calibri")
            cell.alignment = _wrap()
            cell.fill = _fill(FILL.get(v, "FFFFFFFF") if c == "H" else "FFFFFFFF")
    ws.freeze_panes = "B17"


# ------------------------------------------------------------------------------------------------ Expected Results
def _expected_results(wb, meta, blocks):
    ws = wb.create_sheet("Expected Results")
    for col, w in {"A": 34.0, "B": 18.0, "C": 18.0, "D": 15.0, "E": 22.0, "F": 15.0, "H": 5.0, "K": 34.0, "L": 18.0,
                   "M": 18.0, "N": 15.0, "O": 22.0, "P": 15.0}.items():
        ws.column_dimensions[col].width = w
    ws.row_dimensions[1].height, ws.row_dimensions[2].height = 19.95, 31.95
    ws["A1"] = f"As of {meta['completed']:%m-%d-%Y}"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws.merge_cells("A2:Q2")
    ws["A2"] = "DASHBOARD vs BASE TABLES (Independent Recompute)"
    ws["A2"].font = Font(name="Calibri", size=16, bold=True)
    ws["A2"].fill = PatternFill(fill_type="solid", fgColor=Color(theme=3, tint=0.749992370372631, type="theme"))
    ws["A2"].alignment = Alignment(horizontal="center")
    dark = PatternFill(fill_type="solid", fgColor=Color(theme=0, tint=-0.249977111117893, type="theme"))
    r = 4
    for b in blocks:
        ws.merge_cells(f"A{r}:Q{r}")
        ws[f"A{r}"] = f"{b['page']} › {b['tile']}  ({b['period']})"
        ws[f"A{r}"].font = _f(11, True, "FFFFFFFF")
        ws[f"A{r}"].fill = _fill("FF44546A")
        r += 1
        ws.row_dimensions[r].height = 28.05
        ws.merge_cells(f"A{r}:G{r}")
        ws[f"A{r}"] = f"Dashboard Output ({meta['semantic_view']})"
        ws.merge_cells(f"K{r}:Q{r}")
        ws[f"K{r}"] = "Base Table Output (" + ", ".join(meta["base_tables"])[:120] + ")"
        for ref in (f"A{r}", f"K{r}"):
            ws[ref].font = Font(name="Calibri", size=13, bold=True)
            ws[ref].fill = dark
            ws[ref].alignment = Alignment(horizontal="center", wrap_text=True)
        r += 1
        for c, h in zip("ABC", ("ROW", "MEASURE", "VALUE")):
            ws[f"{c}{r}"] = h
        for c, h in zip("KLM", ("ROW", "MEASURE", "VALUE")):
            ws[f"{c}{r}"] = h
        for c in "ABCKLM":
            ws[f"{c}{r}"].font = _f(10)
            ws[f"{c}{r}"].alignment = Alignment(horizontal="center")
        first = r + 1
        for row in b["rows"]:
            r += 1
            ws[f"A{r}"], ws[f"B{r}"], ws[f"C{r}"] = row["label"], row["column"], _num(row["dashboard"])
            ws[f"K{r}"], ws[f"L{r}"], ws[f"M{r}"] = row["label"], row["column"], _num(row["independent"])
            for c in "ABCKLM":
                ws[f"{c}{r}"].font = Font(name="Calibri", size=11)
            for c in "CM":
                ws[f"{c}{r}"].number_format = "#,##0.00####"
        last = r
        n = last - first + 1
        bad = sum(1 for x in b["rows"] if not x.get("ok"))
        r += 2
        ws.merge_cells(f"A{r}:G{r}")
        ws[f"A{r}"] = "RECONCILIATION SUMMARY"
        ws.merge_cells(f"K{r}:Q{r}")
        ws[f"K{r}"] = "FINAL UAT VERDICT"
        for ref in (f"A{r}", f"K{r}"):
            ws[ref].font = _f(11, True, "FF1F497D")
            ws[ref].fill = _fill("FFD9E1F2")
        r += 1
        ws.merge_cells(f"A{r}:E{r}")
        ws.merge_cells(f"F{r}:G{r}")
        ws.merge_cells(f"K{r}:O{r}")
        ws.merge_cells(f"P{r}:Q{r}")
        for ref, v in ((f"A{r}", "METRIC"), (f"F{r}", "VALUE"), (f"K{r}", "CHECK"), (f"P{r}", "RESULT")):
            ws[ref] = v
            ws[ref].font = _f(10)
        metrics = [("VALUES COMPARED", n), ("VALUES MATCHED", n - bad), ("VALUES WITH DIFFERENCES", bad),
                   ("MAX ABSOLUTE DIFFERENCE", f"=SUMPRODUCT(MAX(ABS(M{first}:M{last}-C{first}:C{last})))" if n else 0)]
        checks = [(f"{c['id']} {CHECK_NAMES.get(c['id'], c.get('name', ''))}", c["status"], c.get("summary", ""))
                  for c in b["checks"]]
        for j in range(max(len(metrics), len(checks))):
            r += 1
            if j < len(metrics):
                ws.merge_cells(f"A{r}:E{r}")
                ws.merge_cells(f"F{r}:G{r}")
                ws[f"A{r}"], ws[f"F{r}"] = metrics[j]
                ws[f"A{r}"].font = ws[f"F{r}"].font = _f(10, False)
                ws[f"F{r}"].number_format = "#,##0.00########"
            if j < len(checks):
                label, st, _ = checks[j]
                ws.merge_cells(f"K{r}:O{r}")
                ws.merge_cells(f"P{r}:Q{r}")
                ws[f"K{r}"] = label
                ws[f"K{r}"].font = _f(10, False)
                res = RESULT.get(st, st).upper()
                ws[f"P{r}"] = res
                ws[f"P{r}"].font = _f(10, True, {"PASS": "FF008000", "FAIL": "FFFF0000"}.get(res, "FFC07000"))
        r += 2
        ws.merge_cells(f"A{r}:G{r}")
        ws[f"A{r}"] = "DETAILED RECONCILIATION & VARIANCE (Row-by-Row)"
        ws[f"A{r}"].font = _f(11, True, "FFFFFFFF")
        ws[f"A{r}"].fill = _fill("FF44546A")
        r += 1
        for c, h in zip("ABCDE", ("ROW", "MEASURE", "DIFF (BASE - DASHBOARD)", "DIFF %", "STATUS")):
            ws[f"{c}{r}"] = h
            ws[f"{c}{r}"].font = _f(10)
        for k in range(n):
            r += 1
            src = first + k
            ws[f"A{r}"], ws[f"B{r}"] = f"=A{src}", f"=B{src}"
            ws[f"C{r}"] = f"=M{src}-C{src}"
            ws[f"C{r}"].number_format = "#,##0.00########"
            ws[f"D{r}"] = f"=IF(C{src}=0,0,C{r}/ABS(C{src}))"
            ws[f"D{r}"].number_format = "0.0000%"
            ws[f"E{r}"] = f'=IF(ABS(D{r})<=0.000001,"MATCH","MISMATCH")'
            for c in "ABCD":
                ws[f"{c}{r}"].font = _f(10, False)
            ok = b["rows"][k].get("ok")
            ws[f"E{r}"].font = _f(10, True, "FF008000" if ok else "FFFF0000")
        r += 3


# ------------------------------------------------------------------------------------------------ extra tabs
def _table(ws, headers, rows, widths):
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    for i, h in enumerate(headers):
        c = ws.cell(row=1, column=i + 1, value=h)
        c.font = _f(11, True, "FFFFFFFF", "Times New Roman")
        c.fill = _fill("FF000000")
        c.alignment = _wrap()
    for r, row in enumerate(rows, start=2):
        for i, v in enumerate(row):
            c = ws.cell(row=r, column=i + 1, value=v)
            c.font = _f(10, False, name="Calibri")
            c.alignment = _wrap()
            if v in FILL:
                c.fill = _fill(FILL[v])
    ws.freeze_panes = "A2"


# ------------------------------------------------------------------------------------------------ main
UAT_RESULT = {"accepted": "Pass", "rejected": "Fail", "pending": "Not checked", "changed": "Review",
              "fixed": "Review", "replied": "Review"}
TILE_WORDS = {"accepted": "Looks right", "rejected": "Needs change", "changed": "Changed – please re-check",
              "pending": "To review", "fixed": "Fixed – please re-check", "replied": "Builder replied"}
HISTORY_WORDS = {"accepted": "Reviewer: looks right", "rejected": "Reviewer: needs change",
                 "fixed": "Builder: marked as fixed", "replied": "Builder: replied", "approved": "Page signed off",
                 "approved_notes": "Page signed off with notes", "rejected_page": "Page sent back for changes"}


def build(spec: dict, report: dict, meta: dict[str, Any], signoffs: Optional[list[dict]] = None,
          uat_status: Optional[dict] = None) -> bytes:
    """spec = dashboard layout, report = stored validation report (tiles, dashboard, lineage),
    meta = title, reference, testers, environment, semantic_view, base_tables, period, filters, description,
    recipients, started, completed (dates), goal."""
    tiles = report.get("tiles") or {}
    pages = {p["page_id"]: p for p in spec.get("pages") or []}
    rules = ("Business Rules & Requirements:\n"
             "* 100% Match = PASS: every value on every tile equals the independent recompute on the base tables\n"
             "* Displayed % changes, shares and totals must recompute exactly; additive segments must add to the total\n"
             "* Review = data-health note to confirm; Not checked = the check cannot run for this tile (reason given)\n"
             "* Accepted = a difference accepted by a named person, with reason and expiry")
    meta = {**meta, "rules": meta.get("rules") or rules}
    tc_rows, blocks, trace, sql_rows = [], [], [], []
    acc = {r["cid"]: r for pg in (uat_status or {}).get("pages") or [] for r in pg["tiles"]}
    period = meta.get("period", "")
    flt = meta.get("filters") or "No filters"
    for page in spec.get("pages") or []:
        for comp in page.get("components") or []:
            cid = f"{page['page_id']}/{comp['component_id']}"
            t = tiles.get(cid)
            if not t:
                continue
            fields = ", ".join(x for x in [comp.get("metric_id"), comp.get("metric2_id"), comp.get("dimension"),
                                           comp.get("dimension2"), *(comp.get("metrics") or [])] if x)
            for c in t.get("checks") or []:
                res = RESULT.get(c.get("status"), c.get("status"))
                tc_rows.append([f"{page['label']} › {comp['title']} — {c['id']} {CHECK_NAMES.get(c['id'], '')}",
                                c.get("method") or EXPECTED.get(c["id"], ""),
                                "Analytics Accelerator (automatic) · reviewer: " + (meta.get("reviewer") or "—"),
                                f"{page['label']} · {comp['title']} · {period} · {flt}",
                                EXPECTED.get(c["id"], ""), c.get("summary", ""), res,
                                "\n".join(x for x in [c.get("detail") or "", (c.get("diagnosis") or {}).get("text", "")
                                                      if isinstance(c.get("diagnosis"), dict) else ""] if x)[:900]])
                if c["id"] == "QA-01" and c.get("rows"):
                    blocks.append({"page": page["label"], "tile": comp["title"], "period": period,
                                   "rows": c["rows"][:200], "checks": t["checks"]})
                    sql_rows.append([page["label"], comp["title"], (c.get("sql") or {}).get("dashboard", ""),
                                     (c.get("sql") or {}).get("independent", "")])
            worst = RESULT.get(t.get("status"), t.get("status"))
            a = acc.get(cid) or {}
            if uat_status is not None:
                tc_rows.append([f"{page['label']} › {comp['title']} — UAT business acceptance",
                                "Reviewer confirms the tile answers its business question.",
                                a.get("by") or "Business reviewer",
                                f"{page['label']} · {comp['title']} · {period} · {flt}",
                                f"Tile answers: {comp.get('question') or comp['title']}"
                                + (f" (requirement {a['requirement']})" if a.get("requirement") else ""),
                                {"accepted": "Looks right (reviewer)", "rejected": "Needs change (reviewer)",
                                 "changed": "Approved earlier; tile changed since", "pending": "Not reviewed yet",
                                 "fixed": "Builder fixed it; waiting for re-check",
                                 "replied": "Builder replied; waiting for reviewer"}
                                .get(a.get("state"), ""),
                                UAT_RESULT.get(a.get("state"), "Not checked"),
                                (a.get("comment") or "") + (f" ({a.get('at')})" if a.get("at") else "")])
            trace.append([meta.get("goal") or "", page.get("purpose") or page["label"], page["label"], comp["title"],
                          comp.get("question") or "", a.get("requirement") or (spec.get("requirements") or {}).get(cid, ""),
                          comp["type"].replace("_", " "), fields,
                          ", ".join(c["id"] for c in t.get("checks") or []), worst,
                          TILE_WORDS.get(a.get("state"), "—")
                          + (f" · {a['by']}" if a.get("by") else "")])
    for c in report.get("dashboard") or []:
        tc_rows.append([f"Dashboard — {c['id']} {CHECK_NAMES.get(c['id'], '')}", c.get("method") or "",
                        "Analytics Accelerator (automatic)", f"{meta['semantic_view']} · {period}",
                        EXPECTED.get(c["id"], ""), c.get("summary", ""), RESULT.get(c.get("status"), c.get("status")),
                        ""])
    wb = Workbook()
    wb.remove(wb.active)
    _test_cases(wb, meta, tc_rows)
    _expected_results(wb, meta, blocks)
    _table(wb.create_sheet("Requirement Trace"),
           ["Business goal", "Page question", "Page", "Tile", "Tile question", "Requirement", "Chart",
            "Fields (semantic view)", "Checks run", "Validation", "UAT acceptance"], trace,
           [28, 28, 14, 28, 32, 18, 14, 38, 20, 12, 24])
    if signoffs is None and uat_status is not None:
        signoffs = [{"page": p["label"], "tiles": p["total"], "verified": f"{p['accepted']} accepted",
                     "open": p["open_findings"], "reviewer": p.get("signed_by") or "",
                     "decision": {"approved": "Signed off", "approved_notes": "Signed off with notes",
                                  "rejected": "Sent back for changes",
                                  "changed": "Changed since sign-off"}.get(p["state"], "Not signed"),
                     "date": (p.get("signed_at") or "")[:10], "comment": p.get("comment") or ""}
                    for p in uat_status["pages"]]
    so = signoffs or [{"page": p["label"]} for p in pages.values()]
    _table(wb.create_sheet("Sign-off"),
           ["Page", "Tiles", "Verified", "Open findings", "Reviewer", "Decision", "Date", "Comment"],
           [[s["page"], s.get("tiles", ""), s.get("verified", ""), s.get("open", ""), s.get("reviewer", ""),
             s.get("decision", ""), s.get("date", ""), s.get("comment", "")] for s in so],
           [22, 8, 10, 14, 24, 16, 14, 50])
    if meta.get("history"):
        names = {f"{p['page_id']}/{c['component_id']}": (p["label"], c.get("title") or "")
                 for p in spec.get("pages") or [] for c in p.get("components") or []}
        plabel = {p["page_id"]: p["label"] for p in spec.get("pages") or []}
        hist = []
        for e in reversed(meta["history"]):              # oldest first
            pg, tl = names.get(e.get("tile_key") or "", (plabel.get(e.get("page_id"), e.get("page_label") or ""),
                                                        e.get("tile_title") or ""))
            d = e.get("decision") or ""
            key = "rejected_page" if e.get("kind") == "page" and d == "rejected" else d
            hist.append([str(e.get("created_at") or ""), pg, tl if e.get("kind") == "tile" else "(whole page)",
                         HISTORY_WORDS.get(key, d), e.get("created_by") or "", e.get("comment") or ""])
        _table(wb.create_sheet("Review History"), ["When", "Page", "Tile", "Action", "Who", "Comment / reason"],
               hist, [17, 18, 30, 26, 20, 60])
    _table(wb.create_sheet("SQL Appendix"), ["Page", "Tile", "Dashboard SQL (semantic view)",
                                             "Independent SQL (base tables)"], sql_rows, [16, 30, 80, 80])
    for ws in wb.worksheets:                      # prints landscape, one page wide
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
