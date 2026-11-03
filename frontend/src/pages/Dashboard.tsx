import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowUpRight,
  Bell,
  CalendarDays,
  ChevronRight,
  FileText,
  HeartPulse,
  MessageCircle,
  Pill,
  Plus,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  Watch,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { useAsync } from '../hooks/useAsync';
import {
  analyticsApi,
  appointmentsApi,
  doctorsApi,
  metaApi,
  notificationsApi,
  reportsApi,
} from '../services/api';
import type { Doctor, MetricSummary } from '../types';
import {
  Card,
  DemoTag,
  EmptyState,
  ErrorBox,
  Heading,
  Spinner,
  StatBlock,
  Tag,
  fmtDate,
  fmtDateTime,
  fmtDelta,
  fmtNumber,
} from '../components/ui';

function MetricChart({ metric, accent }: { metric: MetricSummary; accent: string }) {
  const data = metric.series.map((p) => ({
    label: new Date(p.recorded_at).toLocaleDateString(undefined, { day: '2-digit', month: 'short' }),
    value: p.value,
  }));

  if (data.length < 2) {
    return (
      <div className="chart chart-placeholder">
        <span className="small-note">
          Log at least two {metric.metric} readings to render a trend.
        </span>
      </div>
    );
  }

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 6, left: -22, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${metric.metric}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity={0.35} />
              <stop offset="100%" stopColor={accent} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--muted)' }} stroke="var(--line)" />
          <YAxis tick={{ fontSize: 9, fill: 'var(--muted)' }} stroke="var(--line)" />
          <Tooltip
            contentStyle={{
              fontSize: 11,
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: 'var(--panel)',
              color: 'var(--ink)',
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={accent}
            strokeWidth={2}
            fill={`url(#grad-${metric.metric})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();

  const summary = useAsync(() => analyticsApi.summary().then((r) => r.data), []);
  const health = useAsync(() => analyticsApi.healthSummary().then((r) => r.data), []);
  const trends = useAsync(() => reportsApi.trends().then((r) => r.data), []);
  const appointments = useAsync(() => appointmentsApi.list().then((r) => r.data), []);
  const doctors = useAsync(() => doctorsApi.directory().then((r) => r.data), []);
  const notifications = useAsync(() => notificationsApi.list(true).then((r) => r.data), []);
  const meta = useAsync(() => metaApi.get().then((r) => r.data), []);

  const stats = summary.data;
  const metricList = health.data?.metrics ?? [];
  const trendPoints = trends.data?.points ?? [];

  const upcoming = (appointments.data ?? [])
    .filter((a) => a.status === 'scheduled' && new Date(a.appointment_at) >= new Date())
    .sort((a, b) => +new Date(a.appointment_at) - +new Date(b.appointment_at))
    .slice(0, 4);

  const featured: Doctor[] = (doctors.data?.doctors ?? []).slice(0, 4);

  const flaggedTotal = stats?.flagged_parameters ?? 0;
  const totalParams = trendPoints.reduce((sum, p) => sum + p.total, 0);
  const inRangePct = totalParams
    ? Math.round((trendPoints.reduce((s, p) => s + p.within_range, 0) / totalParams) * 100)
    : 0;

  const aiLive = meta.data?.ai?.live ?? false;

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">PATIENT WORKSPACE</div>
          <h1>
            Welcome back, <span>{user?.name?.split(' ')[0] ?? 'there'}</span>
          </h1>
          <p>Live vitals, report analysis and care coordination in one place.</p>
        </div>
        <div className="date-pill">
          <CalendarDays size={14} />
          {new Date().toLocaleDateString(undefined, {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-card">
          <div className="hero-content">
            <div className="eyebrow" style={{ color: '#D7B879' }}>
              HEALTH INTELLIGENCE
            </div>
            <h2>Every lab value, decoded.</h2>
            <p>
              Upload a PDF or a photo of your report. MediSense extracts each parameter, compares it
              with its reference range and explains what moved since last time.
            </p>
            <Link to="/reports" className="hero-btn">
              <FileText size={15} /> Analyse a report <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <img className="hero-heart" src="/images/anatomical-heart.png" alt="" />
            <div className="orbit" />
            <div className="orbit orbit-b" />
            <div className="float-chip chip-one">
              <HeartPulse size={13} /> {metricList.length} metrics tracked
            </div>
            <div className="float-chip chip-two">
              <FileText size={13} /> {stats?.reports ?? 0} reports analysed
            </div>
          </div>
        </div>

        <Card className="risk-card">
          <div className="card-head">
            <div>
              <b>Report integrity</b>
              <small className="small-note">Share of parameters inside reference range</small>
            </div>
            <Tag tone={inRangePct >= 80 ? 'green' : inRangePct >= 60 ? 'amber' : 'violet'}>
              {totalParams ? (inRangePct >= 80 ? 'Good' : inRangePct >= 60 ? 'Watch' : 'Review') : 'No data'}
            </Tag>
          </div>
          <div className="score-wrap">
            <div
              className="score-ring"
              style={{
                background: `conic-gradient(#A98245 0 ${inRangePct}%, var(--line) ${inRangePct}%)`,
              }}
            >
              <div>
                <b>{totalParams ? `${inRangePct}%` : '—'}</b>
                <small>IN RANGE</small>
              </div>
            </div>
            <div>
              <div className="metric-line">
                <span>
                  <Activity size={13} /> Flagged values
                </span>
                <b>{flaggedTotal}</b>
              </div>
              <div className="metric-line">
                <span>
                  <FileText size={13} /> Parameters parsed
                </span>
                <b>{totalParams}</b>
              </div>
              <div className="metric-line">
                <span>
                  <Watch size={13} /> Devices linked
                </span>
                <b>{stats?.wearables ?? 0}</b>
              </div>
            </div>
          </div>
          <p className="demo-caption">
            Calculated from your own analysed reports ({trendPoints.length} on file). Informational
            only — not a diagnosis.
          </p>
        </Card>
      </div>

      <div className="quick-grid">
        {[
          { to: '/reports', icon: <FileText size={16} />, label: 'Analyse report' },
          { to: '/assistant', icon: <MessageCircle size={16} />, label: 'Ask AI' },
          { to: '/appointments', icon: <CalendarDays size={16} />, label: 'Book visit' },
          { to: '/medications', icon: <Pill size={16} />, label: 'Medications' },
          { to: '/anatomy', icon: <Stethoscope size={16} />, label: '3D anatomy' },
        ].map((q) => (
          <Link key={q.to} to={q.to} className="quick-card">
            {q.icon}
            {q.label}
            <ChevronRight size={13} />
          </Link>
        ))}
      </div>

      <div className="stat-grid">
        <StatBlock
          icon={<FileText size={17} />}
          label="Reports analysed"
          value={stats?.reports ?? 0}
          tone="teal"
          sub={`${flaggedTotal} flagged`}
        />
        <StatBlock
          icon={<CalendarDays size={17} />}
          label="Upcoming visits"
          value={stats?.upcoming_appointments ?? 0}
          tone="blue"
          sub={`${stats?.appointments ?? 0} total`}
        />
        <StatBlock
          icon={<Pill size={17} />}
          label="Active medications"
          value={stats?.active_medications ?? 0}
          tone="amber"
          sub="Your saved medication list"
        />
        <StatBlock
          icon={<Bell size={17} />}
          label="Unread alerts"
          value={stats?.unread_notifications ?? 0}
          tone="violet"
          sub="Notifications"
        />
      </div>

      {(summary.error || health.error || trends.error) && (
        <ErrorBox message={summary.error || health.error || trends.error || ''} />
      )}

      <div className="dashboard-grid">
        <Card>
          <div className="card-head">
            <div>
              <b>Vitals &amp; metrics</b>
              <small className="small-note">Recorded readings from your health metrics log</small>
            </div>
            <Link to="/insights" className="text-btn">
              Full insights <ArrowUpRight size={13} />
            </Link>
          </div>

          {health.loading && <Spinner label="Loading metrics…" />}
          {!health.loading && metricList.length === 0 && (
            <EmptyState
              icon={<Activity size={20} />}
              title="No metrics recorded yet"
              desc="Log blood pressure, weight, glucose or any metric to unlock trends."
              action={
                <Link to="/insights" className="btn primary" style={{ marginTop: 10 }}>
                  <Plus size={14} /> Add a reading
                </Link>
              }
            />
          )}

          {metricList.length > 0 && (
            <>
              <MetricChart metric={metricList[0]} accent="#A98245" />
              <div className="chart-legend">
                {metricList.slice(0, 3).map((m) => (
                  <span key={m.metric}>
                    {m.metric} · {fmtNumber(m.latest)} {m.unit}
                    {m.delta !== null && (
                      <em style={{ fontStyle: 'normal', color: m.delta > 0 ? '#C77B63' : '#8E6932' }}>
                        {' '}
                        ({fmtDelta(m.delta)})
                      </em>
                    )}
                  </span>
                ))}
              </div>
            </>
          )}
        </Card>

        <Card>
          <div className="card-head">
            <div>
              <b>Recent reports</b>
              <small className="small-note">Parsed parameters per report</small>
            </div>
            <Link to="/reports" className="text-btn">
              All <ArrowUpRight size={13} />
            </Link>
          </div>

          {trends.loading && <Spinner label="Loading reports…" />}
          {!trends.loading && trendPoints.length === 0 && (
            <EmptyState icon={<FileText size={20} />} title="No reports yet" desc="Upload a PDF or photo to begin." />
          )}
          {trendPoints.length > 0 && (
            <div className="chart tall-sm">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={trendPoints.slice(-6).map((p) => ({
                    name: fmtDate(p.created_at),
                    inRange: p.within_range,
                    flagged: p.flagged,
                  }))}
                  margin={{ top: 8, right: 6, left: -24, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--muted)' }} stroke="var(--line)" />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--muted)' }} stroke="var(--line)" allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      fontSize: 11,
                      borderRadius: 8,
                      border: '1px solid var(--line)',
                      background: 'var(--panel)',
                      color: 'var(--ink)',
                    }}
                  />
                  <Bar dataKey="inRange" stackId="a" fill="#A98245" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="flagged" stackId="a" fill="#C77B63" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="chart-legend">
            <span>
              <i className="dot teal-dot" /> In range
            </span>
            <span>
              <i className="dot amber" /> Flagged
            </span>
          </div>
        </Card>
      </div>

      <div className="bottom-grid">
        <Card>
          <div className="card-head">
            <div>
              <b>Upcoming appointments</b>
              <small className="small-note">Scheduled visits from your care plan</small>
            </div>
            <Link to="/appointments" className="text-btn">
              Manage <ArrowUpRight size={13} />
            </Link>
          </div>
          {appointments.loading && <Spinner label="Loading appointments…" />}
          {!appointments.loading && upcoming.length === 0 && (
            <EmptyState
              icon={<CalendarDays size={18} />}
              title="Nothing scheduled"
              desc="Browse the directory to book a consultation."
              action={
                <Link to="/doctors" className="btn primary" style={{ marginTop: 10 }}>
                  Find a doctor
                </Link>
              }
            />
          )}
          {upcoming.map((a) => (
            <div className="list-row" key={a.id}>
              <div className="file-icon">
                <CalendarDays size={16} />
              </div>
              <div>
                <b>{a.doctor_name}</b>
                <small>
                  {a.specialty} · {fmtDateTime(a.appointment_at)}
                </small>
              </div>
              <Tag tone="blue">{a.status}</Tag>
            </div>
          ))}
        </Card>

        <Card>
          <div className="card-head">
            <div>
              <b>Assistant &amp; platform</b>
              <small className="small-note">Live integration status</small>
            </div>
            <Sparkles size={15} />
          </div>

          <div className="insight">
            <div className="insight-icon">
              <MessageCircle size={15} />
            </div>
            <div>
              <b>AI assistant {aiLive ? 'live' : 'in demo mode'}</b>
              <small>
                {meta.data?.ai?.detail ??
                  (aiLive
                    ? `Connected to ${meta.data?.ai?.provider ?? 'a configured provider'}.`
                    : 'No provider key configured — replies come from the built-in educational engine and are labelled as such.')}
              </small>
            </div>
          </div>

          <div className="insight">
            <div className="insight-icon violet">
              <ShieldCheck size={15} />
            </div>
            <div>
              <b>OCR {meta.data?.ocr?.available ? 'available' : 'unavailable'}</b>
              <small>
                {meta.data?.ocr?.available
                  ? `${meta.data.ocr.engine} extracts text from scans and images.`
                  : 'Scanned-image text extraction needs the OCR extras; digital PDFs still work.'}
              </small>
            </div>
          </div>

          {(notifications.data ?? []).slice(0, 2).map((n) => (
            <div className="insight" key={n.id}>
              <div className="insight-icon">
                <Bell size={15} />
              </div>
              <div>
                <b>{n.title}</b>
                <small>{n.message}</small>
              </div>
            </div>
          ))}

          {notifications.data?.length === 0 && (
            <p className="small-note" style={{ marginTop: 10 }}>
              You&apos;re all caught up — no unread notifications.
            </p>
          )}
        </Card>
      </div>

      <Card>
        <div className="card-head doctor-section-head">
          <div>
            <b className="doctor-section-title">Recommended specialists</b>
            <small className="small-note">
              Directory entries {doctors.data?.doctors.some((d) => d.is_demo) ? '— seeded demo profiles labelled DEMO' : ''}
            </small>
          </div>
          <Link to="/doctors" className="text-btn">
            Directory <ArrowUpRight size={13} />
          </Link>
        </div>
        {doctors.loading && <Spinner label="Loading directory…" />}
        {!doctors.loading && featured.length === 0 && (
          <EmptyState icon={<Stethoscope size={18} />} title="Directory is empty" desc="An administrator can add profiles." />
        )}
        <div className="doctor-cards">
          {featured.map((d) => (
            <div className="doctor-card" key={d.id}>
              <div className="doctor-row">
                {d.image ? (
                  <img src={d.image} alt={d.name} loading="lazy" />
                ) : (
                  <div className="file-icon">
                    <Stethoscope size={16} />
                  </div>
                )}
                <div>
                  <b>{d.name}</b>
                  <small>
                    {d.specialty} · {d.experience || 'Experience n/a'}
                  </small>
                </div>
                {d.is_demo && <DemoTag />}
              </div>
              <div className="hospital-name">{d.hospital || 'Hospital not listed'}</div>
              <div className="doctor-meta">
                <Tag tone="green">★ {fmtNumber(d.rating, 1)}</Tag>
                <Tag tone="neutral">₹{fmtNumber(d.consultation_fee, 0)}</Tag>
              </div>
              <Link to="/appointments" className="btn secondary full">
                Book appointment
              </Link>
            </div>
          ))}
        </div>
      </Card>

      <p className="small-note" style={{ marginTop: 18, display: 'flex', gap: 6, alignItems: 'center' }}>
        {metricList[0]?.delta !== null && metricList[0]?.delta !== undefined ? (
          metricList[0].delta >= 0 ? (
            <TrendingUp size={12} />
          ) : (
            <TrendingDown size={12} />
          )
        ) : (
          <Activity size={12} />
        )}
        MediSense offers informational analysis, not medical advice. Always confirm findings with a
        licensed clinician.
      </p>
    </>
  );
}
