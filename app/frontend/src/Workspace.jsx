import React, { useEffect, useMemo, useRef, useState } from 'react';
import { KPI_DISPLAYS, REGISTRY, pack } from './registry.jsx';
import { AUDIENCE_LABELS, CAP_LABELS, label } from './format.js';

const SWAPPABLE = ['trend_chart', 'forecast_band', 'ranked_bar', 'period_compare', 'share_donut', 'pareto', 'scatter',
  'heatmap', 'small_multiples', 'driver_bridge', 'exception_table'];
const GRAINS = [['', 'Audience default'], ['month', 'Monthly'], ['week', 'Weekly'], ['day', 'Daily'], ['quarter', 'Quarterly']];
const COMPARES = [['prior', 'Previous period'], ['yoy', 'Same period last year'], ['plan', 'Plan / target']];

function tileMetrics(c) { return [c.metric_id, c.metric2_id, ...(c.metrics || [])].filter((x) => x && !String(x).includes(':')); }

/* ------------------------------------------------------------------ time & filter bar */
function ViewBar({ data, send, pageId }) {
  const v = data.view || {};
  const cal = data.profile?.calendar || {};
  const set = (patch) => send('set_view', { ...patch, page_id: pageId }, 'Re-running governed queries…');
  const filters = v.filters || {};
  return (
    <div className="viewbar">
      <label className="vb-item"><span>Period</span>
        <select value={v.grain || ''} onChange={(e) => set({ grain: e.target.value || null })}>
          {GRAINS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
      </label>
      <span className="vb-now" title={`Latest complete ${cal.grain}; data through ${cal.max_date}`}>
        Showing <b>{cal.current_label}</b></span>
      <label className="vb-item"><span>Compare to</span>
        <select value={v.compare || 'prior'} onChange={(e) => set({ compare: e.target.value })}>
          {COMPARES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
      </label>
      {(data.filter_dims || []).map((d) => (
        <label className="vb-item" key={d.id}><span>{d.label}</span>
          <select value={(filters[d.id] || [])[0] || ''}
            onChange={(e) => set({ filters: { ...filters, [d.id]: e.target.value ? [e.target.value] : [] } })}>
            <option value="">All</option>
            {(data.filter_options?.[d.id] || []).map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
      ))}
      {Object.entries(filters).filter(([k, v]) => v?.length && !(data.filter_dims || []).some((d) => d.id === k)).map(([k, v]) => (
        <span className="fchip" key={k}>{label(k)}: <b>{v.join(', ')}</b>
          <button type="button" title="Remove" onClick={() => { const f = { ...filters }; delete f[k]; set({ filters: f }); }}>×</button></span>
      ))}
      {Object.keys(filters).length > 0 && <button type="button" className="link" onClick={() => set({ filters: {} })}>Clear filters</button>}
      <span className="vb-live"><i /> Live · data through {cal.max_date}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ persona strip */
const REFRESH_MS = 5 * 60 * 1000;
function PersonaStrip({ persona, data, onRefresh, auto, setAuto, refreshedAt }) {
  const cal = data.profile?.calendar || {};
  if (persona === 'daily_operations') {
    return (
      <div className="pstrip live">
        <span><i className="pulse" /> <b>Live</b> · today {cal.max_date} · compared with the same weekday last week, same hours</span>
        <span className="pstrip-r">Refreshed {refreshedAt}
          <label className="auto"><input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> auto-refresh every 5 min</label>
          <button type="button" className="link" onClick={onRefresh}>Refresh now</button></span>
      </div>
    );
  }
  if (persona === 'executives') {
    return (
      <div className="pstrip">
        <span><b>Executive brief</b> · year to date through {cal.current_label} · against plan, and last year where there is no plan</span>
        <span className="pstrip-r">Data as of {cal.max_date}</span>
      </div>
    );
  }
  if (persona === 'managers') {
    return (
      <div className="pstrip">
        <span><b>Weekly scorecard</b> · {cal.current_label} vs plan (or the prior week) · click a scorecard row to drill in</span>
        <span className="pstrip-r">Data as of {cal.max_date}</span>
      </div>
    );
  }
  return null;
}

/* ------------------------------------------------------------------ tile menu */
/** What the semantic view and the chart type allow, so menus only offer choices that will work. */
function fieldRules(data) {
  const md = data.model?.metric_dims || {};
  const allMetrics = data.model?.metrics || [];
  const allDims = (data.model?.dimensions || []).filter((d) => !d.is_time);
  const distinct = data.distinct || {};
  const okDims = (metricIds, type, which = 'dim') => {
    const ids = (metricIds || []).filter((m) => m && md[m]);
    const rng = data.tile_types?.[type]?.[which === 'dim2' ? 'dim2_range' : 'dim_range'];
    return allDims.filter((d) => ids.every((m) => md[m].includes(d.id))
      && (!rng || distinct[d.id] == null || (distinct[d.id] >= rng[0] && distinct[d.id] <= rng[1])));
  };
  const okMetrics = (dimIds, type) => {
    const ids = (dimIds || []).filter(Boolean);
    const additive = data.tile_types?.[type]?.additive;
    return allMetrics.filter((m) => (!md[m.id] || ids.every((d) => md[m.id].includes(d))) && (!additive || m.additive));
  };
  const label = (list, id) => list.find((x) => x.id === id)?.label || (id || '').split('.').pop().replace(/_/g, ' ').toLowerCase();
  return { okDims, okMetrics, allMetrics, allDims, label, distinct };
}

/** Keep the current value selectable even if it is no longer in the filtered list. */
function withCurrent(list, id, all) {
  return !id || list.some((x) => x.id === id) ? list : [all.find((x) => x.id === id) || { id, label: id }, ...list];
}

function TileMenu({ c, page, data, send, onClose }) {
  const R = fieldRules(data);
  const dim = c.dimension || c.role_bindings?.segment || c.role_bindings?.region || '';
  const upd = (patch) => { send('tile_update', { page_id: page.page_id, component_id: c.component_id, patch }, 'Validating & re-querying…'); onClose(); };
  const current = c.metrics || [data.bindings?.primary_metric, ...(data.bindings?.supporting_metrics || [])].filter(Boolean);
  const gov = (data.spec?.governance || []).filter((g) => g.tile === c.title).slice(-2);
  const n = (d) => (R.distinct?.[d] != null ? ` (${R.distinct[d]})` : '');
  const isKpi = ['kpi_grid', 'kpi_card'].includes(c.type);
  const metricOpts = withCurrent(R.okMetrics([dim, c.dimension2], c.type), c.metric_id, R.allMetrics);
  const metric2Opts = withCurrent(R.okMetrics([dim], c.type).filter((m) => m.id !== c.metric_id), c.metric2_id, R.allMetrics);
  const dimOpts = withCurrent(R.okDims([c.metric_id, c.metric2_id], c.type), dim, R.allDims);
  const dim2Opts = withCurrent(R.okDims([c.metric_id], c.type, 'dim2').filter((d) => d.id !== dim), c.dimension2, R.allDims);
  const hidden = R.allDims.length - R.okDims([c.metric_id, c.metric2_id], c.type).length;
  return (
    <div className="tmenu" onMouseLeave={onClose}>
      {SWAPPABLE.includes(c.type) && (
        <label>Chart type<select value={c.type} onChange={(e) => upd({ type: e.target.value })}>
          {SWAPPABLE.map((t) => <option key={t} value={t}>{data.tile_types?.[t]?.label || t}</option>)}</select></label>
      )}
      {c.metric_id && !isKpi && (
        <label>{c.type === 'scatter' ? 'Metric (x axis)' : 'Metric'}<select value={c.metric_id} onChange={(e) => upd({ metric_id: e.target.value })}>
          {metricOpts.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</select></label>
      )}
      {c.type === 'scatter' && (
        <label>Metric (y axis)<select value={c.metric2_id || ''} onChange={(e) => upd({ metric2_id: e.target.value })}>
          {metric2Opts.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</select></label>
      )}
      {dim && SWAPPABLE.includes(c.type) && !['trend_chart', 'forecast_band'].includes(c.type) && (
        <label>{c.type === 'heatmap' ? 'Rows' : c.type === 'scatter' ? 'One point per' : 'Break down by'}<select value={dim} onChange={(e) => upd({ dimension: e.target.value })}>
          {dimOpts.map((d) => <option key={d.id} value={d.id}>{d.label}{n(d.id)}</option>)}</select></label>
      )}
      {c.type === 'heatmap' && (
        <label>Columns<select value={c.dimension2 || ''} onChange={(e) => upd({ dimension2: e.target.value })}>
          {dim2Opts.map((d) => <option key={d.id} value={d.id}>{d.label}{n(d.id)}</option>)}</select></label>
      )}
      {hidden > 0 && !isKpi && dim && <div className="muted small tmenu-note">{hidden} breakdown{hidden > 1 ? 's' : ''} hidden: not related to this metric in the semantic view, or too many/few values for this chart.</div>}
      {['kpi_grid', 'kpi_card', 'detail_table', 'evidence_table'].includes(c.type) && (
        <>
          <label>Add metric<select value="" onChange={(e) => e.target.value && upd({ metrics: [...current, e.target.value], type: c.type === 'kpi_card' ? 'kpi_grid' : c.type === 'evidence_table' ? 'detail_table' : c.type })}>
            <option value="">Choose…</option>
            {R.okMetrics(c.type === 'detail_table' ? (c.dimensions || []) : [], c.type).filter((m) => !current.includes(m.id)).map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</select></label>
          {current.length > 1 && (
            <label>Remove metric<select value="" onChange={(e) => e.target.value && upd({ metrics: current.filter((x) => x !== e.target.value), type: c.type === 'kpi_card' ? 'kpi_grid' : c.type === 'evidence_table' ? 'detail_table' : c.type })}>
              <option value="">Choose…</option>
              {current.map((id) => <option key={id} value={id}>{R.label(R.allMetrics, id)}</option>)}</select></label>
          )}
        </>
      )}
      {c.type === 'kpi_plan' && (
        <label>Show as<select value={c.display || 'bullet'} onChange={(e) => upd({ display: e.target.value })}>
          {KPI_DISPLAYS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
      )}
      {isKpi && (
        <label className="tmenu-check"><input type="checkbox" checked={c.show_trend !== false}
          onChange={(e) => upd({ show_trend: e.target.checked })} /> Trend line under each card</label>
      )}
      <label>Width<select value={c.width || c.span} onChange={(e) => upd({ width: Number(e.target.value) })}>
        {(isKpi || ['heatmap', 'detail_table'].includes(c.type) ? [6, 7, 8, 9, 12] : [3, 4, 5, 6, 7, 8, 9, 12]).map((w) => <option key={w} value={w}>{w === 12 ? 'Full width' : `${w}/12`}</option>)}</select></label>
      <div className="tmenu-row">
        <button type="button" className="ghost small" onClick={() => { send('tile_move', { page_id: page.page_id, component_id: c.component_id, dir: -1 }, 'Moving…'); onClose(); }}>← Move</button>
        <button type="button" className="ghost small" onClick={() => { send('tile_move', { page_id: page.page_id, component_id: c.component_id, dir: 1 }, 'Moving…'); onClose(); }}>Move →</button>
        <button type="button" className="ghost small danger-txt" onClick={() => { send('tile_remove', { page_id: page.page_id, component_id: c.component_id }, 'Removing…'); onClose(); }}>Remove</button>
      </div>
      <div className="tmenu-why"><b>Why this chart?</b>
        <div>{c.question || 'Answers the page question for this metric.'}</div>
        {gov.map((g, i) => <div key={i} className="muted small">Validator: {g.action} — {g.reason}</div>)}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ add tile */
function AddTile({ page, data, send, onClose }) {
  const R = fieldRules(data);
  const [mode, setMode] = useState('describe');
  const [text, setText] = useState('');
  const [type, setType] = useState('ranked_bar');
  const [metric, setMetric] = useState(data.bindings?.primary_metric || '');
  const [metric2, setMetric2] = useState('');
  const [dim, setDim] = useState(data.bindings?.segment_dimension || '');
  const [dim2, setDim2] = useState('');
  const needsDim = !['trend_chart', 'forecast_band', 'kpi_grid', 'kpi_plan', 'status_tiles', 'ytd_trajectory', 'pace_chart', 'hour_heatmap'].includes(type);
  const metricOpts = R.okMetrics([], type);
  const dimOpts = R.okDims([metric, type === 'scatter' ? metric2 : null], type);
  const metric2Opts = R.okMetrics([], type).filter((m) => m.id !== metric);
  const dim2Opts = R.okDims([metric], type, 'dim2').filter((d) => d.id !== dim);
  // keep selections valid when the chart type or metric changes
  useEffect(() => { if (metricOpts.length && !metricOpts.some((m) => m.id === metric)) setMetric(metricOpts[0].id); }, [type]);
  useEffect(() => { if (needsDim && dimOpts.length && !dimOpts.some((d) => d.id === dim)) setDim(dimOpts[0].id); }, [type, metric, metric2]);
  useEffect(() => { if (type === 'scatter' && (!metric2 || metric2 === metric) && metric2Opts.length) setMetric2(metric2Opts[0].id); }, [type, metric]);
  useEffect(() => { if (type === 'heatmap' && (!dim2 || dim2 === dim) && dim2Opts.length) setDim2(dim2Opts[0].id); }, [type, metric, dim]);
  return (
    <div className="addtile">
      <div className="idea-tabs">
        <button type="button" className={`seg ${mode === 'describe' ? 'on' : ''}`} onClick={() => setMode('describe')}>✦ Describe it</button>
        <button type="button" className={`seg ${mode === 'pick' ? 'on' : ''}`} onClick={() => setMode('pick')}>Pick chart & fields</button>
      </div>
      {mode === 'describe' ? (
        <div className="addtile-row">
          <input autoFocus placeholder="e.g. free shipping % by region vs last year" value={text} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && text.trim()) { send('tile_add', { page_id: page.page_id, instruction: text }, 'Cortex is designing the tile…'); onClose(); } }} />
          <button type="button" className="btn small ghost-ai" disabled={!text.trim()}
            onClick={() => { send('tile_add', { page_id: page.page_id, instruction: text }, 'Cortex is designing the tile…'); onClose(); }}>Add</button>
        </div>
      ) : (
        <div className="addtile-row wrap">
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {['kpi_grid', ...SWAPPABLE, 'detail_table', 'kpi_plan', 'ytd_trajectory', 'scorecard', 'status_tiles', 'pace_chart', 'hour_heatmap', 'worklist']
              .filter((t) => data.tile_types?.[t]).map((t) => <option key={t} value={t}>{data.tile_types?.[t]?.label || t}</option>)}
          </select>
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>{metricOpts.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</select>
          {type === 'scatter' && <select value={metric2} onChange={(e) => setMetric2(e.target.value)}>{metric2Opts.map((m) => <option key={m.id} value={m.id}>vs {m.label}</option>)}</select>}
          {needsDim && <select value={dim} onChange={(e) => setDim(e.target.value)}>{dimOpts.map((d) => <option key={d.id} value={d.id}>by {d.label}</option>)}</select>}
          {type === 'heatmap' && <select value={dim2} onChange={(e) => setDim2(e.target.value)}>{dim2Opts.map((d) => <option key={d.id} value={d.id}>× {d.label}</option>)}</select>}
          <button type="button" className="btn small" disabled={needsDim && !dimOpts.length} onClick={() => {
            send('tile_add_manual', { page_id: page.page_id, type, metric, metric2: type === 'scatter' ? metric2 : null, metrics: [metric],
              dimension: needsDim ? dim : null, dimension2: type === 'heatmap' ? dim2 : null, dimensions: [dim] }, 'Validating & querying…'); onClose();
          }}>Add</button>
        </div>
      )}
      {mode === 'pick' && needsDim && !dimOpts.length && <div className="muted small">No breakdown in the semantic view works with this metric and chart; pick another metric or chart.</div>}
      <div className="muted small">Lists only show combinations the semantic view supports. Every new tile still goes through the validator.</div>
    </div>
  );
}

/* ------------------------------------------------------------------ per-tile AI panel */
export function TilePanel({ tile, page, data, send, pending, onClose, viewer }) {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('auto');
  const endRef = useRef(null);
  const cid = `${page.page_id}/${tile.component_id}`;
  const chat = data.tile_chat?.[cid] || [];
  useEffect(() => { endRef.current?.scrollIntoView({ block: 'end' }); }, [chat.length, pending]);
  const m = (id) => data.model?.metrics?.find((x) => x.id === id)?.label || (id || '').split('.').pop();
  const d = (id) => data.model?.dimensions?.find((x) => x.id === id)?.label || (id || '').split('.').pop();
  const cal = data.profile?.calendar || {};
  const metric = m(tile.metric_id || (tile.metrics || [])[0]);
  const otherDim = (data.model?.dimensions || []).find((x) => !x.is_time && x.id !== tile.dimension)?.label;
  const suggestions = [
    ['ask', `Why did ${metric} change in ${cal.current_label} vs ${cal.prior_label}?`],
    tile.dimension && ['ask', `Which ${d(tile.dimension)} drove most of the change in ${metric}?`],
    ['ask', `What should I do about this ${metric} result?`],
    !viewer && tile.type !== 'trend_chart' && ['edit', 'Show this as a line chart over time'],
    !viewer && otherDim && tile.dimension && ['edit', `Split this by ${otherDim}`],
  ].filter(Boolean);
  const go = (t, md) => { if (!t.trim()) return; send('tile_ask', { page_id: page.page_id, component_id: tile.component_id, text: t, mode: md === 'auto' ? undefined : md },
    md === 'edit' ? 'Cortex is changing the tile…' : 'Cortex Agent is answering…', true); setText(''); };
  const busy = pending?.type === 'tile_ask';
  return (
    <div className="tpanel">
      <div className="tpanel-head">
        <div><div className="ai-title">✦ Tile assistant</div><b>{tile.title}</b>
          <div className="muted small">{data.tile_types?.[tile.type]?.label || tile.type} · {metric}{tile.dimension ? ` by ${d(tile.dimension)}` : ''} · {cal.current_label}</div></div>
        <button type="button" className="x" onClick={onClose}>×</button>
      </div>
      <div className="tpanel-sub">Questions go to the <b>Cortex Agent</b> (governed SQL on this semantic view, with this tile's context).
        {!viewer && <> Change requests go to <b>Cortex</b> and through the layout validator.</>}</div>
      <div className="tchat">
        {!chat.length && (
          <div className="tsuggest">
            {suggestions.map(([md, s]) => (
              <button type="button" key={s} className={`chip ${md}`} onClick={() => go(s, md)}>{md === 'edit' ? '✎ ' : '? '}{s}</button>
            ))}
          </div>
        )}
        {chat.map((x, i) => (
          <div key={i} className={`msg ${x.role}`}>
            <div className="bubble">
              {x.error ? <div className="alert error small">{x.error}</div> : <div className="answer">{x.text}</div>}
              {x.tables?.map((t, j) => (
                <table className="table compact" key={j}><thead><tr>{t.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                  <tbody>{t.rows.slice(0, 8).map((r, k) => <tr key={k}>{r.map((v, n) => <td key={n}>{String(v)}</td>)}</tr>)}</tbody></table>
              ))}
              {x.actions?.map((a) => <div key={a.id} className="act-card">✓ Agent logged decision <b>{a.id}</b></div>)}
              {x.citations?.length > 0 && (
                <div className="cites"><span>Sources</span>{x.citations.map((c, j) => <span key={j} className="cite" title={c.text}>{c.label}</span>)}</div>
              )}
              {x.sql?.length > 0 && <details><summary className="prov">SQL generated by Cortex Analyst</summary><pre>{x.sql[0]}</pre></details>}
              {(x.provenance || x.agent) && <div className="prov">{x.provenance || x.agent}{x.latency ? ` · ${x.latency}s` : ''}</div>}
            </div>
          </div>
        ))}
        {busy && <div className="msg agent"><div className="bubble typing">{pending.label}</div></div>}
        <div ref={endRef} />
      </div>
      <form className="task" onSubmit={(e) => { e.preventDefault(); go(text, mode); }}>
        {!viewer && (
          <div className="idea-tabs">
            {[['auto', 'Auto'], ['ask', 'Ask'], ['edit', 'Change tile']].map(([k, l]) => (
              <button type="button" key={k} className={`seg ${mode === k ? 'on' : ''}`} onClick={() => setMode(k)}>{l}</button>))}
          </div>
        )}
        <div className="addtile-row">
          <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)} disabled={busy}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(text, mode); } }}
            placeholder={viewer ? 'Ask about this tile…' : 'Ask about this tile, or request a change…'}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(text, viewer ? 'ask' : mode); } }} />
          <button type="submit" className="send" disabled={busy || !text.trim()}>↑</button>
        </div>
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ publish */
function PublishDialog({ data, send, name, onClose }) {
  const [title, setTitle] = useState(name);
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState('');
  const [note, setNote] = useState('');
  useEffect(() => { if (!data.roles?.length) send('list_roles', {}, 'Loading roles…', true); }, []);
  const share = data.share;
  const toggle = (r) => setRoles((x) => (x.includes(r) ? x.filter((y) => y !== r) : [...x, r]));
  return (
    <div className="modal-back">
      <div className="modal publish">
        {share && share.name === title ? (
          <>
            <h3>✓ Published "{share.name}" v{share.version}</h3>
            <p>Viewers get a read-only dashboard: no builder controls, same live governed numbers, filters, tooltips and the tile assistant (questions only).</p>
            <div className="share-box">
              <div><b>Viewer link</b></div>
              <code className="mono">{share.link}</code>
              <div className="muted small">Viewers open the app from Snowsight; it goes straight to this dashboard. It is also listed under "Published dashboards" on the home page.</div>
            </div>
            {share.granted?.length > 0 && <div className="alert ok small">App access granted to roles: {share.granted.join(', ')}</div>}
            {share.failed?.length > 0 && <div className="alert warn small">Could not grant: {share.failed.join('; ')}</div>}
            <div className="muted small">Numbers are queried with the app owner's role (Streamlit in Snowflake runs with owner's rights), so every viewer sees the same governed data. Per-viewer row filtering is on the roadmap.</div>
            <div className="modal-foot"><button type="button" className="btn" onClick={onClose}>Done</button></div>
          </>
        ) : (
          <>
            <h3>Publish dashboard</h3>
            <p className="muted small">Publishing freezes this version for viewers. Keep editing here and publish again to release v{(data.dashboard?.version || 0) + 1}.</p>
            <label>Name<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
            <label>Share with roles <span className="muted small">(grants USAGE on this app)</span></label>
            <div className="role-list">
              {(data.roles || []).length === 0 && <span className="muted small">Loading roles…</span>}
              {(data.roles || []).filter((r) => !['ACCOUNTADMIN', 'ORGADMIN', 'SECURITYADMIN', 'USERADMIN', 'SYSADMIN'].includes(r)).map((r) => (
                <button type="button" key={r} className={`chip ${roles.includes(r) ? 'on' : ''}`} onClick={() => toggle(r)}>{roles.includes(r) ? '✓ ' : ''}{r}</button>
              ))}
            </div>
            <label>Limit to users <span className="muted small">(optional, comma-separated Snowflake user names)</span>
              <input value={users} onChange={(e) => setUsers(e.target.value)} placeholder="e.g. JDOE, ASMITH" /></label>
            <label>Release note<input value={note} onChange={(e) => setNote(e.target.value)} placeholder="What changed in this version" /></label>
            <div className="modal-foot">
              <button type="button" className="ghost" onClick={onClose}>Cancel</button>
              <button type="button" className="btn" onClick={() => send('publish', { name: title, roles, users: users.split(',').map((x) => x.trim()).filter(Boolean), note }, 'Publishing to Snowflake…')}>Publish</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ workspace */
export default function Workspace({ data, send, ctx, pending }) {
  const spec = data.spec;
  const viewer = !!data.viewer_mode;
  const [pageId, setPageId] = useState(spec.pages[0].page_id);
  const [name, setName] = useState(data.dashboard?.name || spec.display_name);
  const [menu, setMenu] = useState(null);
  const [panel, setPanel] = useState(null);
  const [adding, setAdding] = useState(false);
  const [newPage, setNewPage] = useState(null);
  const [renaming, setRenaming] = useState(null);
  const [publishing, setPublishing] = useState(false);
  useEffect(() => {
    if (data.focus_page && spec.pages.find((p) => p.page_id === data.focus_page)) setPageId(data.focus_page);
    else if (!spec.pages.find((p) => p.page_id === pageId)) setPageId(spec.pages[0].page_id);
  }, [spec, data.focus_page]);
  const page = spec.pages.find((p) => p.page_id === pageId) || spec.pages[0];
  const visible = page.components.filter((c) => c.state !== 'omitted');
  const nar = data.narratives?.[page.page_id];
  const packed = useMemo(() => pack(visible), [page, spec]);
  const waiting = Object.values(data.results || {}).some((r) => r.status === 'pending' || r.data?.insights_pending);
  const asked = useRef('');
  useEffect(() => {
    const key = `${spec.template_id}:${data.revision}`;
    if (waiting && asked.current !== key && !pending) {
      asked.current = key;
      send('enrich', {}, 'Snowflake ML: training forecast & finding key drivers…', true);
    }
  }, [waiting, data.revision, pending]);
  // Pages are queried lazily: opening a tab whose tiles have no results yet asks for just that page.
  const loaded = page.components.some((c) => data.results?.[`${page.page_id}/${c.component_id}`]);
  const loadKey = useRef('');
  useEffect(() => {
    const key = `${page.page_id}:${data.revision}`;
    if (!loaded && !pending && page.components.length && loadKey.current !== key) {
      loadKey.current = key;
      send('load_page', { page_id: page.page_id }, 'Running governed queries…', true);
    }
  }, [page.page_id, loaded, data.revision, pending]);
  const persona = spec.persona;
  const single = !!persona && persona !== 'managers' && spec.pages.length === 1;
  // Operations: auto-refresh while the dashboard is on screen
  const [auto, setAuto] = useState(persona === 'daily_operations');
  const stamp = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const [refreshedAt, setRefreshedAt] = useState(stamp());
  useEffect(() => { setRefreshedAt(stamp()); }, [data.revision]);
  const doRefresh = () => send('refresh', { page_id: page.page_id }, 'Refreshing live data…', true);
  useEffect(() => {
    if (persona !== 'daily_operations' || !auto) return undefined;
    const t = setInterval(() => { if (!pending && document.visibilityState === 'visible') doRefresh(); }, REFRESH_MS);
    return () => clearInterval(t);
  }, [persona, auto, pending, page.page_id]);
  // Executive: the "what changed and why" summary writes itself once the page has numbers
  const narKey = useRef('');
  const ready = page.components.some((c) => data.results?.[`${page.page_id}/${c.component_id}`]?.status === 'ready');
  useEffect(() => {
    const key = `${page.page_id}:${data.revision}`;
    if (persona === 'executives' && ready && !nar && !pending && narKey.current !== key) {
      narKey.current = key;
      send('narrative', { page_id: page.page_id }, 'Cortex is writing what changed and why…', true);
    }
  }, [persona, ready, nar, pending, data.revision]);
  const panelTile = panel && spec.pages.find((p) => p.page_id === panel.page_id)?.components.find((c) => c.component_id === panel.component_id);
  const panelPage = panel && spec.pages.find((p) => p.page_id === panel.page_id);
  const origin = spec.origin || 'catalog';

  return (
    <section className={`view ws2 ${panel ? 'with-panel' : ''}`}>
      {viewer && (
        <div className="viewer-banner">
          <span>📊 Published dashboard · v{data.dashboard?.version} · by {data.dashboard?.published_by || 'owner'} · {data.dashboard?.published_at}</span>
          <span className="muted small">Read-only · live governed data</span>
        </div>
      )}
      <div className="ws-head">
        <div>
          <div className="eyebrow">
            {AUDIENCE_LABELS[spec.audience_id]} ·{' '}
            {origin === 'persona' ? <span className="origin ai">Reviewed {AUDIENCE_LABELS[spec.audience_id]?.toLowerCase()} layout · ✦ {spec.slot_origin === 'cortex' ? 'metrics chosen by Cortex' : 'default metrics'} · validated</span>
              : origin === 'cortex' ? <span className="origin ai">✦ Designed by Cortex · approved by you · validated</span>
              : origin === 'catalog-fallback' ? <span className="origin warn">Reviewed template (Cortex unavailable)</span>
                : <span className="origin">Reviewed template {spec.template_id}</span>}
            {spec.edited && !viewer && <span className="origin"> · edited</span>}
          </div>
          {viewer ? <h1 className="ws-title-v">{data.dashboard?.name || spec.display_name}</h1>
            : <input className="ws-title" value={name} onChange={(e) => setName(e.target.value)} />}
          <div className="muted">{spec.description}</div>
        </div>
        <div className="ws-actions">
          <button type="button" className="ghost" onClick={() => send('refresh', { page_id: page.page_id })}>↻ Refresh</button>
          {viewer ? (
            <button type="button" className="ghost" onClick={() => send('exit_viewer', {}, 'Opening…')}>Close</button>
          ) : (
            <>
              <button type="button" className="ghost" onClick={() => send('save_dashboard', { name }, 'Saving draft…')}>Save draft</button>
              <button type="button" className="btn" onClick={() => setPublishing(true)}>Publish{data.dashboard?.published ? ' update' : ''}</button>
            </>
          )}
        </div>
      </div>
      <PersonaStrip persona={persona} data={data} onRefresh={doRefresh} auto={auto} setAuto={setAuto} refreshedAt={refreshedAt} />
      <ViewBar data={data} send={send} pageId={page.page_id} />

      {single && !viewer && newPage == null && (
        <div className="ptab-single"><button type="button" className="ptab-add" onClick={() => setNewPage('')}>+ Add page</button></div>
      )}
      <div className={`ptabs-wrap ${single && newPage == null ? 'hidden' : ''}`}>
        <div className="ptabs" role="tablist">
          {spec.pages.map((p, i) => {
            const on = p.page_id === page.page_id;
            return (
              <div key={p.page_id} className={`ptab ${on ? 'on' : ''}`}>
                {renaming === p.page_id ? (
                  <input autoFocus defaultValue={p.label} onBlur={(e) => { setRenaming(null); if (e.target.value.trim() && e.target.value !== p.label) send('page_rename', { page_id: p.page_id, label: e.target.value }, 'Renaming…'); }}
                    onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); if (e.key === 'Escape') setRenaming(null); }} />
                ) : (
                  <button type="button" role="tab" aria-selected={on} className="ptab-btn" title={`${p.purpose || p.label} · ${p.components.length} tiles${viewer ? '' : ' · double-click to rename'}`}
                    onClick={() => setPageId(p.page_id)} onDoubleClick={() => !viewer && setRenaming(p.page_id)}>
                    <span className="ptab-num">{i + 1}</span>{p.label}
                  </button>
                )}
                {!viewer && on && renaming !== p.page_id && (
                  <span className="ptab-acts">
                    <button type="button" title="Rename page" onClick={() => setRenaming(p.page_id)}>✎</button>
                    <button type="button" title="Move left" disabled={i === 0} onClick={() => send('page_move', { page_id: p.page_id, dir: -1 }, 'Moving…')}>‹</button>
                    <button type="button" title="Move right" disabled={i === spec.pages.length - 1} onClick={() => send('page_move', { page_id: p.page_id, dir: 1 }, 'Moving…')}>›</button>
                    <button type="button" title="Remove page" disabled={spec.pages.length < 2} onClick={() => send('page_remove', { page_id: p.page_id }, 'Removing…')}>×</button>
                  </span>
                )}
              </div>
            );
          })}
          {!viewer && <button type="button" className={`ptab-add ${newPage != null ? 'on' : ''}`} onClick={() => setNewPage(newPage == null ? '' : null)}>+ Add page</button>}
        </div>
        {!viewer && newPage != null && (
          <div className="ptab-new">
            <input autoFocus placeholder="Describe the page, e.g. 'fulfilment health: on-time %, delivery days by carrier'" value={newPage}
              onChange={(e) => setNewPage(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && newPage.trim()) { send('page_add', { mode: 'cortex', instruction: newPage }, 'Cortex is designing the page…'); setNewPage(null); } if (e.key === 'Escape') setNewPage(null); }} />
            <button type="button" className="btn small ghost-ai" disabled={!newPage.trim()} onClick={() => { send('page_add', { mode: 'cortex', instruction: newPage }, 'Cortex is designing the page…'); setNewPage(null); }}>✦ Design with Cortex</button>
            <button type="button" className="ghost small" onClick={() => { send('page_add', { mode: 'blank', label: newPage || 'New page' }, 'Adding page…'); setNewPage(null); }}>Blank page</button>
            <button type="button" className="link" onClick={() => setNewPage(null)}>Cancel</button>
          </div>
        )}
      </div>

      <div className="ws-body">

        <div className="ws-main">
          <div className="page-q"><b>{page.purpose}</b></div>
          <div className="summary">
            <div className="summary-head">
              <span className="ai-title">✦ {persona === 'executives' ? 'What changed and why' : persona === 'daily_operations' ? 'What is happening today' : 'AI summary'}</span>
              <button type="button" className="btn small ghost-ai" onClick={() => send('narrative', { page_id: page.page_id })}>{nar ? 'Regenerate' : 'Generate with Cortex'}</button>
            </div>
            {nar ? (
              <>
                <div className="summary-text">{nar.text}</div>
                <details><summary className="prov">{nar.provenance} — show the governed facts it used</summary>
                  <ul className="facts">{(nar.facts || []).map((f, i) => <li key={i}>{f}</li>)}</ul></details>
              </>
            ) : <div className="muted small">Cortex writes the summary only from the governed facts computed for this page.</div>}
          </div>
          {!visible.length && <div className="empty">This page is empty. {!viewer && 'Add a tile below.'}</div>}
          <div className="grid">
            {packed.map((c) => {
              const res = data.results[`${page.page_id}/${c.component_id}`] || {};
              const R = REGISTRY[c.type];
              const def = ctx.defs?.[c.metric_id];
              const open = panel?.component_id === c.component_id && panel?.page_id === page.page_id;
              return (
                <div className={`tile ${open ? 'focused' : ''}`} style={{ gridColumn: `span ${c.span}` }} key={c.component_id}>
                  <div className="tile-head">
                    <b title={c.question || ''}>{c.title}{def ? <span className="def" title={def}>ⓘ</span> : null}</b>
                    <span className="tile-acts">
                      {c.type === 'kpi_plan' && !viewer ? (
                        <span className="show-as" role="group" aria-label="Show KPIs as">
                          {[['bullet', 'Bars'], ['variance', 'Arrows'], ['table', 'Table']].map(([v, l]) => (
                            <button type="button" key={v} className={(c.display || 'bullet') === v ? 'on' : ''}
                              title={KPI_DISPLAYS.find((d) => d[0] === v)?.[1]}
                              onClick={() => (c.display || 'bullet') !== v && send('tile_update', { page_id: page.page_id, component_id: c.component_id, patch: { display: v } }, 'Switching view…')}>{l}</button>
                          ))}
                        </span>
                      ) : <span className="muted small">{data.tile_types?.[c.type]?.label || c.type.replace(/_/g, ' ')}</span>}
                      <button type="button" className={`sparkle ${open ? 'on' : ''}`} title="Ask or change this tile with AI"
                        onClick={() => setPanel(open ? null : { page_id: page.page_id, component_id: c.component_id })}>✦</button>
                      {!viewer && <button type="button" className="dots" title="Tile options" onClick={() => setMenu(menu === c.component_id ? null : c.component_id)}>⋯</button>}
                    </span>
                    {menu === c.component_id && <TileMenu c={c} page={page} data={data} send={send} onClose={() => setMenu(null)} />}
                  </div>
                  {c.question && <div className="tile-q">{c.question}</div>}
                  {!res.status && <div className="tile-skel"><i /><i /><i /></div>}
                  {res.status === 'ready' && R && <R data={res.data} ctx={ctx} spec={c} />}
                  {res.status === 'error' && <div className="alert error small">Query failed — no substitute value shown. {res.error}</div>}
                  {res.status === 'pending' && <div className="pending-tile"><div className="spinner dark" />{res.message || 'Running Snowflake ML…'}</div>}
                  {res.status === 'blocked' && <div className="alert warn small">Unavailable. Missing: {(res.missing || []).map((x) => CAP_LABELS[x] || label(x)).join(', ')}</div>}
                  {res.skipped_filters?.length > 0 && <div className="skipnote">Filter not applied: {res.skipped_filters.join(', ')} can't split this metric in the semantic view.</div>}
                </div>
              );
            })}
            {!viewer && (
              <div className="tile add" style={{ gridColumn: 'span 12' }}>
                {adding ? <AddTile page={page} data={data} send={send} onClose={() => setAdding(false)} />
                  : <button type="button" className="add-btn" onClick={() => setAdding(true)}>+ Add tile</button>}
              </div>
            )}
          </div>
        </div>

        {panelTile && (
          <TilePanel tile={panelTile} page={panelPage} data={data} send={send} pending={pending} viewer={viewer} onClose={() => setPanel(null)} />
        )}
      </div>
      {publishing && <PublishDialog data={data} send={send} name={name} onClose={() => setPublishing(false)} />}
    </section>
  );
}
