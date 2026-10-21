import React, { useEffect, useMemo, useRef, useState } from 'react';
import { pack } from './registry.jsx';
import Home from './Home.jsx';
import Review, { DraftBanner } from './Review.jsx';
import Workspace from './Workspace.jsx';
import SemanticBuilder from './SemanticBuilder.jsx';
import { AUDIENCE_LABELS, CAP_LABELS, label } from './format.js';

const STEPS = [
  { id: 'home', label: 'Home', hint: 'Ask Cortex to build' },
  { id: 'review', label: 'Review', hint: 'Metrics & outline' },
  { id: 'workspace', label: 'Dashboard', hint: 'Build & publish' },
];
const ADVANCED = [
  { id: 'source', label: 'Data sources' },
  { id: 'metrics', label: 'Field mapping' },
  { id: 'layout', label: 'Layout templates' },
];

let seq = 0;
const newId = () => `${Date.now().toString(36)}-${(seq += 1)}`;

export default function App({ data, emit }) {
  const [pending, setPending] = useState(null);
  const [drawer, setDrawer] = useState(null);           // agent | decisions | governance
  const [decisionDraft, setDecisionDraft] = useState(null);
  const lastRev = useRef(data.revision);

  useEffect(() => {
    if (data.revision !== lastRev.current) { lastRev.current = data.revision; setPending(null); }
  }, [data.revision]);

  const send = (type, payload = {}, label2, quiet = false) => {
    const id = newId();
    setPending({ id, type, quiet, label: label2 || busyLabel(type) });
    emit({ id, type, payload });
  };
  const defs = useMemo(() => Object.fromEntries((data.model?.metrics || []).map((m) => [m.id, m.comment || ''])), [data.model]);
  const ctx = {
    defs,
    send,
    ask: (question) => { setDrawer('agent'); send('ask', { question }, 'Cortex Agent is answering…'); },
    decide: (prefill) => setDecisionDraft({ title: '', detail: '', owner: '', due: '', ...prefill }),
    openDecisions: () => setDrawer('decisions'),
    drill: (dim, value) => send('set_view', { filters: { ...(data.view?.filters || {}), [dim]: [value] } },
      `Drilling into ${value}…`),
  };
  const step = data.step;
  const reachable = { home: true, review: !!data.draft, source: true, metrics: !!data.source, layout: !!data.profile, workspace: !!data.spec };

  return (
    <div className="aa">
      <aside className="rail">
        <div className="brand"><span className="flake">❄</span><div><b>Analytics Accelerator</b><small>Enterprise · Snowflake-native</small></div></div>
        {data.viewer_mode ? (
          <nav className="steps">
            <button type="button" className="step done" onClick={() => send('exit_viewer', {}, 'Opening…')}>
              <span className="num">←</span><span><b>Home</b><small>Published dashboards</small></span>
            </button>
          </nav>
        ) : (
          <>
            <nav className="steps">
              {STEPS.map((s, i) => (
                <button type="button" key={s.id} disabled={!reachable[s.id]}
                  className={`step ${step === s.id ? 'on' : ''} ${reachable[s.id] ? 'done' : ''}`}
                  onClick={() => send('go', { step: s.id }, 'Opening…')}>
                  <span className="num">{i + 1}</span><span><b>{s.label}</b><small>{s.hint}</small></span>
                </button>
              ))}
            </nav>
            <details className="advanced" open={['source', 'metrics', 'layout'].includes(step)}>
              <summary>Advanced setup</summary>
              {ADVANCED.map((s) => (
                <button type="button" key={s.id} disabled={!reachable[s.id]} className={`adv ${step === s.id ? 'on' : ''}`}
                  onClick={() => send('go', { step: s.id }, 'Opening…')}>{s.label}</button>
              ))}
            </details>
          </>
        )}
        <FeaturePanel features={data.features} />
        <div className="rail-foot">
          <button type="button" className="ghost" onClick={() => { setDrawer('governance'); send('quality', {}, 'Loading AI ledger…'); }}>
            🛡 Governance &amp; AI quality
          </button>
        </div>
      </aside>

      <main className="main">
        {step !== 'home' && <TopBar data={data} onDrawer={setDrawer} send={send} />}
        {data.error && <div className="alert error">⚠ {data.error}</div>}
        {data.notice && <div className="alert ok">✓ {data.notice}</div>}
        {step === 'home' && <Home data={data} send={send} pending={pending} onBuilder={() => setDrawer('builder')} />}
        {step === 'source' && <SourceView data={data} send={send} />}
        {step === 'metrics' && data.model && <MetricsView data={data} send={send} />}
        {step === 'layout' && <LayoutView data={data} send={send} />}
        {step === 'review' && data.draft && <Review data={data} send={send} />}
        {step === 'workspace' && data.spec && <Workspace data={data} send={send} ctx={ctx} pending={pending} />}
      </main>

      {drawer && (
        <Drawer title={{ agent: 'Cortex Agent', decisions: 'Decisions', governance: 'Governance & AI quality', builder: 'Connect a table · semantic view drafted by Cortex' }[drawer]}
          wide={drawer === 'builder'} onClose={() => setDrawer(null)}>
          {data.error && drawer !== 'governance' && <div className="alert error small drawer-err">{data.error}</div>}
          {drawer === 'agent' && <AgentPanel data={data} send={send} ctx={ctx} pending={pending} />}
          {drawer === 'decisions' && <DecisionList data={data} send={send} ctx={ctx} />}
          {drawer === 'builder' && <SemanticBuilder data={data} send={send} pending={pending} onDone={() => setDrawer(null)} />}
          {drawer === 'governance' && <Governance data={data} send={send} />}
        </Drawer>
      )}
      {decisionDraft && (
        <DecisionDialog draft={decisionDraft} onCancel={() => setDecisionDraft(null)}
          onSave={(d) => { setDecisionDraft(null); send('add_decision', d, 'Logging decision in Snowflake…'); }} />
      )}
      {pending && !pending.quiet && <div className="busy"><div className="spinner" /><span>{pending.label}</span></div>}
    </div>
  );
}

function busyLabel(type) {
  return {
    select_source: 'Reading semantic view & finding Cortex Agents…', suggest_bindings: 'Cortex is mapping fields…',
    set_bindings: 'Profiling the source…', set_audience: 'Checking layout readiness…',
    recommend_layout: 'Cortex is recommending a layout…', compose_layout: 'Cortex is designing your dashboard from the data profile…',
    tile_add: 'Cortex is designing the tile…', build_draft: 'Running governed queries…', set_view: 'Re-running governed queries…',
    publish: 'Publishing…', open_published: 'Opening published dashboard…', page_add: 'Adding page…', page_regenerate: 'Cortex is redesigning the page…', tile_update: 'Validating & re-querying…', select_layout: 'Running governed queries & Snowflake ML…',
    narrative: 'Cortex is summarising governed facts…', create_agent: 'Creating a Cortex Agent…',
    save_dashboard: 'Saving to Snowflake…', open_dashboard: 'Opening saved dashboard…', refresh: 'Refreshing…',
  }[type] || 'Working…';
}

function FeaturePanel({ features }) {
  if (!features) return null;
  const items = [
    ['Cortex AI_COMPLETE', features.complete, features.model],
    ['Snowflake ML Forecast', features.forecast],
    ['ML Top Insights', features.top_insights],
    ['Cortex Agents', features.agents],
  ];
  return (
    <div className="features">
      <div className="features-title">Snowflake AI in this account</div>
      {items.map(([n, ok, extra]) => (
        <div key={n} className={`feat ${ok ? 'ok' : 'off'}`}><i />{n}{extra ? <small>{extra}</small> : null}</div>
      ))}
    </div>
  );
}

function TopBar({ data, onDrawer }) {
  const cal = data.profile?.calendar;
  return (
    <header className="top">
      <div className="crumbs">
        {data.source ? <span className="pill" title={data.source.fqn}>{label(data.source.name)}</span> : <span className="muted">No data selected</span>}
        {data.step !== 'source' && data.audience && <span className="pill soft">{AUDIENCE_LABELS[data.audience]}</span>}
        {cal && <span className="pill soft">as of {cal.max_date} · {cal.grain}</span>}
        {data.profile?.current_role && <span className="pill soft">role {data.profile.current_role}</span>}
      </div>
      <div className="top-actions">
        {data.source && <button type="button" className="ghost" onClick={() => onDrawer('decisions')}>☑ Decisions <b>{data.decisions?.length || 0}</b></button>}
        {data.source && <button type="button" className="btn" onClick={() => onDrawer('agent')}>✦ Ask Cortex Agent</button>}
      </div>
    </header>
  );
}

/* ---------------------------------------------------------------- 1. Source */
function SourceView({ data, send }) {
  const [q, setQ] = useState('');
  const all = (data.sources || []).filter((s) => s.fqn);
  const needle = q.trim().toLowerCase();
  const sources = all.filter((s) => !needle || `${s.fqn} ${s.comment}`.toLowerCase().includes(needle));
  const err = (data.sources || []).find((s) => s.error);
  return (
    <section className="view">
      <div className="hero">
        <div>
          <div className="eyebrow">Step 1 · Governed source</div>
          <h1>Start from a Snowflake semantic view</h1>
          <p>Every number in this app is queried through <code>SEMANTIC_VIEW()</code> under your role. Cortex and Snowflake ML
            add recommendations, forecasts, drivers and narrative — never ungoverned numbers.</p>
        </div>
      </div>
      {data.dashboards?.length > 0 && (
        <>
          <h3>Saved dashboards</h3>
          <div className="cards">
            {data.dashboards.map((d) => (
              <button type="button" className="card link-card" key={d.dashboard_id} onClick={() => send('open_dashboard', { dashboard_id: d.dashboard_id })}>
                <b>{d.name}</b><small>{AUDIENCE_LABELS[d.audience]} · v{d.version} · {d.semantic_view}</small>
                <small className="muted">{d.created_by} · {d.created_at}</small>
              </button>
            ))}
          </div>
        </>
      )}
      <div className="source-head">
        <h3>Semantic views you can use <span className="muted">({sources.length}{needle ? ` of ${all.length}` : ''})</span></h3>
        <input className="search" placeholder="Search semantic views, e.g. superstore" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {err && <div className="alert error">{err.error}</div>}
      {!sources.length && !err && <div className="empty">No semantic views visible to this role in the allowlisted schemas.</div>}
      <div className="cards">
        {sources.map((s) => (
          <button type="button" className={`card link-card ${data.source?.fqn === s.fqn ? 'sel' : ''}`} key={s.fqn}
            onClick={() => send('select_source', { fqn: s.fqn })}>
            <b>{label(s.name)}</b><small className="mono">{s.fqn}</small>
            <small className="muted">{s.comment || 'No description'}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- 2. Metrics */
function MetricsView({ data, send }) {
  const m = data.model;
  const [b, setB] = useState(data.bindings);
  const [intent, setIntent] = useState('');
  useEffect(() => setB(data.bindings), [data.bindings]);
  const metrics = m.metrics, times = m.dimensions.filter((d) => d.is_time), cats = m.dimensions.filter((d) => !d.is_time);
  const sug = data.binding_suggestion;
  const upd = (k, v) => setB({ ...b, [k]: v });
  const toggleSupport = (id) => upd('supporting_metrics', b.supporting_metrics.includes(id)
    ? b.supporting_metrics.filter((x) => x !== id) : [...b.supporting_metrics, id]);
  const others = metrics.filter((x) => x.id !== b.primary_metric).map((x) => x.id);
  return (
    <section className="view">
      <div className="eyebrow">Step 2 · Governed fields</div>
      <h1>Map semantic-view fields to dashboard roles</h1>
      <p className="lede">Roles drive which saved layouts are available. The app proposes a mapping; Cortex can refine it; you approve it.</p>
      {data.metric_draft && <DraftBanner md={data.metric_draft} send={send} />}
      <div className="two">
        <div className="panel">
          <Select label="Primary metric (headline outcome)" value={b.primary_metric} onChange={(v) => upd('primary_metric', v)}
            options={metrics.map((x) => [x.id, `${x.label}${x.additive ? '' : ' · non-additive'}`])} />
          <div className="field">
            <label>Supporting metrics ({b.supporting_metrics.length} selected) ·{' '}
              <button type="button" className="link" onClick={() => upd('supporting_metrics', others)}>select all</button>
              <button type="button" className="link" onClick={() => upd('supporting_metrics', [])}>clear</button>
            </label>
            <div className="chips">
              {metrics.filter((x) => x.id !== b.primary_metric).map((x) => (
                <button type="button" key={x.id} className={`chip ${b.supporting_metrics.includes(x.id) ? 'on' : ''}`} onClick={() => toggleSupport(x.id)}>{x.label}</button>
              ))}
            </div>
          </div>
          <Select label="Time dimension" value={b.time_dimension} onChange={(v) => upd('time_dimension', v)} options={times.map((x) => [x.id, x.label])} />
          <Select label="Segment dimension" value={b.segment_dimension} onChange={(v) => upd('segment_dimension', v)} options={[['', '—'], ...cats.map((x) => [x.id, x.label])]} />
          <Select label="Region / second dimension" value={b.region_dimension} onChange={(v) => upd('region_dimension', v)} options={[['', '—'], ...cats.map((x) => [x.id, x.label])]} />
          <div className="toggles">
            <Toggle on={b.use_baseline} onChange={(v) => upd('use_baseline', v)} label="Prior-year baseline as target" hint="Labelled as baseline, never as plan" />
            <Toggle on={b.use_forecast} onChange={(v) => upd('use_forecast', v)} label="Snowflake ML FORECAST" hint="Trained on the governed series" />
            <Toggle on={b.use_drivers} onChange={(v) => upd('use_drivers', v)} label="Drivers (ML Top Insights + bridge)" hint="Additive metrics only" />
          </div>
          {data.binding_errors?.length > 0 && <div className="alert error">{data.binding_errors.join(' ')}</div>}
          <div className="actions">
            <button type="button" className="btn" onClick={() => send('set_bindings', { bindings: b, advance: true, source: 'user' })}>Approve mapping &amp; continue →</button>
          </div>
        </div>
        <div className="panel ai">
          <div className="ai-title">✦ Cortex field mapping</div>
          <p className="muted">Cortex reads the semantic view's metric and dimension list and proposes roles. Only IDs that exist in the view are accepted.</p>
          <textarea placeholder="Optional intent, e.g. 'weekly revenue review by customer segment and region'" value={intent} onChange={(e) => setIntent(e.target.value)} />
          <button type="button" className="btn ghost-ai" onClick={() => send('suggest_bindings', { intent })}>Suggest with Cortex</button>
          {sug && (
            <div className="suggestion">
              <div className="prov">{sug.provenance}</div>
              <ul>
                <li>Primary: <b>{label(sug.bindings.primary_metric)}</b></li>
                <li>Supporting: {sug.bindings.supporting_metrics.map(label).join(', ') || '—'}</li>
                <li>Time: {label(sug.bindings.time_dimension)} · Segment: {label(sug.bindings.segment_dimension)} · Region: {label(sug.bindings.region_dimension)}</li>
              </ul>
              {sug.reason && <p className="muted">“{sug.reason}”</p>}
              {sug.rejected?.length > 0 && <div className="alert warn">Rejected (not in semantic view): {sug.rejected.join(', ')}</div>}
              {sug.errors?.length ? <div className="alert error">{sug.errors.join(' ')}</div>
                : <button type="button" className="btn small" onClick={() => setB({ ...sug.bindings })}>Apply suggestion</button>}
            </div>
          )}
          <h4>Semantic view contents</h4>
          <table className="table compact">
            <thead><tr><th>Metric</th><th>Expression</th><th /></tr></thead>
            <tbody>{metrics.map((x) => <tr key={x.id}><td>{x.label}</td><td className="mono small">{x.expression || '—'}</td><td>{x.additive ? <span className="tag">additive</span> : <span className="tag warn">ratio</span>}</td></tr>)}</tbody>
          </table>
          <div className="muted small">{m.dimensions.length} dimensions: {m.dimensions.map((d) => d.label).join(', ')}</div>
        </div>
      </div>
    </section>
  );
}

function Select({ label: l, value, onChange, options }) {
  return (
    <div className="field"><label>{l}</label>
      <select value={value || ''} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
      </select>
    </div>
  );
}

function Toggle({ on, onChange, label: l, hint }) {
  return (
    <button type="button" className={`toggle ${on ? 'on' : ''}`} onClick={() => onChange(!on)}>
      <i /><span><b>{l}</b><small>{hint}</small></span>
    </button>
  );
}

/* ---------------------------------------------------------------- 3. Layout */
const GOAL_EXAMPLES = [
  'Margin problems by region for the CFO',
  'Monthly board pack: growth vs last year and outlook',
  'Which categories and segments need attention this month',
  'Customer mix and concentration risk',
];

function LayoutView({ data, send }) {
  const [goal, setGoal] = useState(data.spec?.goal || '');
  const [showCaps, setShowCaps] = useState(false);
  const caps = data.profile?.capabilities || {};
  const granted = Object.values(caps).filter((c) => c.granted).length;
  return (
    <section className="view">
      <div className="eyebrow">Step 3 · Audience &amp; layout</div>
      <h1>Who is this for, and what should it answer?</h1>
      <div className="audiences">
        {data.catalog_audiences.map((a) => (
          <button type="button" key={a} className={`aud ${data.audience === a ? 'on' : ''}`} onClick={() => send('set_audience', { audience: a })}>{AUDIENCE_LABELS[a]}</button>
        ))}
      </div>
      <div className="caps-bar">
        <span><b>{granted}</b> of {Object.keys(caps).length} data capabilities proven for {AUDIENCE_LABELS[data.audience]}</span>
        <button type="button" className="link" onClick={() => setShowCaps(!showCaps)}>{showCaps ? 'Hide evidence' : 'Show evidence'}</button>
      </div>
      {showCaps && (
        <div className="caps">
          {Object.entries(caps).map(([k, v]) => (
            <div key={k} className={`cap ${v.granted ? 'ok' : 'no'}`}><b>{v.granted ? '✓' : '✗'} {CAP_LABELS[k] || k}</b><small>{v.reason}</small></div>
          ))}
        </div>
      )}
      <div className="panel ai composer">
        <div className="ai-title">✦ Design with Cortex</div>
        <p className="muted small">Cortex reads this semantic view — {data.model?.metrics?.length || 0} metrics, {(data.model?.dimensions || []).filter((d) => !d.is_time).length} dimensions and their cardinality, {data.profile?.calendar?.grain || ''} history, proven capabilities — and designs pages, charts and questions for your goal.
          Every tile is then validated: only known chart types, only real fields, only charts the data can support.</p>
        <textarea rows={2} placeholder="What should this dashboard answer? e.g. 'margin problems by region for the CFO'" value={goal} onChange={(e) => setGoal(e.target.value)} />
        <div className="goal-examples">
          {GOAL_EXAMPLES.map((g) => <button type="button" key={g} className="chip" onClick={() => setGoal(g)}>{g}</button>)}
        </div>
        <div className="composer-foot">
          <span className="muted small">Uses Cortex AI_COMPLETE ({data.features?.model || 'model'}); falls back to a reviewed template if Cortex is unavailable.</span>
          <button type="button" className="btn ai-btn" disabled={!data.features?.complete} onClick={() => send('compose_layout', { goal })}>✦ Design my dashboard</button>
        </div>
      </div>
      <h3 className="sec-title">Or start from a reviewed template</h3>
      <div className="templates">
        {data.options.map((o) => (
          <div key={o.template_id} className={`tpl ${o.selectable ? '' : 'blocked'}`}>
            <div className="tpl-head">
              <b>{o.display_name}</b>
              {o.selectable ? <span className="tag ok">Ready · fit {o.fit_score}%</span> : <span className="tag no">Blocked</span>}
            </div>
            <p>{o.description}</p>
            <div className="pagemap">{o.page_map.map((p, i) => <span key={p.page_id} title={p.purpose}>{i + 1}. {p.label}</span>)}</div>
            {!o.selectable && <div className="missing">Missing: {o.message.replace('Missing: ', '').split(', ').map((x) => CAP_LABELS[x] || label(x)).join(', ')}</div>}
            <div className="tpl-foot">
              <span className="muted small mono">{o.template_id} v{o.version}</span>
              <span className="tpl-btns">
                <button type="button" className="btn small ghost-ai" disabled={!o.selectable || !data.features?.complete}
                  title="Cortex adapts this template to your goal and data"
                  onClick={() => send('compose_layout', { goal, seed_template_id: o.template_id }, 'Cortex is adapting the template…')}>✦ Adapt</button>
                <button type="button" className="btn small" disabled={!o.selectable} onClick={() => send('select_layout', { template_id: o.template_id })}>Use as is →</button>
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- Drawers */
function Drawer({ title, children, onClose, wide }) {
  return (
    <div className="drawer-wrap" onClick={onClose}>
      <div className={`drawer ${wide ? 'wide' : ''}`} onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head"><b>{title}</b><button type="button" className="x" onClick={onClose}>×</button></div>
        <div className="drawer-body">{children}</div>
      </div>
    </div>
  );
}

function AgentPanel({ data, send, ctx, pending }) {
  const [q, setQ] = useState('');
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ block: 'end' }); }, [data.chat?.length, pending]);
  if (!data.source) return <div className="empty">Choose a semantic view first.</div>;
  return (
    <div className="agent">
      {data.agent ? (
        <div className="agent-id"><b>{data.agent.display_name}</b><small className="mono">{data.agent.fqn}</small>
          <small>{["Cortex Analyst", data.agent.has_search && "Cortex Search (documents)", data.agent.has_actions && "log_decision tool"].filter(Boolean).join(" + ")} over {data.source.fqn}</small></div>
      ) : (
        <div className="agent-id"><b>Cortex Agent</b>
          <small>Ask anything about this data. The shared agent for this semantic view is set up automatically on the first question and reused by every dashboard.</small></div>
      )}
      <div className="chat">
        {(data.chat || []).map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === 'user' ? <div className="bubble">{m.text}</div> : (
              <div className="bubble">
                {m.error ? <div className="alert error small">{m.error}</div> : <div className="answer">{m.text}</div>}
                {m.tables?.map((t, j) => (
                  <table className="table compact" key={j}><thead><tr>{t.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                    <tbody>{t.rows.slice(0, 10).map((r, k) => <tr key={k}>{r.map((v, n) => <td key={n}>{String(v)}</td>)}</tr>)}</tbody></table>
                ))}
                {m.actions?.map((x) => (
                  <div key={x.id} className="act-card">✓ Logged in Snowflake by the agent · decision <b>{x.id}</b>
                    <button type="button" className="link" onClick={() => ctx.openDecisions && ctx.openDecisions()}>Open decisions</button></div>
                ))}
                {m.citations?.length > 0 && (
                  <div className="cites"><span>Sources · Cortex Search</span>
                    {m.citations.map((c, j) => <span key={j} className="cite" title={c.text}>{c.label}</span>)}</div>
                )}
                {m.sql?.length > 0 && <details><summary className="prov">SQL generated by Cortex Analyst</summary><pre>{m.sql[0]}</pre></details>}
                {m.raw_preview && <details><summary className="prov">Raw agent response (diagnostics)</summary><pre>{m.raw_preview}</pre></details>}
                <div className="prov">{m.agent} {m.run_id ? `· run ${m.run_id}` : ''} {m.latency ? `· ${m.latency}s` : ''}</div>
                {!m.error && <button type="button" className="link" onClick={() => ctx.decide({ title: 'Follow up: ' + (data.chat[i - 1]?.text || '').slice(0, 90), detail: m.text.slice(0, 900), evidence: { agent: m.agent, run_id: m.run_id, sql: m.sql?.[0] } })}>Log as decision</button>}
              </div>
            )}
          </div>
        ))}
        {pending?.type === 'ask' && <div className="msg agent"><div className="bubble typing">Thinking with Cortex Analyst…</div></div>}
        <div ref={endRef} />
      </div>
      <form className="ask" onSubmit={(e) => { e.preventDefault(); if (q.trim()) { ctx.ask(q.trim()); setQ(''); } }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question about this data…" />
        <button type="submit" className="btn" disabled={!q.trim() || pending?.type === 'ask'}>{pending?.type === 'ask' ? 'Thinking…' : 'Ask'}</button>
      </form>
    </div>
  );
}

function DecisionList({ data, send, ctx }) {
  return (
    <div>
      <button type="button" className="btn small" onClick={() => ctx.decide({})}>+ New decision</button>
      {(data.decisions || []).map((d) => (
        <div className="decision" key={d.decision_id}>
          <b>{d.title}</b><div className="muted small">{d.detail}</div>
          <div className="small">Owner {d.owner || '—'} · due {d.due_date || '—'} · {d.created_by} {d.created_at}</div>
          <select value={d.status} onChange={(e) => send('decision_status', { decision_id: d.decision_id, status: e.target.value })}>
            {['Open', 'In progress', 'Done'].map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      ))}
      {!data.decisions?.length && <div className="empty">No decisions yet.</div>}
    </div>
  );
}

function DecisionDialog({ draft, onCancel, onSave }) {
  const [d, setD] = useState(draft);
  const f = (k) => ({ value: d[k] || '', onChange: (e) => setD({ ...d, [k]: e.target.value }) });
  return (
    <div className="modal-wrap">
      <div className="modal">
        <b>Log a decision</b>
        <div className="field"><label>Title</label><input {...f('title')} /></div>
        <div className="field"><label>Detail / rationale</label><textarea {...f('detail')} /></div>
        <div className="two tight">
          <div className="field"><label>Owner</label><input {...f('owner')} /></div>
          <div className="field"><label>Due date</label><input type="date" {...f('due')} /></div>
        </div>
        {d.evidence && Object.keys(d.evidence).length > 0 && <div className="muted small">Evidence attached: {Object.keys(d.evidence).join(', ')}</div>}
        <div className="actions">
          <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
          <button type="button" className="btn" disabled={!d.title?.trim()} onClick={() => onSave(d)}>Save to Snowflake</button>
        </div>
      </div>
    </div>
  );
}

function Governance({ data, send }) {
  const q = data.quality;
  const ev = data.evals;
  return (
    <div className="gov">
      <h4>How numbers are produced</h4>
      <ul className="small">
        <li>All values: <code>SELECT … FROM SEMANTIC_VIEW({data.source?.fqn || '…'})</code> under role {data.profile?.current_role || 'current role'}.</li>
        <li>Forecasts: <code>SNOWFLAKE.ML.FORECAST</code> trained on those governed series.</li>
        <li>Drivers: <code>SNOWFLAKE.ML.TOP_INSIGHTS</code> + reconciled contribution bridge.</li>
        <li>Layouts: <code>AI_COMPLETE</code> designs pages and tiles from a profile of the data; a validator allows only known chart types, real semantic-view fields and proven capabilities.</li>
        <li>Text: <code>AI_COMPLETE</code> over listed governed facts; field suggestions are validated against allowlists.</li>
        <li>Q&amp;A: Cortex Agent with a Cortex Analyst tool on the same semantic view.</li>
      </ul>
      {data.spec?.governance?.length > 0 && (
        <>
          <h4>Layout decisions <span className="muted small">(every Cortex-proposed tile, checked against the semantic view &amp; proven capabilities)</span></h4>
          <table className="table compact">
            <thead><tr><th>Page</th><th>Tile</th><th>Result</th><th>Why</th></tr></thead>
            <tbody>{data.spec.governance.map((e, i) => (
              <tr key={i}><td className="small">{e.page}</td><td>{e.tile}</td>
                <td><span className={`tag ${e.action === 'kept' || e.action === 'edited' ? 'ok' : e.action === 'repaired' ? 'warn' : 'no'}`}>{e.action}</span></td>
                <td className="small">{e.reason}</td></tr>))}</tbody>
          </table>
        </>
      )}
      <h4>Agent evaluations <span className="muted small">(Snowflake AI Observability · EXECUTE_AI_EVALUATION)</span></h4>
      {!ev ? <div className="muted small">Loading…</div> : !ev.configured ? (
        <div className="muted small">No evaluation set for {ev.agent || 'this agent'} yet. Run <code>setup\run_agent_eval.cmd</code> (Harborline retail agent).</div>
      ) : (
        <div className="eval">
          <div className="eval-bar">
            <select value={ev.run || ''} onChange={(e) => send('eval_load', { run: e.target.value }, 'Loading evaluation…')}>
              {(ev.runs || []).map((r) => <option key={r.run_name} value={r.run_name}>{r.run_name} · {r.started_at}</option>)}
            </select>
            <button type="button" className="ghost small" onClick={() => send('eval_load', { run: ev.run }, 'Refreshing…')}>↻ Refresh</button>
            <button type="button" className="btn small" onClick={() => send('eval_start', {}, 'Starting Snowflake evaluation…')}>Run new evaluation</button>
            {ev.gate != null && <span className={`gate ${ev.gate ? 'ok' : 'no'}`}>Promotion gate: {ev.gate ? 'PASS' : 'FAIL'}</span>}
          </div>
          {ev.status && <div className="muted small">Status: {ev.status}</div>}
          {ev.error && <div className="muted small">Results not available yet: {ev.error}</div>}
          {ev.summary?.length > 0 && (
            <table className="table compact"><thead><tr><th>Metric</th><th>Score</th><th>Gate</th><th>Questions</th></tr></thead>
              <tbody>{ev.summary.map((m) => (
                <tr key={m.metric_name}><td>{m.metric_name}</td>
                  <td><span className="score"><i style={{ width: `${Math.round(Math.max(0, Math.min(1, m.score)) * 100)}%` }} /></span> {m.score.toFixed(2)}</td>
                  <td>{m.threshold == null ? '—' : <span className={`tag ${m.pass ? 'ok' : 'no'}`}>{m.pass ? '≥' : '<'} {m.threshold}</span>}</td>
                  <td>{m.n}</td></tr>))}</tbody></table>
          )}
          {ev.records?.length > 0 && (
            <details><summary className="prov">Per-question scores ({ev.records.length})</summary>
              <table className="table compact"><thead><tr><th>Question</th><th>Metric</th><th>Score</th></tr></thead>
                <tbody>{ev.records.map((r, i) => <tr key={i}><td className="small">{r.input}</td><td className="small">{r.metric_name}</td><td>{Number(r.score ?? 0).toFixed(2)}</td></tr>)}</tbody></table>
            </details>
          )}
          <div className="muted small">Full traces: Snowsight → AI &amp; ML → Agents → {ev.agent?.split('.').pop()} → Evaluations.</div>
        </div>
      )}
      <h4>AI run ledger <span className="muted small">({data.app_schema}.AA_AI_RUNS)</span></h4>
      {!q ? <div className="muted">Loading…</div> : (
        <table className="table compact">
          <thead><tr><th>When</th><th>Feature</th><th>Status</th><th>Provenance</th><th>s</th></tr></thead>
          <tbody>{q.ledger.map((r, i) => <tr key={i}><td className="small">{r.created_at}</td><td>{r.feature}</td><td>{r.status}</td><td className="small">{r.provenance}</td><td>{Number(r.latency_s || 0).toFixed(1)}</td></tr>)}</tbody>
        </table>
      )}
      <h4>Cost by app feature, last {q?.by_feature?.days || 7} days <span className="muted small">(QUERY_TAG on every app query · ACCOUNT_USAGE, lags up to ~3 h)</span></h4>
      {q?.by_feature?.error ? <div className="muted small">Needs ACCOUNT_USAGE access: {q.by_feature.error}</div>
        : !(q?.by_feature?.rows || []).length ? <div className="muted small">No tagged queries in ACCOUNT_USAGE yet (new tags appear after the usage views refresh).</div> : (
        <table className="table compact"><thead><tr><th>Feature</th><th>Queries</th><th>Elapsed s</th><th>Cortex credits</th><th>Tokens</th><th>Warehouse credits</th></tr></thead>
          <tbody>{q.by_feature.rows.map((r, i) => <tr key={i}><td>{r.feature}</td><td>{r.queries}</td><td>{r.elapsed_s}</td>
            <td>{r.cortex_credits == null ? '—' : Number(r.cortex_credits).toFixed(4)}</td><td>{r.tokens ?? '—'}</td>
            <td>{r.warehouse_credits == null ? '—' : Number(r.warehouse_credits).toFixed(4)}</td></tr>)}</tbody></table>
      )}
      <h4>Cortex usage, last 30 days</h4>
      {q?.usage?.error ? <div className="muted small">Needs ACCOUNT_USAGE access: {q.usage.error}</div> : (
        <table className="table compact"><thead><tr><th>Function</th><th>Model</th><th>Credits</th><th>Tokens</th></tr></thead>
          <tbody>{(q?.usage?.rows || []).map((r, i) => <tr key={i}><td>{r.function_name}</td><td>{r.model_name}</td><td>{Number(r.credits || 0).toFixed(3)}</td><td>{r.tokens}</td></tr>)}</tbody></table>
      )}
      <h4>Recent SQL</h4>
      <pre className="sql-log">{(data.sql_log || []).slice(-12).join('\n\n')}</pre>
    </div>
  );
}
