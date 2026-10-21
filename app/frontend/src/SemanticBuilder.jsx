import React, { useEffect, useState } from 'react';

const AGGS = ['SUM', 'AVG', 'MIN', 'MAX', 'COUNT', 'COUNT_DISTINCT'];

/** B1: raw table -> Cortex-drafted semantic view -> human review -> CREATE SEMANTIC VIEW. */
export default function SemanticBuilder({ data, send, pending, onDone }) {
  const sbs = data.sb;
  const [q, setQ] = useState('');
  const [spec, setSpec] = useState(null);
  useEffect(() => { if (!sbs) send('sb_tables', {}, 'Listing tables you can read…', true); }, []);
  useEffect(() => { setSpec(sbs?.spec ? JSON.parse(JSON.stringify(sbs.spec)) : null); }, [sbs?.spec]);
  const busy = pending && String(pending.type).startsWith('sb_');

  if (!sbs) return <div className="muted">Listing tables…</div>;

  if (sbs.step === 'pick') {
    const needle = q.trim().toLowerCase();
    const list = (sbs.tables || []).filter((t) => !needle || `${t.schema} ${t.name}`.toLowerCase().includes(needle));
    return (
      <div className="sb">
        <p className="muted small">Pick a table or view. Cortex profiles its columns and drafts a governed semantic view
          (dimensions, metrics, synonyms, definitions). You review every line before anything is created.</p>
        <input className="search" placeholder="Search tables…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="sb-list">
          {list.map((t) => (
            <button type="button" key={t.fqn} className="sb-row" disabled={busy}
              onClick={() => send('sb_draft', { fqn: t.fqn }, 'Profiling the table and drafting with Cortex…')}>
              <b>{t.name}</b><span className="muted small">{t.schema} · {t.type === 'VIEW' ? 'view' : 'table'}{t.rows != null ? ` · ${Number(t.rows).toLocaleString()} rows` : ''}</span>
              <span className="sb-go">Draft with Cortex →</span>
            </button>
          ))}
          {!list.length && <div className="empty">No tables match.</div>}
        </div>
      </div>
    );
  }

  if (sbs.step === 'done') {
    const rows = sbs.created?.test_rows || [];
    const cols = rows.length ? Object.keys(rows[0]) : [];
    return (
      <div className="sb">
        <div className="sb-done">✓ Created <code>{sbs.created?.semantic_view}</code> and queried it through <code>SEMANTIC_VIEW()</code>.</div>
        {rows.length > 0 && (
          <table className="table compact"><thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>{rows.map((r, i) => <tr key={i}>{cols.map((c) => <td key={c}>{String(r[c] ?? '')}</td>)}</tr>)}</tbody></table>
        )}
        <p className="muted small">It now appears on Home: Cortex ideas, prompt routing and the agent can all use it.</p>
        <div className="sb-actions">
          <button type="button" className="btn" onClick={() => { onDone && onDone(); send('go', { step: 'home' }, 'Opening Home…'); }}>Back to Home</button>
          <button type="button" className="ghost" onClick={() => send('sb_tables', {}, 'Listing tables…')}>Draft another</button>
        </div>
      </div>
    );
  }

  if (!spec) return null;
  const upd = (kind, i, patch) => setSpec((s) => ({ ...s, [kind]: s[kind].map((x, j) => (j === i ? { ...x, ...patch } : x)) }));
  const counts = ['dimensions', 'metrics', 'ratios'].map((k) => (spec[k] || []).filter((x) => x.include !== false).length);
  return (
    <div className="sb">
      <div className="sb-head">
        <div><b>{sbs.profile?.table}</b> <span className="muted small">{sbs.fqn} · {Number(sbs.profile?.rows_profiled || 0).toLocaleString()} rows profiled</span></div>
        <span className={`pill ${sbs.origin === 'cortex' ? 'ai' : 'soft'}`}>{sbs.origin === 'cortex' ? '✦ Drafted by Cortex' : 'Drafted from profile (Cortex unavailable)'}</span>
      </div>
      <label className="sb-field">View description
        <input value={spec.description || ''} onChange={(e) => setSpec({ ...spec, description: e.target.value })} /></label>

      <h4>Dimensions <span className="count">{counts[0]}</span></h4>
      <table className="table compact sb-table"><thead><tr><th /><th>Name</th><th>Column</th><th>Definition</th></tr></thead>
        <tbody>{spec.dimensions.map((d, i) => (
          <tr key={`d${i}`} className={d.include === false ? 'off' : ''}>
            <td><input type="checkbox" checked={d.include !== false} onChange={(e) => upd('dimensions', i, { include: e.target.checked })} /></td>
            <td><input value={d.name} onChange={(e) => upd('dimensions', i, { name: e.target.value })} />{d.column === spec.time_dimension && <em className="tdim">time</em>}</td>
            <td className="muted small">{d.column}</td>
            <td><input value={d.comment} onChange={(e) => upd('dimensions', i, { comment: e.target.value })} /></td>
          </tr>))}</tbody></table>

      <h4>Metrics <span className="count">{counts[1] + counts[2]}</span></h4>
      <table className="table compact sb-table"><thead><tr><th /><th>Name</th><th>Aggregation</th><th>Column</th><th>Definition</th></tr></thead>
        <tbody>
          {spec.metrics.map((m, i) => (
            <tr key={`m${i}`} className={m.include === false ? 'off' : ''}>
              <td><input type="checkbox" checked={m.include !== false} onChange={(e) => upd('metrics', i, { include: e.target.checked })} /></td>
              <td><input value={m.name} onChange={(e) => upd('metrics', i, { name: e.target.value })} /></td>
              <td><select value={m.agg} onChange={(e) => upd('metrics', i, { agg: e.target.value })}>{AGGS.map((a) => <option key={a}>{a}</option>)}</select></td>
              <td className="muted small">{m.column || 'rows'}</td>
              <td><input value={m.comment} onChange={(e) => upd('metrics', i, { comment: e.target.value })} /></td>
            </tr>))}
          {(spec.ratios || []).map((r, i) => (
            <tr key={`r${i}`} className={r.include === false ? 'off' : ''}>
              <td><input type="checkbox" checked={r.include !== false} onChange={(e) => upd('ratios', i, { include: e.target.checked })} /></td>
              <td><input value={r.name} onChange={(e) => upd('ratios', i, { name: e.target.value })} /></td>
              <td className="small">ratio</td>
              <td className="muted small">{r.numerator} ÷ {r.denominator}</td>
              <td><input value={r.comment} onChange={(e) => upd('ratios', i, { comment: e.target.value })} /></td>
            </tr>))}
        </tbody></table>

      {sbs.notes?.length > 0 && (
        <details open><summary className="prov">Validator: {sbs.notes.length} change{sbs.notes.length > 1 ? 's' : ''} to Cortex's draft</summary>
          <ul className="small sb-notes">{sbs.notes.map((n, i) => <li key={i}><span className={`tag ${n.action === 'dropped' ? 'no' : 'warn'}`}>{n.action}</span> {n.item}: {n.why}</li>)}</ul></details>
      )}
      {spec.questions?.length > 0 && (
        <details><summary className="prov">Questions this view should answer</summary>
          <ul className="small">{spec.questions.map((x, i) => <li key={i}>{x}</li>)}</ul></details>
      )}
      <details><summary className="prov">SQL that will run (source view + CREATE SEMANTIC VIEW)</summary>
        <pre className="sql-log">{sbs.ddl?.view_sql}{'\n\n'}{sbs.ddl?.sv_sql}</pre></details>

      <div className="sb-actions">
        <button type="button" className="ghost" disabled={busy} onClick={() => send('sb_tables', {}, 'Listing tables…')}>← Other table</button>
        <button type="button" className="ghost" disabled={busy} onClick={() => send('sb_preview', { spec }, 'Re-validating…')}>Re-check</button>
        <button type="button" className="btn" disabled={busy || !counts[1]} onClick={() => send('sb_create', { spec }, 'Creating the semantic view in Snowflake…')}>
          Create semantic view</button>
      </div>
    </div>
  );
}
