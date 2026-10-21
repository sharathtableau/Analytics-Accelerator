import React, { useEffect, useMemo, useState } from 'react';
import { pack } from './registry.jsx';

const THEMES = ['Sales', 'Profitability', 'Customers', 'Fulfilment', 'Returns', 'Inventory', 'Plan'];

/** Small chart glyphs so the outline reads as a layout, not a list. */
function Glyph({ type }) {
  const p = { width: 22, height: 16, viewBox: '0 0 22 16', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round' };
  switch (type) {
    case 'kpi_grid': case 'kpi_card': case 'kpi_plan': case 'status_tiles':
      return <svg {...p}><rect x="1" y="3" width="5.5" height="10" rx="1.5" /><rect x="8.25" y="3" width="5.5" height="10" rx="1.5" /><rect x="15.5" y="3" width="5.5" height="10" rx="1.5" /></svg>;
    case 'trend_chart': case 'small_multiples': case 'pace_chart':
      return <svg {...p}><path d="M1 12l5-5 4 3 5-6 6 4" /></svg>;
    case 'forecast_band': case 'ytd_trajectory':
      return <svg {...p}><path d="M1 12l5-5 4 3 4-4" /><path d="M14 6l7-2" strokeDasharray="2 2" /></svg>;
    case 'share_donut':
      return <svg {...p}><circle cx="11" cy="8" r="6" /><circle cx="11" cy="8" r="2.5" /></svg>;
    case 'scatter':
      return <svg {...p}><circle cx="4" cy="11" r="1.4" /><circle cx="9" cy="7" r="1.4" /><circle cx="14" cy="9" r="1.4" /><circle cx="18" cy="4" r="1.4" /></svg>;
    case 'heatmap': case 'segment_matrix': case 'hour_heatmap': case 'scorecard':
      return <svg {...p}><rect x="2" y="2" width="5" height="5" /><rect x="8.5" y="2" width="5" height="5" /><rect x="15" y="2" width="5" height="5" /><rect x="2" y="9" width="5" height="5" /><rect x="8.5" y="9" width="5" height="5" /><rect x="15" y="9" width="5" height="5" /></svg>;
    case 'detail_table': case 'evidence_table': case 'action_table':
      return <svg {...p}><path d="M2 3h18M2 8h18M2 13h18" /></svg>;
    case 'driver_bridge':
      return <svg {...p}><path d="M2 14V6M7 6V3M12 3v5M17 8v6" /></svg>;
    case 'exception_table': case 'worklist':
      return <svg {...p}><path d="M11 2l9 12H2z" /><path d="M11 7v3" /></svg>;
    default:
      return <svg {...p}><path d="M2 14h4V6H2zM9 14h4V2H9zM16 14h4V9h-4z" /></svg>;
  }
}

function tileMetrics(c) { return [c.metric_id, c.metric2_id, ...(c.metrics || [])].filter(Boolean); }

/** Metric picker: compact rows, business language first, formula only on demand. */
function MetricPicker({ cards, selected, onToggle, onClose }) {
  const [theme, setTheme] = useState('All');
  const [q, setQ] = useState('');
  const needle = q.trim().toLowerCase();
  const list = cards.filter((c) => (theme === 'All' || c.theme === theme)
    && (!needle || `${c.label} ${c.definition}`.toLowerCase().includes(needle)));
  const themes = ['All', ...THEMES.filter((t) => cards.some((c) => c.theme === t))];
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal picker" onClick={(e) => e.stopPropagation()}>
        <div className="picker-head">
          <div><h3>Add or remove metrics</h3><span className="muted small">{cards.length} {cards.some((c) => c.origin === 'cortex' || c.origin === 'adhoc') ? 'metrics drafted from the facts of' : 'governed metrics in'} this semantic view · {selected.size} on the dashboard</span></div>
          <button type="button" className="x" onClick={onClose}>×</button>
        </div>
        <div className="picker-tools">
          <input autoFocus className="search" placeholder="Search metrics, e.g. shipping, stock, margin" value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="idea-tabs">
            {themes.map((t) => <button type="button" key={t} className={`seg ${theme === t ? 'on' : ''}`} onClick={() => setTheme(t)}>{t}</button>)}
          </div>
        </div>
        <div className="picker-list">
          {list.map((c) => (
            <label key={c.id} className={`prow ${selected.has(c.id) ? 'on' : ''}`}>
              <input type="checkbox" checked={selected.has(c.id)} onChange={() => onToggle(c.id)} />
              <span className="prow-main">
                <b>{c.label}{c.recommended && <em className="rec-dot" title="Recommended by Cortex">✦</em>}</b>
                {c.definition && <span>{c.definition}</span>}
                {c.why && <span className="prow-why">✦ {c.why}</span>}
              </span>
              <span className="prow-theme">{c.theme}</span>
              {c.formula && <span className="prow-f" title={c.formula}>ƒ</span>}
            </label>
          ))}
          {!list.length && <div className="empty">No metric matches "{q}".</div>}
        </div>
        <div className="modal-foot"><button type="button" className="btn" onClick={onClose}>Done</button></div>
      </div>
    </div>
  );
}

/** Facts-only semantic view: the metrics were drafted from a data profile; say so and let the user act on it. */
export function DraftBanner({ md, send }) {
  const byCortex = md.origin === 'cortex';
  return (
    <section className="rv2-block draft-banner">
      <div className="db-head">
        <div>
          <b>{md.view?.split('.').pop()}{md.table ? ` · ${md.table}` : ''} defines no metrics, so {byCortex ? 'Cortex' : 'the app'} drafted {md.count} from its {md.facts} facts.</b>
          <div className="muted small">{byCortex
            ? `Snowflake profiled ${md.profiled_facts || 0} facts (counts, distinct values, ranges) through the semantic view; Cortex chose an aggregation for each fact, added ratios and wrote definitions; the validator checked every one. Hover a metric for why.`
            : 'Cortex was unavailable, so rules chose the aggregations from the data profile. Try re-drafting with Cortex.'}
            {md.saved_at ? ` Saved ${md.saved_at}${md.saved_by ? ` by ${md.saved_by}` : ''}, shared by everyone using this view.` : ''}</div>
        </div>
        <button type="button" className="btn small ghost-ai" onClick={() => send('metrics_redraft', {}, 'Profiling the facts and drafting metrics with Cortex…')}>✦ Re-draft with Cortex</button>
      </div>
      {md.notes?.length > 0 && (
        <details><summary className="prov">Validator: {md.notes.length} change{md.notes.length > 1 ? 's' : ''} to the draft</summary>
          <ul className="small sb-notes">{md.notes.map((n, i) => <li key={i}><span className={`tag ${n.action === 'dropped' ? 'no' : 'warn'}`}>{n.action}</span> {n.item}: {n.why}</li>)}</ul></details>
      )}
      <details><summary className="prov">Make them governed: METRICS clause for the view owner</summary>
        <p className="muted small">The app queries these as ad-hoc metrics. To make them part of the semantic view, the owner adds this clause to its definition (CREATE OR REPLACE SEMANTIC VIEW … ).</p>
        <pre className="sql-log">{md.ddl}</pre></details>
    </section>
  );
}

/** Between the prompt and the dashboard: Cortex proposes, the user approves. */
export default function Review({ data, send }) {
  const draft = data.draft;
  const spec = draft.spec;
  const cards = draft.cards || [];
  const byId = useMemo(() => Object.fromEntries(cards.map((c) => [c.id, c])), [draft]);
  // after a redesign the draft carries the user's own selection; otherwise start from Cortex's recommendation
  const init = () => new Set(draft.selected?.length ? draft.selected : cards.filter((c) => c.recommended).map((c) => c.id));
  const initOutline = () => spec.pages.map((p) => ({ page_id: p.page_id, label: p.label, purpose: p.purpose, tiles: p.components.map((c) => c.component_id) }));
  const [selected, setSelected] = useState(init);
  const [outline, setOutline] = useState(initOutline);
  const [picking, setPicking] = useState(false);
  useEffect(() => { setSelected(init()); setOutline(initOutline()); }, [draft]);

  const comps = useMemo(() => Object.fromEntries(spec.pages.flatMap((p) => p.components.map((c) => [`${p.page_id}/${c.component_id}`, c]))), [draft]);
  const toggle = (id) => setSelected((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const survives = (c) => (c.metrics && c.metrics.length ? c.metrics.some((m) => selected.has(m)) : tileMetrics(c).every((m) => selected.has(m)));
  const livePages = outline.map((p) => ({ ...p, comps: p.tiles.map((t) => comps[`${p.page_id}/${t}`]).filter(Boolean) }));
  const tileCount = livePages.reduce((n, p) => n + p.comps.filter(survives).length, 0);
  const usedIds = new Set(Object.values(comps).flatMap(tileMetrics));
  const added = [...selected].filter((m) => !usedIds.has(m));
  const chosen = [...selected].map((id) => byId[id]).filter(Boolean)
    .sort((a, b) => THEMES.indexOf(a.theme) - THEMES.indexOf(b.theme));
  const removeTile = (pi, tid) => setOutline((o) => o.map((p, i) => (i !== pi ? p : { ...p, tiles: p.tiles.filter((t) => t !== tid) })));
  const label = (id) => byId[id]?.label || (id || '').split('.').pop().replace(/_/g, ' ').toLowerCase();

  return (
    <section className="view review2">
      <header className="rv2-head">
        <div>
          <div className="eyebrow">Step 2 of 3 · Review the draft</div>
          <h1>{spec.display_name}</h1>
          <p className="muted">{spec.description}</p>
        </div>
        <div className="rv2-meta">
          <span className="pill ai">{spec.origin === 'persona' ? `Reviewed layout · ✦ ${spec.slot_origin === 'cortex' ? 'metrics chosen by Cortex' : 'default metrics'}` : '✦ Drafted by Cortex'}</span>
        </div>
      </header>

      {data.metric_draft && <DraftBanner md={data.metric_draft} send={send} />}
      <section className="rv2-block">
        <div className="rv2-title">
          <h3>Metrics <span className="count">{selected.size}</span></h3>
          <button type="button" className="link" onClick={() => setPicking(true)}>+ Add or remove metrics</button>
        </div>
        <div className="mchips">
          {chosen.map((c) => (
            <span key={c.id} className="mchip" title={c.definition || ''}>
              {c.recommended && <em className="rec-dot" title="Recommended by Cortex">✦</em>}{c.label}
              {c.origin === 'cortex' && <em className="draft-tag" title={c.why || 'Drafted by Cortex from the facts'}>drafted</em>}
              <button type="button" aria-label={`Remove ${c.label}`} onClick={() => toggle(c.id)}>×</button>
            </span>
          ))}
          {!chosen.length && <span className="muted small">No metrics selected — add at least one.</span>}
        </div>
        {added.length > 0 && <div className="rv2-note">New metrics ({added.map(label).join(', ')}) will appear as headline cards on page 1.</div>}
      </section>

      <section className="rv2-block">
        <div className="rv2-title">
          <h3>Layout preview <span className="count">{outline.length} pages · {tileCount} tiles</span></h3>
          <span className="muted small">Hover a tile to see what it shows · × removes it · rename pages inline</span>
        </div>
        <div className="wf-pages">
          {livePages.map((p, pi) => (
            <div className="wf-page" key={p.page_id}>
              <div className="wf-page-head">
                <span className="ol-num">{pi + 1}</span>
                <input value={p.label} onChange={(e) => setOutline((o) => o.map((x, i) => (i === pi ? { ...x, label: e.target.value } : x)))} />
                <span className="wf-acts">
                  <button type="button" title="Move left" disabled={pi === 0} onClick={() => setOutline((o) => { const n = [...o]; [n[pi - 1], n[pi]] = [n[pi], n[pi - 1]]; return n; })}>‹</button>
                  <button type="button" title="Move right" disabled={pi === outline.length - 1} onClick={() => setOutline((o) => { const n = [...o]; [n[pi + 1], n[pi]] = [n[pi], n[pi + 1]]; return n; })}>›</button>
                  <button type="button" title="Remove page" disabled={outline.length < 2} onClick={() => setOutline((o) => o.filter((_, i) => i !== pi))}>×</button>
                </span>
              </div>
              <div className="wf-q">{p.purpose}</div>
              <div className="wf-grid">
                {pack(p.comps).map((c) => {
                  const ok = survives(c);
                  const ms = tileMetrics(c).map(label);
                  const dim = c.dimension ? c.dimension.split('.').pop().replace(/_/g, ' ').toLowerCase() : '';
                  return (
                    <div key={c.component_id} className={`wf-tile ${ok ? '' : 'gone'} ${c.type === 'kpi_grid' ? 'kpi' : ''}`}
                      style={{ gridColumn: `span ${c.span}` }}
                      title={`${c.title}\n${data.tile_types?.[c.type]?.label || c.type}: ${ms.join(', ')}${dim ? ` by ${dim}` : ''}${ok ? '' : '\nWill be removed: its metric is not selected'}`}>
                      <span className="wf-glyph"><Glyph type={c.type} /></span>
                      <span className="wf-name">{c.title}</span>
                      <button type="button" className="wf-x" aria-label="Remove tile" onClick={() => removeTile(pi, c.component_id)}>×</button>
                    </div>
                  );
                })}
                {!p.comps.length && <div className="wf-empty">Empty page</div>}
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="review-bar">
        <button type="button" className="ghost" onClick={() => send('go', { step: 'home' }, 'Opening…')}>← Back</button>
        <span className="muted small">{selected.size} metrics · {outline.length} pages · {tileCount} tiles</span>
        <span className="review-actions">
          <button type="button" className="btn ghost-ai" onClick={() => send('redraft', { metrics: [...selected], added }, 'Cortex is redesigning around your metrics…')}>✦ Redesign</button>
          <button type="button" className="btn" disabled={!tileCount && !added.length}
            onClick={() => send('build_draft', { metrics: [...selected], outline: outline.map((p) => ({ page_id: p.page_id, label: p.label, tiles: p.tiles })) }, 'Running governed queries…')}>
            Build dashboard →
          </button>
        </span>
      </div>
      {picking && <MetricPicker cards={cards} selected={selected} onToggle={toggle} onClose={() => setPicking(false)} />}
    </section>
  );
}
