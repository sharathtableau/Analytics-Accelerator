import React, { useLayoutEffect, useRef, useState } from 'react';
import { fmt } from './format.js';

let _gid = 0;
const useGid = (p) => { const r = useRef(null); if (!r.current) { _gid += 1; r.current = `${p}${_gid}`; } return r.current; };

/** Track the rendered width so SVG text stays a constant size. */
function useWidth(fallback = 720) {
  const ref = useRef(null);
  const [w, setW] = useState(fallback);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const update = () => { const cw = Math.round(el.clientWidth); if (cw > 50) setW(cw); };
    update();
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(update) : null;
    if (ro) ro.observe(el);
    return () => ro && ro.disconnect();
  }, []);
  return [ref, w];
}

/** Floating tooltip positioned inside a chart container. */
function useTip(box) {
  const [tip, setTip] = useState(null);
  const show = (e, content) => {
    const el = box.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left, y = e.clientY - r.top;
    setTip({ x, y, content, flip: x > r.width * 0.62 });
  };
  const hide = () => setTip(null);
  const node = tip ? (
    <div className={`tip ${tip.flip ? 'flip' : ''}`} style={{ left: tip.x, top: tip.y }}>{tip.content}</div>
  ) : null;
  return [node, show, hide];
}

function TipBody({ title, rows = [] }) {
  return (
    <>
      {title && <div className="tip-title">{title}</div>}
      {rows.filter(Boolean).map(([k, v, cls], i) => (
        <div className="tip-row" key={i}><span>{k}</span><b className={cls || ''}>{v}</b></div>
      ))}
    </>
  );
}

function niceTicks(min, max, count = 4) {
  if (min === max) { max = min + 1; }
  const span = max - min;
  const step0 = span / count;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) || step0;
  const lo = Math.floor(min / step) * step;
  const hi = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(v);
  return ticks;
}

/** Value-axis domain. Starts at 0 unless the data sits in a narrow band far from zero
 *  (rates such as in-stock 94–96%), where a zero baseline flattens every movement. */
function valueDomain(vals, { force0 = false } = {}) {
  const lo = Math.min(...vals), hi = Math.max(...vals);
  if (force0 || lo <= 0 || hi <= 0) return { lo: Math.min(0, lo), hi: Math.max(hi, lo === hi ? lo + 1e-9 : hi), zoomed: false };
  if ((hi - lo) / hi > 0.4) return { lo: 0, hi, zoomed: false };
  const pd = Math.max((hi - lo) * 0.25, hi * 0.005);
  return { lo: Math.max(0, lo - pd), hi: hi + pd, zoomed: true };
}

/** Zig-zag on the value axis: tells the reader the axis does not start at zero. */
function AxisBreak({ x, y }) {
  return (
    <g className="axis-break"><title>Axis zoomed to the data range (does not start at 0)</title>
      <rect x={x - 7} y={y - 7} width="14" height="9" />
      <path d={`M${x - 7},${y - 2} l3.5,-3 l3.5,3 l3.5,-3 l3.5,3 M${x - 7},${y + 2} l3.5,-3 l3.5,3 l3.5,-3 l3.5,3`} />
    </g>
  );
}

const pctTxt = (v) => (v == null ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`);

/** Line chart: actual, optional baseline (dashed), optional forecast band. */
export function LineChart({ points = [], forecast = [], kind, height = 240, baselineLabel, seriesLabel = 'Actual' }) {
  const [hover, setHover] = useState(null);
  const ref = useRef(null);
  const [box, W] = useWidth();
  const [tip, show, hide] = useTip(box);
  const gid = useGid('lg');
  const all = [...points.map((p) => ({ ...p, t: 'a' })), ...forecast.map((p) => ({ ...p, t: 'f' }))];
  const vals = [];
  points.forEach((p) => { if (p.value != null) vals.push(p.value); if (p.baseline != null) vals.push(p.baseline); });
  forecast.forEach((p) => { vals.push(p.lower, p.upper, p.forecast); });
  if (!vals.length) return <div ref={box}><Empty text="No data points in this window." /></div>;
  const dom = valueDomain(vals);
  const ticks = niceTicks(dom.lo, dom.hi);
  const y0 = ticks[0], y1 = ticks[ticks.length - 1];
  const pad = { l: 56, r: 12, t: 12, b: 28 };
  const iw = W - pad.l - pad.r, ih = height - pad.t - pad.b;
  const n = all.length;
  const x = (i) => pad.l + (n <= 1 ? iw / 2 : (i * iw) / (n - 1));
  const y = (v) => pad.t + ih - ((v - y0) / (y1 - y0 || 1)) * ih;
  const path = (arr, key, offset = 0) => arr.map((p, i) => (p[key] == null ? null : `${x(i + offset)},${y(p[key])}`))
    .filter(Boolean).map((s, i) => (i ? 'L' : 'M') + s).join(' ');
  const off = points.length;
  const band = forecast.length ? [
    ...forecast.map((p, i) => `${x(i + off)},${y(p.upper)}`),
    ...forecast.slice().reverse().map((p, i) => `${x(off + forecast.length - 1 - i)},${y(p.lower)}`),
  ] : [];
  const every = Math.max(1, Math.ceil(n / Math.max(3, Math.floor(W / 90))));
  const onMove = (e) => {
    const b = ref.current.getBoundingClientRect();
    const px = ((e.clientX - b.left) / b.width) * W;
    const i = Math.max(0, Math.min(n - 1, Math.round(((px - pad.l) / iw) * (n - 1))));
    setHover(i);
    const h = all[i];
    const prev = i > 0 && all[i - 1].t === 'a' ? all[i - 1].value : null;
    show(e, h.t === 'a'
      ? <TipBody title={h.label} rows={[[seriesLabel, fmt(h.value, kind)],
        h.baseline != null && [baselineLabel || 'Baseline', fmt(h.baseline, kind)],
        h.baseline != null && ['vs baseline', pctTxt(h.baseline ? (h.value - h.baseline) / Math.abs(h.baseline) : null)],
        prev != null && h.value != null && ['vs previous', pctTxt(prev ? (h.value - prev) / Math.abs(prev) : null)]]} />
      : <TipBody title={`${h.label} · forecast`} rows={[['Forecast', fmt(h.forecast, kind)],
        ['80% range', `${fmt(h.lower, kind)} – ${fmt(h.upper, kind)}`]]} />);
  };
  const h = hover != null ? all[hover] : null;
  return (
    <div className="chart" ref={box}>
      <svg ref={ref} viewBox={`0 0 ${W} ${height}`} role="img" onMouseMove={onMove}
        onMouseLeave={() => { setHover(null); hide(); }}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
            <text x={pad.l - 8} y={y(t) + 4} className="tick" textAnchor="end">{fmt(t, kind)}</text>
          </g>
        ))}
        {all.map((p, i) => (((i % every === 0 && n - 1 - i >= every / 2) || i === n - 1)) && (
          <text key={i} x={x(i)} y={height - 8} className="tick" textAnchor={i === n - 1 ? 'end' : i === 0 ? 'start' : 'middle'}>{shortLabel(p.label)}</text>
        ))}
        {dom.zoomed && <AxisBreak x={pad.l} y={pad.t + ih - 3} />}
        {band.length > 0 && <polygon points={band.join(' ')} className="band" />}
        {points.some((p) => p.baseline != null) && <path d={path(points, 'baseline')} className="line baseline" />}
        <defs><linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#29B5E8" stopOpacity="0.28" /><stop offset="100%" stopColor="#29B5E8" stopOpacity="0" /></linearGradient></defs>
        {(() => { const pts = points.map((p, i) => (p.value == null ? null : [x(i), y(p.value)])).filter(Boolean);
          return pts.length > 1 ? <path d={`M${pts[0][0]},${pad.t + ih} ${pts.map((q) => `L${q[0]},${q[1]}`).join(' ')} L${pts[pts.length - 1][0]},${pad.t + ih} Z`} fill={`url(#${gid})`} /> : null; })()}
        <path d={path(points, 'value')} className="line actual" />
        {(() => { const li = points.map((p) => p.value).lastIndexOf(points.filter((p) => p.value != null).slice(-1)[0]?.value);
          return li >= 0 && hover == null ? <circle cx={x(li)} cy={y(points[li].value)} r="4.5" className="dot end" /> : null; })()}
        {forecast.length > 0 && (
          <path d={`M${x(off - 1)},${y(points[points.length - 1]?.value ?? forecast[0].forecast)} `
            + forecast.map((p, i) => `L${x(i + off)},${y(p.forecast)}`).join(' ')} className="line forecast" />
        )}
        {h && <line x1={x(hover)} x2={x(hover)} y1={pad.t} y2={pad.t + ih} className="cursor" />}
        {h && h.t === 'a' && h.value != null && <circle cx={x(hover)} cy={y(h.value)} r="4" className="dot" />}
        {h && h.t === 'f' && <circle cx={x(hover)} cy={y(h.forecast)} r="4" className="dot f" />}
      </svg>
      {tip}
      <div className="legend">
        <span><i className="sw actual" />{seriesLabel}</span>
        {points.some((p) => p.baseline != null) && <span><i className="sw baseline" />{baselineLabel || 'Baseline'}</span>}
        {forecast.length > 0 && <span><i className="sw forecast" />Forecast (80% band)</span>}
      </div>
    </div>
  );
}

function shortLabel(l = '') {
  return l.replace('Wk of ', '').replace(/ 20(\d\d)$/, " '$1");
}

/** KPI sparkline with a labelled window, highlighted current point and hover values. */
export function Sparkline({ values = [], labels = [], kind, height = 44 }) {
  const [hover, setHover] = useState(null);
  const [box, width] = useWidth(220);
  const [tip, show, hide] = useTip(box);
  const gid = useGid('sg');
  const v = values.filter((x) => x != null);
  if (v.length < 2) return null;
  const min = Math.min(...v), max = Math.max(...v);
  const px = (i) => 3 + (i / (values.length - 1)) * (width - 6);
  const py = (val) => height - 4 - ((val - min) / (max - min || 1)) * (height - 8);
  const pts = values.map((val, i) => (val == null ? null : `${px(i)},${py(val)}`)).filter(Boolean).join(' ');
  const last = values.length - 1;
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const i = Math.max(0, Math.min(last, Math.round(((e.clientX - r.left) / r.width) * last)));
    setHover(i);
    show(e, <TipBody title={labels[i] || ''} rows={[['Value', fmt(values[i], kind)]]} />);
  };
  return (
    <div className="spark-wrap" ref={box}>
      <svg className="spark" viewBox={`0 0 ${width} ${height}`} onMouseMove={onMove}
        onMouseLeave={() => { setHover(null); hide(); }}>
        <defs><linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#29B5E8" stopOpacity="0.30" /><stop offset="100%" stopColor="#29B5E8" stopOpacity="0" /></linearGradient></defs>
        {(() => { const idx = values.map((val, i) => (val == null ? null : i)).filter((i) => i != null);
          return <path d={`M${px(idx[0])},${height} ${idx.map((i) => `L${px(i)},${py(values[i])}`).join(' ')} L${px(idx[idx.length - 1])},${height} Z`} fill={`url(#${gid})`} stroke="none" />; })()}
        <polyline points={pts} />
        {values[last] != null && <circle cx={px(last)} cy={py(values[last])} r="3" className="spark-now" />}
        {hover != null && values[hover] != null && <circle cx={px(hover)} cy={py(values[hover])} r="3" className="spark-hover" />}
      </svg>
      {tip}
    </div>
  );
}

/** Horizontal ranked bars with prior-period marker. */
export function RankedBars({ rows = [], kind, max = 12, onSelect, currentLabel, priorLabel, inverse = false }) {
  const good = (c) => (c == null || c === 0 ? '' : (c > 0) !== inverse ? 'up' : 'down');
  const box = useRef(null);
  const [tip, show, hide] = useTip(box);
  const shown = rows.slice(0, max);
  const top = Math.max(...shown.map((r) => Math.max(r.current || 0, r.prior || 0)), 1e-12);
  return (
    <div className="bars chart" ref={box} onMouseLeave={hide}>
      {shown.map((r) => (
        <button type="button" key={r.segment} className="bar-row" onClick={() => onSelect && onSelect(r)}
          onMouseMove={(e) => show(e, <TipBody title={r.segment} rows={[
            [currentLabel || 'Current', fmt(r.current, kind)],
            r.prior != null && [priorLabel || 'Prior', fmt(r.prior, kind)],
            r.change != null && ['Change', pctTxt(r.change), good(r.change)],
            r.share != null && ['Share of total', `${(r.share * 100).toFixed(1)}%`],
            onSelect && ['', 'Click to ask the agent why'],
          ]} />)}>
          <span className="bar-label">{r.segment}</span>
          <span className="bar-track">
            <i className="bar-fill" style={{ width: `${Math.max(0, (r.current || 0) / top) * 100}%` }} />
            {r.prior != null && <i className="bar-prior" style={{ left: `${Math.max(0, r.prior / top) * 100}%` }} />}
          </span>
          <span className="bar-value">{fmt(r.current, kind)}</span>
          <span className={`bar-delta ${good(r.change)}`}>
            {r.change == null ? '' : `${r.change > 0 ? '▲' : '▼'} ${(Math.abs(r.change) * 100).toFixed(0)}%`}
          </span>
        </button>
      ))}
      {tip}
    </div>
  );
}

/** Waterfall: start, signed steps, end (reconciled). */
export function Waterfall({ start, end, steps = [], kind, startLabel, endLabel, height = 250 }) {
  const [box, W] = useWidth();
  const [tip, show, hide] = useTip(box);
  const cols = [{ name: startLabel, v: start, type: 'total' },
    ...steps.map((s) => ({ name: s.segment, v: s.delta, type: s.delta >= 0 ? 'up' : 'down' })),
    { name: endLabel, v: end, type: 'total' }];
  let run = 0;
  const bars = cols.map((c) => {
    if (c.type === 'total') { run = c.v; return { ...c, a: 0, b: c.v }; }
    const a = run; run += c.v; return { ...c, a, b: run };
  });
  // Totals bars start at 0, so only zoom the axis when every running level stays well above 0.
  const levels = bars.flatMap((b) => (b.type === 'total' ? [b.b] : [b.a, b.b]));
  const dom = valueDomain(levels);
  const ticks = niceTicks(dom.lo, dom.hi, 4);
  const lo = ticks[0], hi = ticks[ticks.length - 1];
  if (dom.zoomed) bars.forEach((b) => { if (b.type === 'total') b.a = lo; });
  const pad = { l: 56, r: 8, t: 16, b: 46 };
  const iw = W - pad.l - pad.r, ih = height - pad.t - pad.b;
  const bw = iw / bars.length;
  const y = (v) => pad.t + ih - ((v - lo) / (hi - lo || 1)) * ih;
  const total = start || 0;
  return (
    <div className="chart" ref={box}>
      <svg viewBox={`0 0 ${W} ${height}`} role="img" onMouseLeave={hide}>
        {ticks.map((t) => (
          <g key={t}><line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
            <text x={pad.l - 8} y={y(t) + 4} className="tick" textAnchor="end">{fmt(t, kind)}</text></g>
        ))}
        {bars.map((b, i) => (
          <g key={i} onMouseMove={(e) => show(e, <TipBody title={b.name} rows={b.type === 'total'
            ? [['Total', fmt(b.v, kind)]]
            : [['Contribution', `${b.v >= 0 ? '+' : '−'}${fmt(Math.abs(b.v), kind)}`, b.v >= 0 ? 'up' : 'down'],
              ['Running total', fmt(b.b, kind)], total ? ['% of starting total', pctTxt(b.v / Math.abs(total))] : null]} />)}>
            <rect x={pad.l + i * bw + bw * 0.15} width={bw * 0.7} y={y(Math.max(b.a, b.b))}
              height={Math.max(1, Math.abs(y(b.a) - y(b.b)))} rx="4" className={`wf ${b.type}`} />
            <text x={pad.l + i * bw + bw / 2} y={y(Math.max(b.a, b.b)) - 4} className="tick val" textAnchor="middle">
              {b.type === 'total' ? fmt(b.v, kind) : `${b.v >= 0 ? '+' : '−'}${fmt(Math.abs(b.v), kind)}`}
            </text>
            <text x={pad.l + i * bw + bw / 2} y={height - 26} className="tick" textAnchor="middle">
              {String(b.name).slice(0, 12)}
            </text>
          </g>
        ))}
        {dom.zoomed && <AxisBreak x={pad.l} y={pad.t + ih - 3} />}
      </svg>
      {tip}
    </div>
  );
}

// Sequential ramp (one hue, light -> dark, Snowflake blue). Steps 0-4 take dark text, 5-6 white (all >= 5:1 contrast).
const HEAT_RAMP = ['#EEF6FC', '#D2E7F6', '#A9D1EE', '#78B4E0', '#4693CF', '#1F72B3', '#0D548C'];

/** Shading for skewed data: outliers (> Q3 + 3*IQR) get the darkest shade and an outline, so the story
 *  cells pop; ordinary cells are split into equal-count shades so their differences stay visible. */
function heatScale(flat) {
  const sorted = [...flat].sort((a, b) => a - b);
  const n = sorted.length;
  const top = HEAT_RAMP.length - 1;
  if (!n) return { step: () => 0, breaks: [], cut: null };
  const qt = (arr, p) => arr[Math.min(arr.length - 1, Math.max(0, Math.floor(p * arr.length)))];
  const iqr = qt(sorted, 0.75) - qt(sorted, 0.25);
  const cutRaw = qt(sorted, 0.75) + 3 * iqr;
  const body = n >= 8 && iqr > 0 ? sorted.filter((v) => v <= cutRaw) : sorted;
  const cut = body.length < n ? cutRaw : null;
  const k = cut == null ? HEAT_RAMP.length : top;                 // shades for ordinary cells
  const uniq = [...new Set(body)];
  let stepBody, breaks;
  if (uniq.length <= k) {
    stepBody = (v) => Math.round((uniq.indexOf(v) / Math.max(1, uniq.length - 1)) * (k - 1));
    breaks = uniq.map((v) => [v, v]);
  } else {
    const cuts = Array.from({ length: k - 1 }, (_, i) => qt(body, (i + 1) / k));
    stepBody = (v) => { let i = 0; while (i < cuts.length && v >= cuts[i]) i += 1; return i; };
    breaks = Array.from({ length: k }, (_, i) => [i === 0 ? body[0] : cuts[i - 1], i === k - 1 ? body[body.length - 1] : cuts[i]]);
  }
  const step = (v) => (cut != null && v > cut ? top : stepBody(v));
  return { step, breaks, cut, max: sorted[n - 1] };
}

export function Heatmap({ rows = [], cols = [], values = [], kind, rowLabel, colLabel }) {
  const box = useRef(null);
  const [tip, show, hide] = useTip(box);
  const flat = values.flat().filter((v) => v != null);
  const { step, breaks, cut, max } = heatScale(flat);
  const total = flat.reduce((a, b) => a + b, 0);
  const additive = kind !== 'percent';
  return (
    <div className="heat-wrap chart" ref={box} onMouseLeave={hide}>
      <table className="heat">
        <thead><tr><th>{rowLabel} \ {colLabel}</th>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r}><th>{r}</th>
              {cols.map((c, j) => {
                const v = values[i]?.[j];
                const st = v == null ? -1 : step(v);
                return (
                  <td key={c} className={cut != null && v > cut ? 'outlier' : ''}
                    style={{ background: st < 0 ? '#f6f8fb' : HEAT_RAMP[st], color: st >= 5 ? '#fff' : '#0f1d2e' }}
                    onMouseMove={(e) => show(e, <TipBody title={`${r} · ${c}`} rows={[['Value', fmt(v, kind)],
                      v != null && (cut != null && v > cut ? ['Outlier', `far above the rest (> ${fmt(cut, kind)})`]
                        : ['Shade', `${fmt(breaks[st][0], kind)}–${fmt(breaks[st][1], kind)}`]),
                      additive && total && v != null ? ['Share of table', `${((v / total) * 100).toFixed(1)}%`] : null]} />)}>
                    {fmt(v, kind)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {breaks.length > 1 && (
        <div className="heat-legend" aria-label="Colour scale">
          <span className="muted small">Lower</span>
          {breaks.map(([lo, hi], i) => (
            <span key={i} className="hl-step" title={`${fmt(lo, kind)} – ${fmt(hi, kind)}`}>
              <i style={{ background: HEAT_RAMP[Math.round((i / Math.max(1, breaks.length - 1)) * ((cut != null ? HEAT_RAMP.length - 2 : HEAT_RAMP.length - 1)))] }} />
              <em>{fmt(lo, kind)}</em>
            </span>
          ))}
          {cut != null && (
            <span className="hl-step out" title={`Outliers: above ${fmt(cut, kind)}`}>
              <i style={{ background: HEAT_RAMP[HEAT_RAMP.length - 1] }} /><em>outlier ≤ {fmt(max, kind)}</em>
            </span>
          )}
          <span className="muted small">Higher</span>
        </div>
      )}
      {tip}
    </div>
  );
}

export function MiniLine({ points = [], kind }) {
  const [hover, setHover] = useState(null);
  const box = useRef(null);
  const [tip, show, hide] = useTip(box);
  const vals = points.map((p) => p.value).filter((v) => v != null);
  if (vals.length < 2) return <Empty text="Not enough points" />;
  const w = 220, h = 70;
  const min = Math.min(...vals), max = Math.max(...vals);
  const px = (i) => (i / (points.length - 1)) * w;
  const py = (v) => h - 6 - ((v - min) / (max - min || 1)) * (h - 12);
  const d = points.map((p, i) => (p.value == null ? null : `${px(i)},${py(p.value)}`)).filter(Boolean);
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const i = Math.max(0, Math.min(points.length - 1, Math.round(((e.clientX - r.left) / r.width) * (points.length - 1))));
    setHover(i);
    show(e, <TipBody title={points[i].label} rows={[['Value', fmt(points[i].value, kind)]]} />);
  };
  return (
    <div className="chart" ref={box}>
      <svg viewBox={`0 0 ${w} ${h}`} className="mini" onMouseMove={onMove} onMouseLeave={() => { setHover(null); hide(); }}>
        <polyline points={d.join(' ')} />
        {hover != null && points[hover]?.value != null && <circle cx={px(hover)} cy={py(points[hover].value)} r="3" className="spark-hover" />}
      </svg>
      {tip}
    </div>
  );
}

export function Empty({ text }) {
  return <div className="empty">{text}</div>;
}

// Snowflake-derived categorical order, validated (dataviz validate_palette.js: lightness, chroma, CVD, normal-vision all PASS).
export const PALETTE = ['#11629E', '#29B5E8', '#E8830C', '#11A39A', '#7D44CF', '#D45B90'];
const OTHER = '#A9B4C2';

/** Donut with legend (share of an additive metric). */
const DONUT_MAX = 6;   // 5 coloured slices + one grey "Other": beyond that colours repeat or blur

/** Keep the largest slices, fold the rest (including any server-side "Other") into one grey slice. */
function foldSlices(raw) {
  const isOther = (s) => /^other\b/i.test(String(s.label));
  const named = raw.filter((s) => !isOther(s));
  const tail = raw.filter(isOther);
  if (named.length + (tail.length ? 1 : 0) <= DONUT_MAX && tail.length <= 1) {
    return raw.map((s) => ({ ...s, other: isOther(s) }));
  }
  const keep = named.slice(0, DONUT_MAX - 1);
  const rest = [...named.slice(DONUT_MAX - 1), ...tail];
  const sum = (k) => rest.reduce((a, s) => (s[k] == null ? a : a + s[k]), 0);
  const members = rest.filter((s) => !isOther(s)).map((s) => s.label);
  const hidden = tail.reduce((a, s) => a + (Number(String(s.label).match(/\((\d+)\)/)?.[1]) || 0), 0);
  const count = members.length + hidden;
  return [...keep.map((s) => ({ ...s, other: false })),
    { label: `Other (${count})`, value: sum('value'), share: rest.some((s) => s.share != null) ? sum('share') : null,
      other: true, members, hidden }];
}

export function Donut({ slices: rawSlices = [], kind, total, centerLabel }) {
  const slices = foldSlices(rawSlices);
  const [hover, setHover] = useState(null);
  const [box, W] = useWidth(400);
  const [tip, show, hide] = useTip(box);
  const R = 78, r = 54, C = 90;
  let a0 = -Math.PI / 2;
  const arcs = slices.map((s, i) => {
    const a1 = a0 + (s.share || 0) * Math.PI * 2;
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const p = (ang, rad) => `${C + rad * Math.cos(ang)},${C + rad * Math.sin(ang)}`;
    const full = (s.share || 0) >= 0.9999;
    const d = full   // a single 100% slice: draw a ring (an arc from a point to itself renders nothing)
      ? `M${C - R},${C} A${R},${R} 0 1 1 ${C + R},${C} A${R},${R} 0 1 1 ${C - R},${C} M${C - r},${C} A${r},${r} 0 1 0 ${C + r},${C} A${r},${r} 0 1 0 ${C - r},${C} Z`
      : `M${p(a0, R)} A${R},${R} 0 ${large} 1 ${p(a1, R)} L${p(a1, r)} A${r},${r} 0 ${large} 0 ${p(a0, r)} Z`;
    a0 = a1;
    return { d, color: s.other ? OTHER : PALETTE[i % PALETTE.length], s, i };
  });
  const h = hover != null ? slices[hover] : null;
  const tipFor = (s) => <TipBody title={s.label} rows={[['Value', fmt(s.value, kind)], ['Share', `${((s.share || 0) * 100).toFixed(1)}%`],
    s.members?.length ? ['Includes', s.members.slice(0, 4).join(', ') + (s.members.length + (s.hidden || 0) > 4 ? ` +${s.members.length + (s.hidden || 0) - 4} more` : '')] : null]} />;
  return (
    <div className={`donut-wrap chart ${W < 420 ? 'stack' : ''}`} ref={box} onMouseLeave={() => { setHover(null); hide(); }}>
      <svg viewBox="0 0 180 180" className="donut">
        {arcs.map((a) => (
          <path key={a.i} d={a.d} fill={a.color} fillRule="evenodd" stroke="#fff" strokeWidth="2" opacity={hover == null || hover === a.i ? 1 : 0.35}
            onMouseMove={(e) => { setHover(a.i); show(e, tipFor(a.s)); }} />
        ))}
        <text x="90" y="86" textAnchor="middle" className="donut-val">{h ? `${((h.share || 0) * 100).toFixed(0)}%` : fmt(total, kind)}</text>
        <text x="90" y="104" textAnchor="middle" className="tick">{h ? String(h.label).slice(0, 16) : centerLabel}</text>
      </svg>
      <div className="donut-legend">
        {slices.map((s, i) => (
          <div key={s.label} className="dl" onMouseMove={(e) => { setHover(i); show(e, tipFor(s)); }}>
            <i style={{ background: s.other ? OTHER : PALETTE[i % PALETTE.length] }} /><span>{s.label}</span>
            <b>{s.share == null ? '' : `${(s.share * 100).toFixed(1)}%`}</b><em>{fmt(s.value, kind)}</em>
          </div>
        ))}
      </div>
      {tip}
    </div>
  );
}

/** Pareto: sorted bars + cumulative share line, 80% guide. */
export function Pareto({ rows = [], kind, height = 250 }) {
  const [box, W] = useWidth();
  const [hover, setHover] = useState(null);
  const [tip, show, hide] = useTip(box);
  if (!rows.length) return <div ref={box}><Empty text="No data." /></div>;
  const pad = { l: 56, r: 40, t: 12, b: 50 };
  const iw = W - pad.l - pad.r, ih = height - pad.t - pad.b;
  const max = Math.max(...rows.map((r) => r.value), 1e-12);
  const ticks = niceTicks(0, max, 4);
  const top = ticks[ticks.length - 1];
  const bw = iw / rows.length;
  const y = (v) => pad.t + ih - (v / top) * ih;
  const yc = (c) => pad.t + ih - c * ih;
  const line = rows.map((r, i) => `${i ? 'L' : 'M'}${pad.l + i * bw + bw / 2},${yc(r.cum_share || 0)}`).join(' ');
  const every = Math.max(1, Math.ceil(rows.length / Math.max(3, Math.floor(iw / 60))));
  return (
    <div className="chart" ref={box}>
      <svg viewBox={`0 0 ${W} ${height}`} role="img" onMouseLeave={() => { setHover(null); hide(); }}>
        {ticks.map((t) => (
          <g key={t}><line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
            <text x={pad.l - 8} y={y(t) + 4} className="tick" textAnchor="end">{fmt(t, kind)}</text></g>
        ))}
        <line x1={pad.l} x2={W - pad.r} y1={yc(0.8)} y2={yc(0.8)} className="line baseline" />
        <text x={W - pad.r + 4} y={yc(0.8) + 4} className="tick">80%</text>
        <text x={W - pad.r + 4} y={yc(1) + 4} className="tick">100%</text>
        {rows.map((r, i) => (
          <g key={i} onMouseMove={(e) => { setHover(i); show(e, <TipBody title={`#${i + 1} ${r.label}`} rows={[['Value', fmt(r.value, kind)],
            ['Cumulative share', `${((r.cum_share || 0) * 100).toFixed(1)}%`]]} />); }}>
            <rect x={pad.l + i * bw + bw * 0.12} width={bw * 0.76} y={y(Math.max(0, r.value))}
              height={Math.max(1, pad.t + ih - y(Math.max(0, r.value)))} rx="3" className={`wf total ${hover === i ? 'hl' : ''}`} />
            {(i % every === 0) && (
              <text x={pad.l + i * bw + bw / 2} y={height - 34} className="tick" textAnchor="end"
                transform={`rotate(-35 ${pad.l + i * bw + bw / 2} ${height - 34})`}>{String(r.label).slice(0, 14)}</text>
            )}
          </g>
        ))}
        <path d={line} className="line forecast" />
      </svg>
      {tip}
      <div className="legend">
        <span><i className="sw actual" />Value</span><span><i className="sw forecast" />Cumulative share</span>
      </div>
    </div>
  );
}

/** Greedy label placement for scatter points: try right, left, above, below; skip a label that would
 *  overlap another label or a point (the tooltip still names it). Largest-|y| points are placed first. */
function placeLabels(points, x, y, area) {
  if (points.length > 24) return [];
  const CW = 6.1, H = 12, R = 6;
  const dots = points.map((p) => ({ cx: x(p.x), cy: y(p.y) }));
  const boxes = [];
  const hit = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
  const order = points.map((p, i) => i).sort((a, b) => Math.abs(points[b].y) - Math.abs(points[a].y));
  const out = [];
  order.forEach((i) => {
    const text = String(points[i].label).slice(0, 16);
    const w = text.length * CW, { cx, cy } = dots[i];
    const cands = [
      { x: cx + 8, y: cy + 4, anchor: 'start', b: { x0: cx + 7, x1: cx + 9 + w, y0: cy - 7, y1: cy + 5 } },
      { x: cx - 8, y: cy + 4, anchor: 'end', b: { x0: cx - 9 - w, x1: cx - 7, y0: cy - 7, y1: cy + 5 } },
      { x: cx, y: cy - 9, anchor: 'middle', b: { x0: cx - w / 2, x1: cx + w / 2, y0: cy - 9 - H + 2, y1: cy - 7 } },
      { x: cx, y: cy + 17, anchor: 'middle', b: { x0: cx - w / 2, x1: cx + w / 2, y0: cy + 7, y1: cy + 7 + H } },
    ];
    const ok = cands.find((c) => c.b.x0 >= area.l && c.b.x1 <= area.r + 4 && c.b.y0 >= area.t - 2 && c.b.y1 <= area.b + 2
      && !boxes.some((b) => hit(b, c.b))
      && !dots.some((d, j) => j !== i && hit(c.b, { x0: d.cx - R, x1: d.cx + R, y0: d.cy - R, y1: d.cy + R })));
    if (ok) { boxes.push(ok.b); out.push({ i, text, x: ok.x, y: ok.y, anchor: ok.anchor }); }
  });
  return out;
}

/** Scatter of two metrics across dimension values; median guides. */
export function Scatter({ points = [], xKind, yKind, xLabel, yLabel, height = 260 }) {
  const [box, W] = useWidth();
  const [hover, setHover] = useState(null);
  const [tip, show, hide] = useTip(box);
  if (!points.length) return <div ref={box}><Empty text="No data." /></div>;
  const pad = { l: 60, r: 14, t: 12, b: 40 };
  const iw = W - pad.l - pad.r, ih = height - pad.t - pad.b;
  const span = (arr) => { const lo = Math.min(...arr), hi = Math.max(...arr); const pd = (hi - lo || Math.abs(hi) || 1) * 0.12; return [lo - pd, hi + pd]; };
  const [x0, x1] = span(points.map((p) => p.x));
  const [y0, y1] = span(points.map((p) => p.y));
  const xs = niceTicks(x0, x1, 4);
  const ys = niceTicks(y0, y1, 4);
  const x = (v) => pad.l + ((v - xs[0]) / (xs[xs.length - 1] - xs[0] || 1)) * iw;
  const y = (v) => pad.t + ih - ((v - ys[0]) / (ys[ys.length - 1] - ys[0] || 1)) * ih;
  const med = (arr) => { const s = [...arr].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
  const mx = med(points.map((p) => p.x)), my = med(points.map((p) => p.y));
  return (
    <div className="chart" ref={box}>
      <svg viewBox={`0 0 ${W} ${height}`} role="img" onMouseLeave={() => { setHover(null); hide(); }}>
        {ys.map((t) => <g key={`y${t}`}><line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
          <text x={pad.l - 8} y={y(t) + 4} className="tick" textAnchor="end">{fmt(t, yKind)}</text></g>)}
        {xs.map((t) => <text key={`x${t}`} x={x(t)} y={height - 22} className="tick" textAnchor="middle">{fmt(t, xKind)}</text>)}
        <line x1={x(mx)} x2={x(mx)} y1={pad.t} y2={pad.t + ih} className="line baseline" />
        <line x1={pad.l} x2={W - pad.r} y1={y(my)} y2={y(my)} className="line baseline" />
        {points.map((p, i) => (
          <circle key={i} cx={x(p.x)} cy={y(p.y)} r={hover === i ? 7 : 5} className={`pt ${p.y < 0 ? 'neg' : ''}`}
            onMouseMove={(e) => { setHover(i); show(e, <TipBody title={p.label} rows={[[xLabel, fmt(p.x, xKind)], [yLabel, fmt(p.y, yKind)]]} />); }} />
        ))}
        {placeLabels(points, x, y, { l: pad.l, r: W - pad.r, t: pad.t, b: pad.t + ih }).map((L) => (
          <text key={`l${L.i}`} x={L.x} y={L.y} className="tick pt-label" textAnchor={L.anchor}>{L.text}</text>
        ))}
        <text x={W - pad.r} y={height - 6} className="tick" textAnchor="end">{xLabel} →</text>
      </svg>
      {tip}
      <div className="legend"><span className="muted small">↑ {yLabel} · dashed lines = medians</span></div>
    </div>
  );
}

/** Grouped horizontal bars: current / prior / prior year. */
export function GroupedBars({ rows = [], kind, labels = [], inverse = false }) {
  const good = (c) => (c == null || c === 0 ? '' : (c > 0) !== inverse ? 'up' : 'down');
  const box = useRef(null);
  const [tip, show, hide] = useTip(box);
  const max = Math.max(...rows.flatMap((r) => [r.current || 0, r.prior || 0, r.yoy || 0]), 1e-12);
  const keys = ['current', 'prior', 'yoy'];
  return (
    <div className="gbars chart" ref={box} onMouseLeave={hide}>
      <div className="legend">{labels.map((l, i) => <span key={l}><i className={`sw g${i}`} />{l}</span>)}</div>
      {rows.map((r) => (
        <div className="gbar" key={r.segment} onMouseMove={(e) => show(e, <TipBody title={r.segment} rows={[
          [labels[0], fmt(r.current, kind)], [labels[1], fmt(r.prior, kind)], [labels[2], fmt(r.yoy, kind)],
          ['vs previous', pctTxt(r.change), good(r.change)], ['vs last year', pctTxt(r.yoy_change), good(r.yoy_change)]]} />)}>
          <span className="bar-label">{r.segment}</span>
          <div className="gstack">
            {keys.map((k, i) => (
              <div className="gline" key={k}>
                <i className={`g${i}`} style={{ width: `${Math.max(0, (r[k] || 0) / max) * 100}%` }} />
                {i === 0 && <em>{fmt(r[k], kind)}</em>}
              </div>
            ))}
          </div>
          <span className={`bar-delta ${good(r.yoy_change)}`}>
            {r.yoy_change == null ? '' : `${r.yoy_change > 0 ? '▲' : '▼'} ${(Math.abs(r.yoy_change) * 100).toFixed(0)}% YoY`}
          </span>
        </div>
      ))}
      {tip}
    </div>
  );
}

/** Several aligned series over the same x labels: actual (solid + area), plan (dark dashed), ref (grey),
 *  forecast (purple dashed + band). `nowIndex` draws a "now" guide. Used by the YTD trajectory and today's pace. */
const SERIES_STYLE = {
  actual: { stroke: '#1872C4', width: 2.6, dash: '' },
  plan: { stroke: '#0b2440', width: 1.6, dash: '3 4' },
  ref: { stroke: '#A9B4C2', width: 1.8, dash: '' },
  forecast: { stroke: '#7D44CF', width: 2.2, dash: '6 4' },
};
export function SeriesChart({ labels = [], series = [], band, kind, nowIndex, nowLabel = 'now', height = 250 }) {
  const [box, W] = useWidth();
  const [hover, setHover] = useState(null);
  const [tip, show, hide] = useTip(box);
  const gid = useGid('sc');
  const vals = series.flatMap((s) => s.values.filter((v) => v != null));
  if (band) vals.push(...band.lower.filter((v) => v != null), ...band.upper.filter((v) => v != null));
  if (!vals.length || !labels.length) return <div ref={box}><Empty text="No data points yet." /></div>;
  const ticks = niceTicks(Math.min(0, ...vals), Math.max(...vals), 4);
  const y0 = ticks[0], y1 = ticks[ticks.length - 1];
  const pad = { l: 58, r: 14, t: 14, b: 28 };
  const iw = W - pad.l - pad.r, ih = height - pad.t - pad.b;
  const n = labels.length;
  const x = (i) => pad.l + (n <= 1 ? iw / 2 : (i * iw) / (n - 1));
  const y = (v) => pad.t + ih - ((v - y0) / (y1 - y0 || 1)) * ih;
  const path = (vs) => {
    let d = '', pen = false;
    vs.forEach((v, i) => { if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i)},${y(v)} `; pen = true; });
    return d;
  };
  const actual = series.find((s) => s.style === 'actual');
  const aPts = actual ? actual.values.map((v, i) => (v == null ? null : [x(i), y(v)])).filter(Boolean) : [];
  const bandPts = band ? (() => {
    const idx = band.upper.map((v, i) => (v == null || band.lower[i] == null ? null : i)).filter((i) => i != null);
    return idx.length > 1 ? [...idx.map((i) => `${x(i)},${y(band.upper[i])}`), ...idx.slice().reverse().map((i) => `${x(i)},${y(band.lower[i])}`)].join(' ') : null;
  })() : null;
  const every = Math.max(1, Math.ceil(n / Math.max(3, Math.floor(iw / 64))));
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    const i = Math.max(0, Math.min(n - 1, Math.round(((px - pad.l) / iw) * (n - 1))));
    setHover(i);
    const rows = series.filter((s) => s.values[i] != null).map((s) => [s.label, fmt(s.values[i], kind)]);
    if (actual && actual.values[i] != null) {
      const other = series.find((s) => s.style === 'plan' && s.values[i] != null);
      if (other && other.values[i]) {
        const d = (actual.values[i] - other.values[i]) / Math.abs(other.values[i]);
        rows.push([`vs ${other.label.toLowerCase()}`, `${d > 0 ? '+' : ''}${(d * 100).toFixed(1)}%`, d >= 0 ? 'up' : 'down']);
      }
    }
    if (band && band.lower[i] != null && i !== nowIndex) rows.push(['80% range', `${fmt(band.lower[i], kind)} – ${fmt(band.upper[i], kind)}`]);
    show(e, <TipBody title={labels[i]} rows={rows} />);
  };
  return (
    <div className="chart" ref={box}>
      <svg viewBox={`0 0 ${W} ${height}`} role="img" onMouseMove={onMove} onMouseLeave={() => { setHover(null); hide(); }}>
        {ticks.map((t) => (
          <g key={t}><line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
            <text x={pad.l - 8} y={y(t) + 4} className="tick" textAnchor="end">{fmt(t, kind)}</text></g>
        ))}
        {labels.map((l, i) => ((i % every === 0 && n - 1 - i >= every / 2) || i === n - 1) && (
          <text key={i} x={x(i)} y={height - 8} className="tick" textAnchor={i === n - 1 ? 'end' : i === 0 ? 'start' : 'middle'}>{l}</text>
        ))}
        {bandPts && <polygon points={bandPts} className="band" />}
        <defs><linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#29B5E8" stopOpacity="0.26" /><stop offset="100%" stopColor="#29B5E8" stopOpacity="0" /></linearGradient></defs>
        {aPts.length > 1 && <path d={`M${aPts[0][0]},${pad.t + ih} ${aPts.map((q) => `L${q[0]},${q[1]}`).join(' ')} L${aPts[aPts.length - 1][0]},${pad.t + ih} Z`} fill={`url(#${gid})`} />}
        {series.filter((s) => s.style !== 'actual').map((s) => {
          const st = SERIES_STYLE[s.style] || SERIES_STYLE.ref;
          return <path key={s.key} d={path(s.values)} fill="none" stroke={st.stroke} strokeWidth={st.width} strokeDasharray={st.dash} />;
        })}
        {actual && <path d={path(actual.values)} fill="none" stroke={SERIES_STYLE.actual.stroke} strokeWidth={SERIES_STYLE.actual.width} strokeLinejoin="round" />}
        {nowIndex != null && nowIndex < n - 1 && (
          <g className="now-guide"><line x1={x(nowIndex)} x2={x(nowIndex)} y1={pad.t} y2={pad.t + ih} />
            <text x={x(nowIndex) + (x(nowIndex) > W - 110 ? -4 : 4)} y={pad.t + 10} className="tick now"
              textAnchor={x(nowIndex) > W - 110 ? 'end' : 'start'}>{nowLabel}</text></g>
        )}
        {actual && nowIndex != null && actual.values[nowIndex] != null && hover == null && (
          <circle cx={x(nowIndex)} cy={y(actual.values[nowIndex])} r="4.5" className="dot end" />
        )}
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={pad.t} y2={pad.t + ih} className="cursor" />}
        {hover != null && series.map((s) => s.values[hover] != null && (
          <circle key={s.key} cx={x(hover)} cy={y(s.values[hover])} r="3.5" fill={(SERIES_STYLE[s.style] || SERIES_STYLE.ref).stroke} stroke="#fff" strokeWidth="1.5" />
        ))}
      </svg>
      {tip}
      <div className="legend slegend">
        {series.map((s) => {
          const st = SERIES_STYLE[s.style] || SERIES_STYLE.ref;
          return <span key={s.key}><svg width="22" height="8"><line x1="0" x2="22" y1="4" y2="4" stroke={st.stroke} strokeWidth="2.4" strokeDasharray={st.dash} /></svg>{s.label}</span>;
        })}
      </div>
    </div>
  );
}

/** Bullet bar (Stephen Few): value bar against a target tick. Positive values use a 0..max scale; when the
 * value or target is negative (e.g. a variance) the scale spans min..max with a zero line, and the bar grows
 * from zero. Everything is clamped to the track so a bar can never spill out of its card. */
export function Bullet({ value, target, good }) {
  if (value == null || !Number.isFinite(value)) return null;
  const t = target != null && Number.isFinite(target) ? target : null;
  const clamp = (x) => Math.max(0, Math.min(100, x));
  const lo = Math.min(0, value, t ?? 0);
  const hi = Math.max(0, value, t ?? 0);
  const span = (hi - lo) * 1.12 || 1;
  const pos = (x) => clamp(((x - lo) / span) * 100);
  const zero = pos(0);
  const v = pos(value);
  const left = Math.min(zero, v);
  const width = Math.abs(v - zero);
  return (
    <div className="bullet" title={t != null ? `Bar = actual, tick = target (${t.toLocaleString()})` : ''}>
      {lo < 0 && <b className="zero" style={{ left: `${zero}%` }} />}
      <i className={good === false ? 'off' : ''} style={{ left: `${left}%`, width: `${width}%` }} />
      {t != null && <s style={{ left: `calc(${pos(t)}% - 1px)` }} />}
    </div>
  );
}
