import type { CSSProperties, ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, Loader2 } from 'lucide-react';

// ── Formatting helpers ─────────────────────────────────────────────────────────
export function fmtDate(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });
}

export function fmtDateTime(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function fmtNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return Number.isInteger(value) ? String(value) : value.toFixed(digits);
}

export function fmtDelta(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value > 0 ? '+' : ''}${fmtNumber(value, 2)}`;
}

export function initials(name?: string | null): string {
  if (!name) return 'MS';
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

/** Human label for a report-parameter status. */
export function statusLabel(status: string): string {
  switch (status) {
    case 'within_range':
      return 'In range';
    case 'below_range':
      return 'Below range';
    case 'above_range':
      return 'Above range';
    case 'no_reference_range':
      return 'No reference';
    default:
      return status;
  }
}

/** Tone used by <Tag> for a report-parameter status. */
export function statusTone(status: string): string {
  switch (status) {
    case 'within_range':
      return 'green';
    case 'below_range':
      return 'blue';
    case 'above_range':
      return 'amber';
    default:
      return 'neutral';
  }
}

// ── Primitives ─────────────────────────────────────────────────────────────────
export function Card({
  children,
  className = '',
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  return <section className={`card ${className}`} style={style}>{children}</section>;
}

export function Heading({
  eyebrow,
  title,
  desc,
  action,
}: {
  eyebrow?: string;
  title: string;
  desc?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {desc && <p>{desc}</p>}
      </div>
      {action}
    </div>
  );
}

export function Tag({ children, tone = 'teal' }: { children: ReactNode; tone?: string }) {
  return <span className={`tag ${tone}`}>{children}</span>;
}

/** Marks data that is seeded/demo rather than entered by the signed-in user. */
export function DemoTag() {
  return (
    <span className="tag amber" title="Seeded demo record — not a real clinical entry">
      DEMO
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  type = 'button',
  disabled,
  full,
  title,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  type?: 'button' | 'submit';
  disabled?: boolean;
  full?: boolean;
  title?: string;
}) {
  return (
    <button
      type={type}
      className={`btn ${variant}${full ? ' full' : ''}`}
      onClick={onClick}
      disabled={disabled}
      title={title}
    >
      {children}
    </button>
  );
}

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading-row" role="status" aria-live="polite">
      <Loader2 size={16} className="spin" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={13} style={{ verticalAlign: '-2px', marginRight: 6 }} />
      {message}
    </div>
  );
}

export function Notice({
  children,
  tone = 'teal',
}: {
  children: ReactNode;
  tone?: 'teal' | 'amber';
}) {
  return (
    <div className={`notice${tone === 'amber' ? ' amber' : ''}`}>
      <Info size={13} style={{ flexShrink: 0, marginTop: 1 }} />
      <div>{children}</div>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  desc,
  action,
}: {
  icon: ReactNode;
  title: string;
  desc?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div>{icon}</div>
      <b>{title}</b>
      {desc && <p className="muted">{desc}</p>}
      {action}
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label>
      {label}
      {children}
      {hint && <small className="small-note">{hint}</small>}
    </label>
  );
}

export function SuccessNote({ children }: { children: ReactNode }) {
  return (
    <div className="notice">
      <CheckCircle2 size={13} style={{ flexShrink: 0, marginTop: 1 }} />
      <div>{children}</div>
    </div>
  );
}

/** Small inline statistic used across dashboard/admin cards. */
export function StatBlock({
  icon,
  label,
  value,
  sub,
  tone = 'teal',
}: {
  icon: ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  tone?: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>{icon}</div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
        {sub && <span className="stat-arrow">{sub}</span>}
      </div>
    </div>
  );
}
