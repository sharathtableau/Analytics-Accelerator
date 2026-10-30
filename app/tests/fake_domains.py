"""Local tests only: the Finance (Keystone) and CPG (Apex) semantic views over the real pack CSVs.

Mirrors setup/<domain>/02_views.sql + build_<domain>_sv.py closely enough for the app's own queries:
weekly rows dated by week ending, end-of-week stocks taken at the latest week of each group (NON ADDITIVE BY week),
weighted rates, and one logical table per fact so a metric can only be split by dimensions of its own table
(SHOW SEMANTIC DIMENSIONS ... FOR METRIC). Turned on with AA_FAKE_DOMAINS=1. Not used in Snowflake.
"""
from __future__ import annotations

import csv
import datetime as dt
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
SETUP = Path(os.environ.get("AA_FAKE_SETUP") or HERE.parents[1] / "setup")
SHIFT_WEEKS = 4                         # pack week 2026-09-14 -> week ending 2026-10-18 (as live on 21 Oct 2026)

FIN = "WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV"
CPG = "WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV"


def _csv(domain: str, name: str) -> list[dict[str, str]]:
    with open(SETUP / domain / "data" / f"{name}.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _week(start: str) -> dict[str, Any]:
    ws = dt.date.fromisoformat(start)
    we = ws + dt.timedelta(days=6 + 7 * SHIFT_WEEKS)
    return {"WEEK_ENDING": we, "WEEK_START": we - dt.timedelta(days=6), "MONTH_START": we.replace(day=1),
            "MONTH_NAME": we.strftime("%b %Y"), "CALENDAR_QUARTER": f"{we.year}-Q{(we.month - 1) // 3 + 1}",
            "CALENDAR_YEAR": we.year}


WEEK_DIMS = {"WEEK_ENDING": "DATE", "MONTH_START": "DATE", "MONTH_NAME": "VARCHAR", "CALENDAR_QUARTER": "VARCHAR",
             "CALENDAR_YEAR": "NUMBER"}


# ------------------------------------------------------------------------------------------------- metric helpers
def S(col):
    return lambda rs: sum(_f(r[col]) for r in rs)


def STOCK(col):
    """End-of-week stock: the sum at the latest week of the group."""
    def fn(rs):
        if not rs:
            return None
        last = max(r["WEEK_ENDING"] for r in rs)
        return sum(_f(r[col]) for r in rs if r["WEEK_ENDING"] == last)
    return fn


def D(a: Callable, b: Callable, k: float = 1.0):
    def fn(rs):
        den = b(rs)
        return 0.0 if not den else a(rs) * k / den
    return fn


def WEEKS(rs):
    return len({r["WEEK_ENDING"] for r in rs})


class Domain:
    """tables: {table: rows}; dims: {(table, name): type} (a dimension lives on every table that carries the column);
    metrics: {name: (table, expression text, fn)}"""
    def __init__(self, fqn, tables, dims, metrics, comment):
        self.fqn, self.tables, self.dims, self.metrics, self.comment = fqn, tables, dims, metrics, comment

    def describe(self) -> list[dict[str, Any]]:
        out = [{"object_kind": "SEMANTIC_VIEW", "object_name": self.fqn.split(".")[-1], "parent_entity": None,
                "property": "COMMENT", "property_value": self.comment}]
        for t in self.tables:
            out.append({"object_kind": "TABLE", "object_name": t.upper(), "parent_entity": None,
                        "property": "BASE_TABLE_NAME", "property_value": t.upper()})
        for (ent, name), typ in self.dims.items():
            out.append({"object_kind": "DIMENSION", "object_name": name, "parent_entity": ent.upper(),
                        "property": "DATA_TYPE", "property_value": typ})
            out.append({"object_kind": "DIMENSION", "object_name": name, "parent_entity": ent.upper(),
                        "property": "EXPRESSION", "property_value": "C_" + name})
        for name, (table, expr, _) in self.metrics.items():
            out.append({"object_kind": "METRIC", "object_name": name, "parent_entity": table.upper(),
                        "property": "EXPRESSION", "property_value": expr})
            out.append({"object_kind": "METRIC", "object_name": name, "parent_entity": table.upper(),
                        "property": "DATA_TYPE", "property_value": "NUMBER(38,6)"})
        return out

    def dims_for(self, metric: str) -> list[dict[str, str]]:
        table = self.metrics[metric.upper()][0]
        cols = set(self.tables[table][0]) if self.tables[table] else set()
        return [{"table_name": ent.upper(), "name": name} for (ent, name) in self.dims if name in cols]

    def query(self, dims: list[tuple[str, str, Any]], mets: list[tuple[str, str]], keep: Callable) -> list[dict]:
        """dims: [(alias, column, trunc_grain|None)], mets: [(alias, metric)]; one group-by per metric table, merged."""
        from fake_snowflake import trunc
        by_table: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for alias, m in mets:
            if m.upper() not in self.metrics:
                raise RuntimeError(f"invalid metric {m}")
            by_table[self.metrics[m.upper()][0]].append((alias, m.upper()))
        merged: dict[tuple, dict[str, Any]] = {}
        if not by_table:
            cols = [c for _, c, _ in dims]
            home = next((t for t, rows in self.tables.items() if rows and all(c in rows[0] for c in cols)), None)
            if not home:
                raise RuntimeError("Dimensions from unrelated tables")
            by_table = {home: []}
        for table, ms in by_table.items():
            rows = self.tables[table]
            if rows:
                missing = [c for _, c, _ in dims if c not in rows[0]]
                if missing:
                    raise RuntimeError(f"Dimension {missing[0]} is not related to the metric's table {table}")
            groups: dict[tuple, list] = defaultdict(list)
            for r in rows:
                if keep(r):
                    groups[tuple(trunc(r[c], g) if g else r[c] for _, c, g in dims)].append(r)
            for key, rs in groups.items():
                row = merged.setdefault(key, {alias: key[i] for i, (alias, _, _) in enumerate(dims)})
                for alias, m in ms:
                    row[alias] = self.metrics[m][2](rs)
        out = list(merged.values())
        for r in out:
            for alias, _ in mets:
                r.setdefault(alias, None)
        return out


# ------------------------------------------------------------------------------------------------------- finance
def _finance() -> Domain:
    prod = {r["product_id"]: r for r in _csv("finance", "finance_dim_product")}
    seg = {r["segment_id"]: r for r in _csv("finance", "finance_dim_segment")}

    def attrs(r, with_seg=True):
        p = prod[r["product_id"]]
        out = {**_week(r["week_start_date"]), "PRODUCT_NAME": p["product_name"], "PRODUCT_TYPE": p["product_type"],
               "TIER": p["tier"]}
        if with_seg:
            s = seg[r["segment_id"]]
            fico = _f(s["avg_fico"])
            out.update({"SEGMENT_NAME": s["segment_name"], "CREDIT_TIER": "Prime (740+)" if fico >= 740 else
                        "Near-prime (660-739)" if fico >= 660 else "Subprime (<660)"})
        return out

    pf = []
    pidx = {}
    for r in _csv("finance", "finance_fact_portfolio_week"):
        card = prod[r["product_id"]]["product_type"] == "Credit Card"
        row = {**attrs(r), "ENDING_BALANCE": _f(r["ending_balance"]),
               "CARD_BALANCE": _f(r["ending_balance"]) if card else 0.0,
               "REVOLVING_BALANCE": _f(r["ending_balance"]) * _f(r["revolve_rate_pct"]) / 100,
               **{k.upper(): _f(r[k]) for k in ("new_accounts", "closed_accounts", "active_accounts", "purchase_volume",
                                                 "interchange_revenue", "rewards_expense", "net_interest_income")},
               "COST_OF_FUNDS": _f(r["cost_of_funds_dollars"])}
        pf.append(row)
        pidx[(r["week_start_date"], r["product_id"], r["segment_id"])] = r
    cr = []
    for r in _csv("finance", "finance_fact_credit_week"):
        p = pidx[(r["week_start_date"], r["product_id"], r["segment_id"])]
        bal = _f(p["ending_balance"])
        cr.append({**attrs(r), "DPD_30_BALANCE": _f(r["dpd_30_balance"]), "DPD_60_BALANCE": _f(r["dpd_60_balance"]),
                   "DPD_90_BALANCE": _f(r["dpd_90_balance"]), "GROSS_CHARGEOFFS": _f(r["gross_chargeoff_dollars"]),
                   "RECOVERIES": _f(r["recovery_dollars"]), "NET_CHARGEOFFS": _f(r["net_chargeoff_dollars"]),
                   "CARD_BALANCE": bal, "FICO_X_BALANCE": _f(r["avg_fico"]) * bal,
                   "CARD_REVENUE": _f(p["net_interest_income"]) + _f(p["interchange_revenue"]) - _f(p["rewards_expense"])})
    dpst = []
    for r in _csv("finance", "finance_fact_deposits_week"):
        b = _f(r["deposit_balance"])
        dpst.append({**attrs(r), "DEPOSIT_BALANCE": b, "RUNOFF": _f(r["runoff_dollars"]),
                     "MATURING": _f(r["maturing_dollars"]), "NEW_MONEY": _f(r["new_money_dollars"]),
                     "RATE_PAID_X": _f(r["rate_paid_pct"]) / 100 * b, "COMP_X": _f(r["competitor_rate_pct"]) / 100 * b,
                     "GAP_X": _f(r["rate_gap_pct"]) / 100 * b})
    acq = []
    for r in _csv("finance", "finance_fact_acquisition_week"):
        acq.append({**attrs(r, with_seg=False), "CHANNEL": r["channel"],
                    **{k.upper(): _f(r[k]) for k in ("marketing_spend", "applications", "approvals", "bookings")},
                    "LINE_X": _f(r["avg_initial_credit_line"]) * _f(r["bookings"])})
    tables = {"portfolio": pf, "credit": cr, "deposits": dpst, "acquisition": acq}
    dims = {**{("weeks", k): v for k, v in WEEK_DIMS.items()},
            ("products", "PRODUCT_NAME"): "VARCHAR", ("products", "PRODUCT_TYPE"): "VARCHAR",
            ("products", "TIER"): "VARCHAR", ("segments", "SEGMENT_NAME"): "VARCHAR",
            ("segments", "CREDIT_TIER"): "VARCHAR", ("acquisition", "CHANNEL"): "VARCHAR"}
    bw = S("ENDING_BALANCE")
    cbw = lambda rs: sum(r["CARD_BALANCE"] for r in rs)
    dbw = S("DEPOSIT_BALANCE")
    M = {
        "ENDING_BALANCE": ("portfolio", "SUM(portfolio.f_ending_balance)", STOCK("ENDING_BALANCE")),
        "ACTIVE_ACCOUNTS": ("portfolio", "SUM(portfolio.f_active_accounts)", STOCK("ACTIVE_ACCOUNTS")),
        "AVERAGE_BALANCE": ("portfolio", "DIV0(portfolio.helper_balance_weeks, portfolio.helper_weeks)", D(bw, WEEKS)),
        "NEW_ACCOUNTS": ("portfolio", "SUM(portfolio.f_new_accounts)", S("NEW_ACCOUNTS")),
        "CLOSED_ACCOUNTS": ("portfolio", "SUM(portfolio.f_closed_accounts)", S("CLOSED_ACCOUNTS")),
        "ATTRITION_RATE": ("portfolio", "DIV0(portfolio.closed_accounts * 52, portfolio.helper_active_weeks)",
                           D(S("CLOSED_ACCOUNTS"), S("ACTIVE_ACCOUNTS"), 52)),
        "PURCHASE_VOLUME": ("portfolio", "SUM(portfolio.f_purchase_volume)", S("PURCHASE_VOLUME")),
        "INTERCHANGE_REVENUE": ("portfolio", "SUM(portfolio.f_interchange_revenue)", S("INTERCHANGE_REVENUE")),
        "REWARDS_EXPENSE": ("portfolio", "SUM(portfolio.f_rewards_expense)", S("REWARDS_EXPENSE")),
        "REWARDS_TO_INTERCHANGE_RATIO": ("portfolio", "DIV0(portfolio.rewards_expense, portfolio.interchange_revenue)",
                                         D(S("REWARDS_EXPENSE"), S("INTERCHANGE_REVENUE"))),
        "NET_INTEREST_INCOME": ("portfolio", "SUM(portfolio.f_net_interest_income)", S("NET_INTEREST_INCOME")),
        "COST_OF_FUNDS": ("portfolio", "SUM(portfolio.f_cost_of_funds)", S("COST_OF_FUNDS")),
        "NET_INTEREST_MARGIN_PCT": ("portfolio", "DIV0((portfolio.net_interest_income - portfolio.cost_of_funds) * 52, "
                                                 "portfolio.helper_balance_weeks)",
                                    D(lambda rs: S("NET_INTEREST_INCOME")(rs) - S("COST_OF_FUNDS")(rs), bw, 52)),
        "REVOLVE_RATE": ("portfolio", "DIV0(portfolio.helper_revolving_weeks, portfolio.helper_balance_weeks)",
                         D(S("REVOLVING_BALANCE"), bw)),
        "DPD_30_BALANCE": ("credit", "SUM(credit.f_dpd_30_balance)", STOCK("DPD_30_BALANCE")),
        "DPD_60_BALANCE": ("credit", "SUM(credit.f_dpd_60_balance)", STOCK("DPD_60_BALANCE")),
        "DPD_90_BALANCE": ("credit", "SUM(credit.f_dpd_90_balance)", STOCK("DPD_90_BALANCE")),
        "DELINQUENCY_RATE": ("credit", "DIV0(credit.helper_dpd_30_weeks, credit.helper_credit_card_balance_weeks)",
                             D(S("DPD_30_BALANCE"), cbw)),
        "GROSS_CHARGEOFFS": ("credit", "SUM(credit.f_gross_chargeoffs)", S("GROSS_CHARGEOFFS")),
        "RECOVERIES": ("credit", "SUM(credit.f_recoveries)", S("RECOVERIES")),
        "NET_CHARGEOFFS": ("credit", "SUM(credit.f_net_chargeoffs)", S("NET_CHARGEOFFS")),
        "ANNUALIZED_LOSS_RATE": ("credit", "DIV0(credit.net_chargeoffs * 52, credit.helper_credit_card_balance_weeks)",
                                 D(S("NET_CHARGEOFFS"), cbw, 52)),
        "CARD_REVENUE": ("credit", "SUM(credit.f_card_revenue)", S("CARD_REVENUE")),
        "RISK_ADJUSTED_YIELD": ("credit", "DIV0((credit.card_revenue - credit.net_chargeoffs) * 52, "
                                          "credit.helper_credit_card_balance_weeks)",
                                D(lambda rs: S("CARD_REVENUE")(rs) - S("NET_CHARGEOFFS")(rs), cbw, 52)),
        "AVERAGE_FICO": ("credit", "DIV0(credit.helper_fico_x_balance, credit.helper_credit_card_balance_weeks)",
                         D(S("FICO_X_BALANCE"), cbw)),
        "DEPOSIT_BALANCE": ("deposits", "SUM(deposits.f_deposit_balance)", STOCK("DEPOSIT_BALANCE")),
        "RUNOFF": ("deposits", "SUM(deposits.f_runoff)", S("RUNOFF")),
        "NEW_MONEY": ("deposits", "SUM(deposits.f_new_money)", S("NEW_MONEY")),
        "NET_NEW_MONEY": ("deposits", "deposits.new_money - deposits.runoff",
                          lambda rs: S("NEW_MONEY")(rs) - S("RUNOFF")(rs)),
        "RUNOFF_RATE": ("deposits", "DIV0(deposits.runoff * 52, deposits.helper_deposit_balance_weeks)",
                        D(S("RUNOFF"), dbw, 52)),
        "RATE_PAID": ("deposits", "DIV0(deposits.helper_rate_paid_x_balance, deposits.helper_deposit_balance_weeks)",
                      D(S("RATE_PAID_X"), dbw)),
        "COMPETITOR_RATE": ("deposits", "DIV0(deposits.helper_competitor_x_balance, deposits.helper_deposit_balance_weeks)",
                            D(S("COMP_X"), dbw)),
        "RATE_GAP": ("deposits", "DIV0(deposits.helper_rate_gap_x_balance, deposits.helper_deposit_balance_weeks)",
                     D(S("GAP_X"), dbw)),
        "MARKETING_SPEND": ("acquisition", "SUM(acquisition.f_marketing_spend)", S("MARKETING_SPEND")),
        "APPLICATIONS": ("acquisition", "SUM(acquisition.f_applications)", S("APPLICATIONS")),
        "APPROVALS": ("acquisition", "SUM(acquisition.f_approvals)", S("APPROVALS")),
        "BOOKINGS": ("acquisition", "SUM(acquisition.f_bookings)", S("BOOKINGS")),
        "APPROVAL_RATE": ("acquisition", "DIV0(acquisition.approvals, acquisition.applications)",
                          D(S("APPROVALS"), S("APPLICATIONS"))),
        "COST_PER_BOOKING": ("acquisition", "DIV0(acquisition.marketing_spend, acquisition.bookings)",
                             D(S("MARKETING_SPEND"), S("BOOKINGS"))),
    }
    return Domain(FIN, tables, dims, M, "Keystone Financial (fictional bank), weekly")


# ----------------------------------------------------------------------------------------------------------- CPG
def _cpg() -> Domain:
    cust = {r["customer_id"]: r for r in _csv("cpg", "cpg_dim_customer")}
    prod = {r["product_id"]: r for r in _csv("cpg", "cpg_dim_product")}

    def attrs(r):
        c, p = cust[r["customer_id"]], prod[r["product_id"]]
        off = "off-price" in c["customer_name"].lower()
        return {**_week(r["week_start_date"]), "CUSTOMER_NAME": c["customer_name"], "CHANNEL": c["channel"],
                "REGION_SCOPE": c["region_scope"],
                "ACCOUNT_TYPE": "Direct to consumer" if c["channel"] == "DTC" else "Off-price" if off else "Wholesale partner",
                "PRODUCT_NAME": p["product_name"], "PRODUCT_CATEGORY": p["product_category"],
                "GENDER_SEGMENT": p["gender_segment"]}

    st = {(r["week_start_date"], r["customer_id"], r["product_id"]): r for r in _csv("cpg", "cpg_fact_sellthrough_week")}
    trade = []
    for r in _csv("cpg", "cpg_fact_sellin_week"):
        t = st[(r["week_start_date"], r["customer_id"], r["product_id"])]
        c = cust[r["customer_id"]]
        units, ns = _f(r["shipped_units"]), _f(r["net_sales"])
        trade.append({**attrs(r), "SHIPPED_UNITS": units, "GROSS_SALES": _f(r["gross_sales"]),
                      "TRADE_SPEND": _f(r["trade_spend"]), "NET_SALES": ns,
                      "GM_DOLLARS": ns * _f(r["gross_margin_pct"]) / 100, "RETURN_DOLLARS": _f(r["return_dollars"]),
                      "FILL_X": _f(r["fill_rate_pct"]) / 100 * units, "OTIF_X": _f(r["otif_pct"]) / 100 * units,
                      "DTC_NS": ns if c["channel"] == "DTC" else 0.0,
                      "OFF_NS": ns if "off-price" in c["customer_name"].lower() else 0.0,
                      "POS_UNITS": _f(t["pos_units"]), "POS_DOLLARS": _f(t["pos_dollars"]),
                      "ON_HAND": _f(t["retailer_on_hand_units"]),
                      "ACV_X": _f(t["acv_distribution_pct"]) / 100 * _f(t["pos_dollars"])})
    promo = []
    for r in _csv("cpg", "cpg_fact_trade_promo"):
        sp = _f(r["trade_spend"])
        promo.append({**attrs(r), "PROMO_ID": r["promo_id"], "PROMO_TYPE": r["promo_type"], "PROMO_SPEND": sp,
                      "INCREMENTAL_REVENUE": _f(r["incremental_revenue"]),
                      "ROI_X": _f(r["promo_roi_pct"]) / 100 * sp, "LIFT_X": _f(r["volume_lift_pct"]) / 100 * sp})
    tables = {"trade": trade, "promotions": promo}
    dims = {**{("weeks", k): v for k, v in WEEK_DIMS.items()},
            **{("accounts", k): "VARCHAR" for k in ("CUSTOMER_NAME", "CHANNEL", "ACCOUNT_TYPE", "REGION_SCOPE")},
            **{("products", k): "VARCHAR" for k in ("PRODUCT_NAME", "PRODUCT_CATEGORY", "GENDER_SEGMENT")},
            ("promotions", "PROMO_TYPE"): "VARCHAR", ("promotions", "PROMO_ID"): "VARCHAR"}
    ns, gs, su = S("NET_SALES"), S("GROSS_SALES"), S("SHIPPED_UNITS")
    M = {
        "GROSS_SALES": ("trade", "SUM(trade.f_gross_sales)", gs),
        "TRADE_SPEND": ("trade", "SUM(trade.f_trade_spend)", S("TRADE_SPEND")),
        "NET_SALES": ("trade", "SUM(trade.f_net_sales)", ns),
        "TRADE_SPEND_RATE": ("trade", "DIV0(trade.trade_spend, trade.gross_sales)", D(S("TRADE_SPEND"), gs)),
        "SHIPPED_UNITS": ("trade", "SUM(trade.f_shipped_units)", su),
        "GROSS_MARGIN_DOLLARS": ("trade", "SUM(trade.f_gross_margin_dollars)", S("GM_DOLLARS")),
        "GROSS_MARGIN_PCT": ("trade", "DIV0(trade.gross_margin_dollars, trade.net_sales)", D(S("GM_DOLLARS"), ns)),
        "AVERAGE_SELLING_PRICE": ("trade", "DIV0(trade.gross_sales, trade.shipped_units)", D(gs, su)),
        "RETURN_DOLLARS": ("trade", "SUM(trade.f_return_dollars)", S("RETURN_DOLLARS")),
        "RETURNS_RATE": ("trade", "DIV0(trade.return_dollars, trade.gross_sales)", D(S("RETURN_DOLLARS"), gs)),
        "FILL_RATE": ("trade", "DIV0(trade.helper_fill_x_units, trade.shipped_units)", D(S("FILL_X"), su)),
        "OTIF_RATE": ("trade", "DIV0(trade.helper_otif_x_units, trade.shipped_units)", D(S("OTIF_X"), su)),
        "DTC_MIX": ("trade", "DIV0(trade.dtc_net_sales, trade.net_sales)", D(S("DTC_NS"), ns)),
        "OFF_PRICE_MIX": ("trade", "DIV0(trade.off_price_net_sales, trade.net_sales)", D(S("OFF_NS"), ns)),
        "POS_UNITS": ("trade", "SUM(trade.f_pos_units)", S("POS_UNITS")),
        "POS_DOLLARS": ("trade", "SUM(trade.f_pos_dollars)", S("POS_DOLLARS")),
        "SELL_THROUGH_RATIO": ("trade", "DIV0(trade.pos_units, trade.shipped_units)", D(S("POS_UNITS"), su)),
        "RETAILER_ON_HAND_UNITS": ("trade", "SUM(trade.f_on_hand_units)", STOCK("ON_HAND")),
        "WEEKS_OF_SUPPLY": ("trade", "DIV0(trade.helper_on_hand_weeks, trade.pos_units)", D(S("ON_HAND"), S("POS_UNITS"))),
        "ACV_DISTRIBUTION": ("trade", "DIV0(trade.helper_acv_x_pos, trade.pos_dollars)", D(S("ACV_X"), S("POS_DOLLARS"))),
        "PROMO_COUNT": ("promotions", "COUNT(DISTINCT promotions.f_promo_id)", lambda rs: len({r["PROMO_ID"] for r in rs})),
        "PROMO_SPEND": ("promotions", "SUM(promotions.f_promo_spend)", S("PROMO_SPEND")),
        "INCREMENTAL_REVENUE": ("promotions", "SUM(promotions.f_incremental_revenue)", S("INCREMENTAL_REVENUE")),
        "PROMO_ROI": ("promotions", "DIV0(promotions.helper_roi_x_spend, promotions.promo_spend)",
                      D(S("ROI_X"), S("PROMO_SPEND"))),
        "VOLUME_LIFT": ("promotions", "DIV0(promotions.helper_lift_x_spend, promotions.promo_spend)",
                        D(S("LIFT_X"), S("PROMO_SPEND"))),
    }
    return Domain(CPG, tables, dims, M, "Apex Athletic (fictional athletic brand), weekly")


_CACHE: dict[str, Domain] = {}


def get(fqn: str):
    fqn = (fqn or "").upper().replace('"', "")
    if os.environ.get("AA_FAKE_DOMAINS") != "1" or fqn not in (FIN, CPG):
        return None
    if fqn not in _CACHE:
        _CACHE[fqn] = _finance() if fqn == FIN else _cpg()
    return _CACHE[fqn]
