import React from 'react';
import { Bullet, Donut, GroupedBars, Heatmap, LineChart, MiniLine, Pareto, RankedBars, Scatter, SeriesChart, Sparkline, Waterfall, Empty } from './charts.jsx';
import { fmt, pct, tone } from './format.js';


const LOWER_IS_BETTER = /RETURN|STOCKOUT|DELIVERY_DAYS|TRANSIT|CLICK_TO_SHIP|DISCOUNT|LOST|COST|COGS|WEEKS_OF_SUPPLY/i;

function KpiGrid({ data, ctx, spec }) {
  const trend = spec?.show_trend !== false;
  return (
    <>
      <div className="kpis">
        {data.items.map((k, i) => {
          const def = ctx?.defs?.[k.metric];
          const inv = LOWER_IS_BETTER.test(k.metric);
          return (
            <div className={`kpi ${i === 0 ? 'primary' : ''}`} key={k.metric}>
              <div className="kpi-label" title={def || ''}>{k.label}{def ? <span className="def">ⓘ</span> : null}</div>
              <div className="kpi-value">{fmt(k.current, k.kind)}</div>
              <div className="kpi-period">{data.current_label}</div>
              <div className="kpi-delta">
                <span className={`delta ${tone(k.delta, inv)}`}>{arrow(k.delta)} {pct(k.delta)}</span>
                <em>{k.delta_label}{k.base != null ? ` (${fmt(k.base, k.kind)})` : ''}</em>
              </div>
              {trend && <Sparkline values={k.spark} labels={data.spark_labels} kind={k.kind} />}
            </div>
          );
        })}
      </div>
      {trend && <div className="kpi-foot">Lines show the {(data.spark_caption || '').toLowerCase()} · hover a line for each value · green/red already accounts for metrics where lower is better</div>}
    </>
  );
}

function Trend({ data }) {
  return <LineChart points={data.points} kind={data.kind} baselineLabel={data.baseline_label}
    seriesLabel={data.metric_label} />;
}

function Forecast({ data }) {
  return (
    <>
      <LineChart points={data.history} forecast={data.forecast} kind={data.kind} seriesLabel={data.metric_label} />
      <div className="prov">⚙ {data.provenance}</div>
    </>
  );
}

function Ranked({ data, ctx, spec }) {
  return (
    <>
      <div className="sub">{data.dimension_label} · {data.current_label} (marker = {data.prior_label})</div>
      <RankedBars inverse={LOWER_IS_BETTER.test(spec?.metric_id || '')} rows={data.rows} kind={data.kind} currentLabel={data.current_label} priorLabel={data.prior_label}
        onSelect={(r) => ctx.ask(`Why did ${data.metric_label} for ${data.dimension_label} ${r.segment} change in ${data.current_label} vs ${data.prior_label}?`)} />
    </>
  );
}

function Bridge({ data }) {
  return (
    <>
      <Waterfall start={data.start} end={data.end} steps={data.steps} kind={data.kind}
        startLabel={data.start_label} endLabel={data.end_label} />
      <div className={`recon ${data.reconciled ? 'ok' : 'bad'}`}>
        {data.reconciled ? '✓ Reconciled: start + contributions = end' : '✗ Does not reconcile'}
        {' · '}{data.dimension_label} contribution, additive metric
      </div>
      {data.insights?.length > 0 && (
        <div className="insights">
          <div className="insights-title">Key drivers · Snowflake ML Top Insights</div>
          {data.insights.map((ins, i) => (
            <div className="insight" key={i}>
              <span>{ins.contributor.join(' & ')}</span>
              <b className={ins.contribution >= 0 ? 'up' : 'down'}>{ins.contribution >= 0 ? '+' : '−'}{fmt(Math.abs(ins.contribution), data.kind)}</b>
            </div>
          ))}
        </div>
      )}
      {data.insights_pending && <div className="prov">⚙ Snowflake ML Top Insights is analysing drivers…</div>}
      {!data.insights?.length && data.insights_error && (
        <details><summary className="prov muted">Top Insights unavailable — showing the reconciled bridge (details)</summary>
          <pre className="err-pre">{data.insights_error}</pre></details>
      )}
    </>
  );
}

function Exceptions({ data, ctx, spec }) {
  if (!data.rows.length) return <Empty text="No segment deviates materially from its own history." />;
  const inv = LOWER_IS_BETTER.test(data.metric || spec?.metric_id || '');
  const tone = (z) => (z === 0 ? '' : (z > 0) !== inv ? 'up' : 'down');
  return (
    <>
      {data.none_flagged && <div className="exc-calm">No {data.dimension_label?.toLowerCase() || 'segment'} is outside its normal range (|z| ≥ 2). Closest movers to watch:</div>}
      <div className="exc">
        {data.rows.map((r) => (
          <div className="exc-row" key={r.segment}>
            <span className="exc-seg">{r.segment}</span>
            <span className={`sev ${r.severity.toLowerCase()}`}>{r.severity}</span>
            <span className="nums">
              {r.lower != null ? (
                <>{fmt(r.current, data.kind)} vs expected {fmt(r.expected, data.kind)} ·{' '}
                  <b className={tone(r.z)}>{pct(r.deviation, 0)}</b>{' '}
                  <span className="muted">(normal range {fmt(r.lower, data.kind)}–{fmt(r.upper, data.kind)})</span></>
              ) : (
                <>{fmt(r.current, data.kind)} vs norm {fmt(r.expected, data.kind)} ·{' '}
                  <b className={tone(r.z)}>{pct(r.deviation, 0)}</b> (z {r.z.toFixed(1)})</>
              )}
            </span>
            <span className="acts">
              <button type="button" className="link" onClick={() => ctx.ask(`Why is ${data.metric_label} for ${r.segment} ${r.direction} its normal level in the latest period?`)}>Ask agent</button>
              <button type="button" className="link" onClick={() => ctx.decide({
                title: `Investigate ${r.segment} ${data.metric_label.toLowerCase()} (${pct(r.deviation, 0)} vs norm)`,
                detail: `${r.segment} ${data.metric_label} ${fmt(r.current, data.kind)} vs norm ${fmt(r.expected, data.kind)} (z ${r.z.toFixed(1)}).`,
                evidence: { component: spec.component_id, ...r },
              })}>Log decision</button>
            </span>
          </div>
        ))}
      </div>
      <div className="prov">{data.ml && <span className="ml-badge" title={data.provenance || ''}>Snowflake ML · ANOMALY_DETECTION</span>}
        {data.insights_pending && <span className="ml-badge wait">Training Snowflake ML anomaly model…</span>}
        {data.method}</div>
    </>
  );
}

function Actions({ data, ctx }) {
  return (
    <>
      <div className="table-actions"><button type="button" className="btn small" onClick={() => ctx.decide({})}>+ New decision</button></div>
      {!data.rows?.length ? <Empty text="No decisions logged yet. Log one from an exception, an agent answer, or here." /> : (
        <table className="table">
          <thead><tr><th>Decision</th><th>Owner</th><th>Due</th><th>Status</th><th>Logged</th></tr></thead>
          <tbody>
            {data.rows.map((d) => (
              <tr key={d.decision_id}>
                <td><b>{d.title}</b><div className="muted small">{d.detail}</div></td>
                <td>{d.owner || '—'}</td><td>{d.due_date || '—'}</td>
                <td>
                  <select value={d.status} onChange={(e) => ctx.send('decision_status', { decision_id: d.decision_id, status: e.target.value })}>
                    {['Open', 'In progress', 'Done'].map((s) => <option key={s}>{s}</option>)}
                  </select>
                </td>
                <td className="muted small">{d.created_by}<br />{d.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

function Evidence({ data }) {
  return (
    <div className="scroll">
      <div className="sub">{data.period_label}</div>
      <table className="table">
        <thead><tr>{data.columns.map((c) => <th key={c.id}>{c.label}</th>)}</tr></thead>
        <tbody>
          {data.rows.map((r, i) => (
            <tr key={i}>{data.columns.map((c) => <td key={c.id}>{c.type === 'dim' ? r[c.id] : fmt(r[c.id], c.kind)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Multiples({ data }) {
  return (
    <div className="multiples">
      {data.panels.map((p) => {
        const vals = p.points.map((x) => x.value).filter((v) => v != null);
        const change = vals.length > 1 ? (vals[vals.length - 1] - vals[0]) / Math.abs(vals[0] || 1) : null;
        return (
          <div className="multiple" key={p.segment}>
            <div className="multiple-head"><b>{p.segment}</b><span className={`delta ${tone(change)}`}>{pct(change, 0)}</span></div>
            <MiniLine points={p.points} kind={data.kind} />
            <div className="muted small">{fmt(vals[vals.length - 1], data.kind)} latest</div>
          </div>
        );
      })}
    </div>
  );
}

function Matrix({ data }) {
  return <Heatmap rows={data.rows} cols={data.cols} values={data.values} kind={data.kind}
    rowLabel={data.row_label} colLabel={data.col_label} />;
}

function Share({ data }) {
  return (
    <>
      <div className="sub">{data.dimension_label} · {data.period_label}</div>
      <Donut slices={data.slices} kind={data.kind} total={data.total} centerLabel={data.metric_label} />
    </>
  );
}

function ParetoTile({ data }) {
  return (
    <>
      <div className="sub">{data.dimension_label} · {data.period_label}
        {data.n80 ? <> · <b>{data.n80} of {data.total_count}</b> make up 80%</> : null}</div>
      <Pareto rows={data.rows} kind={data.kind} />
    </>
  );
}

function ScatterTile({ data, ctx }) {
  return (
    <>
      <div className="sub">Each point = one {data.dimension_label} · {data.period_label}</div>
      <Scatter points={data.points} xKind={data.x_kind} yKind={data.y_kind} xLabel={data.x_label} yLabel={data.y_label} />
    </>
  );
}

function Compare({ data, spec }) {
  return <GroupedBars rows={data.rows} kind={data.kind} labels={data.labels} inverse={LOWER_IS_BETTER.test(spec?.metric_id || '')} />;
}

/* ------------------------------------------------------------------ persona tiles */
const dtxt = (d, kind) => (d == null ? '—' : kind === 'percent' ? `${d > 0 ? '+' : ''}${(d * 100).toFixed(1)} pt` : pct(d));
const STATUS_CLS = { good: 'up', ok: 'flat', warn: 'warn', bad: 'down' };

const arrow = (d) => (d == null || Math.abs(d) < 0.0005 ? '▬' : d > 0 ? '▲' : '▼');
const absVar = (k) => (k.value == null || k.target == null ? null : k.value - k.target);
const signed = (v, kind) => (v == null ? '—' : kind === 'percent' ? `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)} pt`
  : `${v > 0 ? '+' : ''}${fmt(v, kind)}`);
export const KPI_DISPLAYS = [['bullet', 'Bullet bars (actual vs target)'], ['variance', 'Variance with arrows'], ['table', 'Variance table']];

/** Executive: YTD vs plan (or last year). Shown as bullet bars (default), variance cards with arrows, or a
 * compact variance table - the tile menu's "Show as" switches it; the numbers are the same in all three. */
function KpiPlan({ data, ctx, spec }) {
  const mode = spec?.display || 'bullet';
  if (mode === 'table') {
    return (
      <>
        <table className="table kplan-table">
          <thead><tr><th>Metric</th><th className="num">{data.period_label}</th><th className="num">Target</th>
            <th className="num">Variance</th><th className="num">Variance %</th><th className="num">{data.month_label}</th></tr></thead>
          <tbody>
            {data.items.map((k) => (
              <tr key={k.metric}>
                <td title={ctx?.defs?.[k.metric] || ''}>{k.label}</td>
                <td className="num"><b>{fmt(k.value, k.kind)}</b></td>
                <td className="num">{fmt(k.target, k.kind)} <span className="muted small">{k.target_label === 'plan' ? 'plan' : 'LY'}</span></td>
                <td className={`num delta ${STATUS_CLS[k.status]}`}>{arrow(absVar(k))} {signed(absVar(k), k.kind)}</td>
                <td className={`num delta ${STATUS_CLS[k.status]}`}>{k.kind === 'percent' ? '' : dtxt(k.delta, k.kind)}</td>
                <td className="num">{fmt(k.month, k.kind)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="kpi-foot">Target = plan where the metric has one, otherwise last year · ▲▼ colour already accounts for metrics where lower is better</div>
      </>
    );
  }
  return (
    <>
      <div className="kplan">
        {data.items.map((k) => (
          <div className={`kplan-card st-${k.status}`} key={k.metric}>
            <div className="kpi-label" title={ctx?.defs?.[k.metric] || ''}>{k.label}</div>
            {mode === 'variance' ? (
              <>
                <div className="kplan-row"><span className="kpi-value">{fmt(k.value, k.kind)}</span></div>
                <div className={`kplan-var ${STATUS_CLS[k.status]}`}>
                  <span className="arr">{arrow(k.delta)}</span>
                  <b>{dtxt(k.delta, k.kind)}</b>
                  {k.kind !== 'percent' && <span>{signed(absVar(k), k.kind)}</span>}
                  <em>vs {k.target_label} ({fmt(k.target, k.kind)})</em>
                </div>
              </>
            ) : (
              <>
                <div className="kplan-row">
                  <span className="kpi-value">{fmt(k.value, k.kind)}</span>
                  <span className={`delta ${STATUS_CLS[k.status]}`}>{arrow(k.delta)} {dtxt(k.delta, k.kind)}</span>
                  <em>vs {k.target_label}</em>
                </div>
                <Bullet value={k.value} target={k.target} good={k.status === 'bad' ? false : undefined} />
              </>
            )}
            <div className="kplan-foot">
              {mode !== 'variance' && <span>{k.target_label === 'plan' ? 'Plan' : 'Last year'} {fmt(k.target, k.kind)}</span>}
              {k.target_label === 'plan' && k.py != null && <span>LY {arrow(k.delta_py)} {dtxt(k.delta_py, k.kind)}</span>}
              {k.month != null && <span>{data.month_label}: {fmt(k.month, k.kind)}{k.month_delta != null ? ` (${dtxt(k.month_delta, k.kind)})` : ''}</span>}
            </div>
          </div>
        ))}
      </div>
      <div className="kpi-foot">{data.period_label} · {mode === 'bullet' ? `bar = actual, tick = ${data.has_plan ? 'plan (last year where a metric has no plan)' : 'last year'} · ` : ''}colour and ▲▼ already account for metrics where lower is better</div>
    </>
  );
}

function SeriesTile({ data }) {
  const fc = data.series?.some((s) => s.style === 'forecast');
  const nowLabel = data.mode === 'hour' ? `now · ${data.labels?.[data.now_index] || ''}` : data.mode === 'ytd' ? 'latest month' : 'today';
  return (
    <>
      {data.mode === 'hour' && data.pace != null && (
        <div className="pace-head"><b className={data.pace >= 0 ? 'up' : 'down'}>{pct(data.pace)}</b> vs the same time last week
          {data.projected != null && <> · on this pace the day closes near <b>{fmt(data.projected, data.kind)}</b></>}</div>
      )}
      <SeriesChart labels={data.labels} series={data.series} band={data.band} kind={data.kind}
        nowIndex={data.now_index} nowLabel={nowLabel} />
      <div className="prov">
        {fc && <span className="ml-badge" title={data.provenance || ''}>Snowflake ML · FORECAST</span>}
        {data.insights_pending && <span className="ml-badge wait">Training Snowflake ML forecast to year end…</span>}
        {data.caption}
      </div>
    </>
  );
}

/** Operations: big status cards, today so far vs the same time last week. */
function StatusTiles({ data, ctx }) {
  return (
    <>
      <div className="status-row">
        {data.items.map((k) => (
          <div className={`status-card st-${k.status}`} key={k.metric}>
            <div className="kpi-label" title={ctx?.defs?.[k.metric] || ''}>{k.label}{k.timed ? '' : ' (today)'}</div>
            <div className="status-val">{fmt(k.current, k.kind)}</div>
            <div className="kpi-delta"><span className={`delta ${STATUS_CLS[k.status]}`}>{arrow(k.delta)} {dtxt(k.delta, k.kind)}</span>
              <em>{data.compare_label}{k.base != null ? ` (${fmt(k.base, k.kind)})` : ''}</em></div>
            {k.avg != null && <div className="muted small">4-week normal {fmt(k.avg, k.kind)}</div>}
          </div>
        ))}
      </div>
    </>
  );
}

function HourHeat({ data }) {
  return <Heatmap rows={data.rows} cols={data.cols} values={data.values} kind={data.kind} rowLabel={data.row_label} colLabel={data.col_label} />;
}

/** Operations: what is off today, worst first, with actions on every row. */
function Worklist({ data, ctx, spec }) {
  if (!data.rows?.length) return <Empty text="Nothing is off today compared with a normal day." />;
  return (
    <>
      {data.none_flagged && <div className="exc-calm">Nothing is outside its normal range today. Closest movers to watch:</div>}
      <table className="table worklist">
        <thead><tr><th /><th>What</th><th>Where</th><th className="num">Today</th><th className="num">Normal {data.today_label?.slice(0, 3)}</th><th className="num">Change</th><th /></tr></thead>
        <tbody>
          {data.rows.map((r, i) => (
            <tr key={i}>
              <td><span className={`sevdot ${r.severity.toLowerCase()}`} title={`${r.severity} · z ${r.z.toFixed(1)}`} /></td>
              <td><b>{r.metric_label}</b></td>
              <td>{r.segment} <span className="muted small">{r.dimension_label}</span></td>
              <td className="num">{fmt(r.current, r.kind)}</td>
              <td className="num muted">{fmt(r.normal, r.kind)}</td>
              <td className="num"><b className="down">{dtxt(r.deviation, r.kind)}</b></td>
              <td className="acts">
                <button type="button" className="link" onClick={() => ctx.ask(`Why is ${r.metric_label} for ${r.segment} (${r.dimension_label}) ${r.deviation > 0 ? 'above' : 'below'} a normal ${data.today_label?.slice(0, 3)} today, and what should we do now?`)}>Ask agent</button>
                <button type="button" className="link" onClick={() => ctx.decide({
                  title: `Act on ${r.segment} ${r.metric_label.toLowerCase()} today (${dtxt(r.deviation, r.kind)})`,
                  detail: `${r.segment} (${r.dimension_label}) ${r.metric_label} ${fmt(r.current, r.kind)} today vs normal ${fmt(r.normal, r.kind)}.`,
                  evidence: { component: spec.component_id, ...r },
                })}>Log decision</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="prov">{data.method}</div>
    </>
  );
}

/** Manager: dimension x KPI scorecard, RAG vs plan/prior; click a row to filter the dashboard to it. */
function Scorecard({ data, ctx }) {
  const cols = data.columns;
  const cell = (c, col, i) => (
    <td key={i} className={`sc-cell st-${c.status}`} title={c.base != null ? `${col.compare === 'plan' ? 'Plan' : col.compare}: ${fmt(c.base, col.kind)}` : ''}>
      <span className="sc-val">{fmt(c.value, col.kind)}</span>
      <span className={`sc-d ${STATUS_CLS[c.status]}`}>{dtxt(c.delta, col.kind)}</span>
    </td>
  );
  return (
    <>
      <table className="table scorecard">
        <thead><tr><th>{data.dimension_label}</th>{cols.map((c) => <th key={c.metric} className="num">{c.label}<div className="muted small">vs {c.compare}</div></th>)}</tr></thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.segment} className="sc-row" title={`Filter the dashboard to ${r.segment}`}
              onClick={() => ctx.drill && ctx.drill(data.dimension, r.segment)}>
              <td><b>{r.segment}</b></td>{r.cells.map((c, i) => cell(c, cols[i], i))}
            </tr>
          ))}
          <tr className="sc-total"><td>Total</td>{data.total.cells.map((c, i) => cell(c, cols[i], i))}</tr>
        </tbody>
      </table>
      <div className="kpi-foot">{data.period_label} · green ahead, amber slightly behind, red ≥10% (or ≥2 pt) behind · click a row to drill into it</div>
    </>
  );
}

export const REGISTRY = {
  kpi_grid: KpiGrid, kpi_card: KpiGrid, trend_chart: Trend, forecast_band: Forecast,
  ranked_bar: Ranked, target_bar: Ranked, capacity_chart: Ranked, small_multiples: Multiples,
  driver_bridge: Bridge, exception_table: Exceptions, exception_queue: Exceptions, risk_table: Exceptions,
  action_table: Actions, evidence_table: Evidence, segment_matrix: Matrix,
  detail_table: Evidence, heatmap: Matrix, share_donut: Share, pareto: ParetoTile, scatter: ScatterTile,
  period_compare: Compare,
  kpi_plan: KpiPlan, ytd_trajectory: SeriesTile, pace_chart: SeriesTile, status_tiles: StatusTiles,
  hour_heatmap: HourHeat, worklist: Worklist, scorecard: Scorecard,
};

export const SPAN = {
  kpi_grid: 12, kpi_card: 4, trend_chart: 7, forecast_band: 8, small_multiples: 12, driver_bridge: 7,
  ranked_bar: 5, target_bar: 5, capacity_chart: 5, exception_table: 5, risk_table: 5, exception_queue: 12,
  action_table: 12, evidence_table: 12, segment_matrix: 12, detail_table: 12, heatmap: 12, share_donut: 4,
  pareto: 6, scatter: 6, period_compare: 6,
  kpi_plan: 12, ytd_trajectory: 7, pace_chart: 7, status_tiles: 12, hour_heatmap: 5, worklist: 12, scorecard: 8,
};

/** Pack components into 12-column rows; stretch the last item of each row to fill it. */
export function pack(components) {
  const out = [];
  let row = [];
  let used = 0;
  const flush = () => {
    if (row.length) { row[row.length - 1].span += 12 - used; out.push(...row); }
    row = []; used = 0;
  };
  components.forEach((c) => {
    const span = Math.max(3, Math.min(12, c.width || SPAN[c.type] || 6));
    if (used + span > 12) flush();
    row.push({ ...c, span }); used += span;
  });
  flush();
  return out;
}
