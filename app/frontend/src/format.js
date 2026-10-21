export function fmt(v, kind = 'number') {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  if (kind === 'percent') return `${(v * 100).toFixed(1)}%`;
  const a = Math.abs(v);
  let s;
  if (a >= 1e9) s = `${(v / 1e9).toFixed(1)}B`;
  else if (a >= 1e6) s = `${(v / 1e6).toFixed(1)}M`;
  else if (a >= 1e3) s = `${(v / 1e3).toFixed(1)}K`;
  else if (a >= 100 || Number.isInteger(v)) s = Math.round(v).toLocaleString();
  else s = v.toFixed(2);
  return kind === 'currency' ? (v < 0 ? `-$${s.replace('-', '')}` : `$${s}`) : s;
}

export function pct(v, digits = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const s = (v * 100).toFixed(digits);
  return `${v > 0 ? '+' : ''}${s}%`;
}

export function tone(v, invert = false) {
  if (v === null || v === undefined || Math.abs(v) < 0.0005) return 'flat';
  return (v > 0) !== invert ? 'up' : 'down';
}

export const label = (id = '') => id.split('.').pop().replace(/_/g, ' ').toLowerCase()
  .replace(/\b\w/g, (c) => c.toUpperCase());

export const AUDIENCE_LABELS = {
  executives: 'Executives',
  managers: 'Managers',
  daily_operations: 'Operations',
  weekly_business_review: 'Weekly business review',
};

export const CAP_LABELS = {
  comparable_time_series: 'Comparable time series',
  enterprise_scope_authorized: 'Enterprise scope authorized',
  manager_scope_authorized: 'Manager scope authorized',
  operating_scope_authorized: 'Operating scope authorized',
  stable_segment_hierarchy: 'Stable segment hierarchy',
  period_complete: 'Complete period',
  fresh_data: 'Fresh data (≤ 2 days)',
  event_time: 'Event time',
  comparable_intraday_series: 'Intraday series',
  target: 'Target / baseline',
  forecast_versioned: 'Snowflake ML forecast',
  reconciled_driver_bridge: 'Reconciled driver bridge',
  action_tracking: 'Decision tracking',
  plan_versioned: 'Versioned plan',
  risk_metadata_current: 'Risk register',
};
