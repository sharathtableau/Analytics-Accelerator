import React, { useEffect, useRef, useState } from 'react';

const GROUPS = [
  { id: 'all', label: 'All ideas' },
  { id: 'executives', label: 'Executive' },
  { id: 'managers', label: 'Manager' },
  { id: 'operations', label: 'Operations' },
];
const AUD_TAG = { executives: 'Executive', managers: 'Manager', weekly_business_review: 'Weekly review', daily_operations: 'Operations' };
const groupOf = (a) => (a === 'weekly_business_review' || a === 'daily_operations' ? 'operations' : a);
const AUD_PICK = [
  { id: '', label: 'Auto' }, { id: 'executives', label: 'Executive' }, { id: 'managers', label: 'Manager' },
  { id: 'daily_operations', label: 'Operations' }, { id: 'weekly_business_review', label: 'Weekly review' },
];
const PLACEHOLDERS = [
  'Board pack on revenue and margin vs last year, by region…',
  'Which segments and categories need attention this month?',
  'Live operations today: pace by hour and what is going wrong…',
  'Where are we losing profit, and what is driving it?',
];

function Icon({ kind }) {
  const p = { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' };
  if (kind === 'executives') return <svg {...p}><path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" /></svg>;
  if (kind === 'managers') return <svg {...p}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>;
  return <svg {...p}><path d="M3 12h4l3-8 4 16 3-8h4" /></svg>;
}

function Sparkle({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round">
      <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" /><path d="M19 3v4M17 5h4" />
    </svg>
  );
}

export default function Home({ data, send, pending, onBuilder }) {
  const [text, setText] = useState('');
  const [picked, setPicked] = useState(null);   // idea / request placed in the box: its dataset + metrics
  const [aud, setAud] = useState('');
  const [group, setGroup] = useState('all');
  const hasFeatured = (data.featured || []).length > 0;
  const [scope, setScope] = useState('featured');
  const [ph, setPh] = useState(0);
  const asked = useRef({});
  const taRef = useRef(null);
  const ideas = data.suggestions || [];
  const b = data.building;
  const routing = pending?.type === 'route_prompt';
  const designing = pending?.type === 'compose_layout' || (b && !data.error);
  const busy = routing || designing;

  useEffect(() => { const t = setInterval(() => setPh((i) => (i + 1) % PLACEHOLDERS.length), 3500); return () => clearInterval(t); }, []);
  useEffect(() => {
    if (pending) return;
    if (!ideas.length && !asked.current.base) { asked.current.base = true; send('home_suggestions', {}, 'Profiling your data…', true); }
    else if (data.suggestions_by === 'catalog' && !asked.current.ai) { asked.current.ai = true; send('home_suggestions_ai', {}, 'Cortex is proposing dashboards…', true); }
  }, [ideas.length, data.suggestions_by, pending]);
  useEffect(() => {
    const key = b ? `${b.goal}:${data.revision}` : '';
    if (b && !pending && !data.error && asked.current.compose !== key) {
      asked.current.compose = key;
      send('compose_layout', { goal: b.goal }, 'Cortex is designing your dashboard…', true);
    }
  }, [b, pending, data.revision]);

  // Nothing builds until the user presses send: ideas and "Try asking" only fill the box for editing.
  const submit = () => {
    if (busy || !text.trim()) return;
    const t = text.trim();
    if (picked?.s?.semantic_view) {
      // keep the picked dataset; keep its metrics only while the text is unchanged (edited text decides metrics)
      const edited = t !== picked.text;
      send('route_prompt', { suggestion: { ...picked.s, goal: t, metrics: edited ? [] : (picked.s.metrics || []) },
        prompt: t, audience: aud || picked.s.audience }, 'Preparing the governed data…', true);
    } else send('route_prompt', { prompt: t, audience: aud }, 'Finding the right governed data…', true);
  };
  const place = (s, t, label) => {           // put an idea / request in the box, ready to edit
    setText(t); setAud(s.audience || ''); setPicked({ s, text: t, label });
    if (window.scrollTo) window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => { const el = taRef.current; if (el) { el.focus(); el.setSelectionRange(t.length, t.length); } }, 50);
  };
  const prompts = data.prompts || [];
  const audKey = aud === 'weekly_business_review' ? 'managers' : aud;
  // one per audience on Auto; both for the chosen audience
  const tries = audKey ? prompts.filter((t) => t.audience === audKey)
    : ['executives', 'managers', 'daily_operations'].map((a) => prompts.find((t) => t.audience === a)).filter(Boolean);
  const shown = ideas.filter((s) => (group === 'all' || groupOf(s.audience) === group)
    && (!hasFeatured || scope === 'all' || s.featured));
  const f = data.features || {};
  const aiFlags = [['Cortex AI', f.complete], ['ML Forecast', f.forecast], ['Top Insights', f.top_insights], ['Cortex Agents', f.agents]];

  return (
    <section className="home view">
      <div className="home-hero">
        <div className="orb"><Sparkle /></div>
        <h1>What can I help you build today{data.viewer ? `, ${data.viewer}` : ''}?</h1>
        <p>Describe the dashboard or the question. Cortex picks the governed data and designs the layout; Snowflake computes every number.</p>
        <div className={`prompt-bar ${busy ? 'busy-bar' : ''}`}>
          {picked && (
            <div className="picked">Editing: <b>{picked.label}</b> · change any words, then press send
              <button type="button" className="link" onClick={() => { setPicked(null); setText(''); }}>Clear</button></div>
          )}
          <textarea ref={taRef} rows={picked ? 3 : 2} value={text} placeholder={PLACEHOLDERS[ph]} disabled={busy}
            onChange={(e) => { setText(e.target.value); if (!e.target.value.trim()) setPicked(null); }}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }} />
          <div className="prompt-foot">
            <div className="aud-pick">
              <span className="muted small">For</span>
              {AUD_PICK.map((a) => (
                <button type="button" key={a.id} className={`seg ${aud === a.id ? 'on' : ''}`} onClick={() => setAud(a.id)}>{a.label}</button>
              ))}
            </div>
            <button type="button" className="send" disabled={busy || !text.trim()} onClick={submit} aria-label="Build dashboard">
              {busy ? <span className="spinner" /> : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>}
            </button>
          </div>
        </div>
        {data.data_brief?.length > 0 && (
          <div className="data-brief">
            <span className="db-label">Your data</span>
            <div>{data.data_brief.map((l) => <p key={l}>{l}</p>)}</div>
          </div>
        )}
        {tries.length > 0 && (
          <div className="try-asking">
            <span className="db-label">Try asking</span>
            <div className="try-list">
              {tries.map((t) => (
                <button type="button" key={t.text} className="try" disabled={busy} title="Puts this request in the box to edit; nothing is built until you press send"
                  onClick={() => place({ semantic_view: t.semantic_view, audience: t.audience, metrics: t.metrics, title: t.text }, t.text, `${AUD_TAG[t.audience]} request`)}>
                  <em>{AUD_TAG[t.audience]}</em>{t.text}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="ai-ready">
          {aiFlags.map(([n, ok]) => <span key={n} className={ok ? 'ok' : 'off'}><i />{n}</span>)}
          {data.catalog_size ? <span className="muted">· {data.catalog_size} governed datasets profiled</span> : null}
        </div>
      </div>

      <div className="featured-bar">
        {hasFeatured && data.featured.map((f) => (
          <span key={f.fqn} className="featured-ds" title={f.fqn}>
            <i className="live-dot" /> <b>{f.label}</b> · {f.adhoc ? `${f.metrics} measures from facts` : `${f.metrics} governed metrics`} · {f.dimensions} dimensions{f.adhoc ? '' : ' · updating live'}
          </span>
        ))}
        {onBuilder && <button type="button" className="link connect-link" onClick={onBuilder}>＋ Connect a Snowflake table</button>}
      </div>
      {data.catalog_skipped?.length > 0 && (
        <details className="skipped-views">
          <summary>{data.catalog_skipped.length} semantic view{data.catalog_skipped.length > 1 ? 's' : ''} found but not used for ideas</summary>
          <ul>{data.catalog_skipped.map((v) => <li key={v.fqn}><b title={v.fqn}>{v.name}</b>: {v.reason}.</li>)}</ul>
        </details>
      )}

      {(routing || b) && (
        <div className="build-card">
          <div className="build-title"><Sparkle size={18} /> Building: <i>{b?.prompt || text}</i></div>
          <ol className="build-steps">
            <li className={b ? 'done' : 'now'}>
              <b>Understand the request &amp; choose governed data</b>
              {b && <span>{AUD_TAG[b.audience]} dashboard on <b>{b.domain}</b>{b.reason ? ` — ${b.reason}` : ''} <em>({b.by})</em></span>}
            </li>
            <li className={b ? 'done' : ''}>
              <b>Profile the data</b>
              {b && <span>{b.metrics} metrics · {b.dimensions} dimensions · history, cardinality and capabilities proven</span>}
            </li>
            <li className={b ? 'now' : ''}><b>Cortex drafts pages &amp; charts, validator checks every tile</b></li>
            <li><b>You review metrics &amp; outline, then build</b></li>
          </ol>
        </div>
      )}

      <div className="idea-head">
        <h3>Ideas from your data</h3>
        {hasFeatured && (
          <div className="idea-tabs">
            <button type="button" className={`seg ${scope === 'featured' ? 'on' : ''}`} onClick={() => setScope('featured')}>● {data.featured.length > 1 ? 'Featured data' : data.featured[0].label}</button>
            <button type="button" className={`seg ${scope === 'all' ? 'on' : ''}`} onClick={() => setScope('all')}>All data{ideas.length ? ` (${ideas.length})` : ''}</button>
          </div>
        )}
        <div className="idea-tabs">
          {GROUPS.map((g) => <button type="button" key={g.id} className={`seg ${group === g.id ? 'on' : ''}`} onClick={() => setGroup(g.id)}>{g.label}</button>)}
        </div>
        <span className="idea-src">
          {pending?.type === 'home_suggestions_ai' && data.suggestions_by === 'cortex' ? <><span className="spinner dark sm" /> Cortex is writing new ideas…</>
            : data.suggestions_by === 'cortex' ? <><Sparkle size={13} /> Suggested by Cortex{data.suggestions_at ? ` · saved ${data.suggestions_at}` : ''}
              <button type="button" className="link" title="Ask Cortex for a fresh set of ideas (added on top; earlier ideas stay below)"
                onClick={() => send('home_suggestions_ai', { fresh: true }, 'Cortex is writing new ideas…', true)}>↻ New ideas</button></>
            : data.suggestions_by === 'catalog' ? <><span className="spinner dark sm" /> Cortex is tailoring ideas…</>
              : ideas.length ? 'From your data catalog' : null}
        </span>
      </div>
      {ideas.length > 0 && !shown.length && (
        <div className="empty">No ideas for this filter yet. <button type="button" className="link" onClick={() => setScope('all')}>Show all data</button></div>
      )}
      {!ideas.length ? (
        <div className="ideas">{[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="idea skeleton"><i /><b /><span /><span /></div>)}</div>
      ) : (
        <div className="ideas">
          {shown.map((s, i) => (
            <button type="button" key={`${s.title}-${i}`} className={`idea ${groupOf(s.audience)}`} disabled={busy} title="Puts this idea in the box to edit; nothing is built until you press send"
              onClick={() => place(s, s.goal || s.title, `${AUD_TAG[s.audience]} idea "${s.title}"`)}>
              <div className="idea-top"><span className="idea-icon"><Icon kind={groupOf(s.audience)} /></span><span className="idea-aud">{s.featured && <em className="live-tag">● Live</em>}{AUD_TAG[s.audience]}{s.earlier && <em className="idea-earlier" title={`Suggested earlier (saved ${s.earlier})`}>· Earlier</em>}</span></div>
              {s.theme_label && <span className="idea-theme">{s.theme_label}</span>}
              <b>{s.title}</b>
              <span className="idea-detail">{s.detail}</span>
              <span className="idea-foot">
                {(s.metrics || []).slice(0, 3).map((m) => <em key={m}>{m}</em>)}
                <small>{s.domain}</small>
              </span>
            </button>
          ))}
        </div>
      )}

      {data.published?.length > 0 && (
        <>
          <h3 className="sec-title">Published dashboards</h3>
          <div className="recent">
            {data.published.slice(0, 8).map((d) => (
              <button type="button" key={d.dashboard_id} className="recent-card pub" disabled={busy} onClick={() => send('open_published', { dashboard_id: d.dashboard_id })}>
                <b>📊 {d.name}</b><small>v{d.version} · {AUD_TAG[d.audience] || d.audience} · {d.published_by || ''} · {d.published_at}</small>
              </button>
            ))}
          </div>
        </>
      )}
      {data.dashboards?.length > 0 && (
        <>
          <h3 className="sec-title">Your drafts</h3>
          <div className="recent">
            {data.dashboards.slice(0, 6).map((d) => (
              <button type="button" key={d.dashboard_id} className="recent-card" disabled={busy} onClick={() => send('open_dashboard', { dashboard_id: d.dashboard_id })}>
                <b>{d.name}</b><small>{AUD_TAG[d.audience] || d.audience} · v{d.version} · {d.created_at}</small>
              </button>
            ))}
          </div>
        </>
      )}
      <div className="home-foot">
        <button type="button" className="link" onClick={() => send('go', { step: 'source' }, 'Opening…')}>Browse governed data sources (advanced) →</button>
      </div>
    </section>
  );
}
