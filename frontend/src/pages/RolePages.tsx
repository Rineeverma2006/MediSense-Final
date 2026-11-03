import { useEffect, useState } from 'react';
import { Activity, CalendarDays, FileText, ShieldCheck, Users } from 'lucide-react';
import { adminApi, apiError, doctorsApi } from '../services/api';
import type { AdminStats, AdminUser, DoctorAppointment, DoctorStats } from '../types';
import { Card, EmptyState, ErrorBox, Heading, Spinner, fmtDateTime } from '../components/ui';

export function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState('');
  useEffect(() => { Promise.all([adminApi.stats(), adminApi.users()]).then(([s, u]) => { setStats(s.data); setUsers(u.data); }).catch(e => setError(apiError(e))); }, []);
  return <>
    <Heading eyebrow="PLATFORM ADMIN" title="Administration" desc="Aggregate platform status and account directory. Protected by server-side admin authorization." />
    {error && <ErrorBox message={error} />}
    {!stats && !error ? <Spinner label="Loading administration overview…"/> : stats && <>
      <div className="stat-grid">
        {[[Users, 'Users', stats.users], [FileText, 'Reports', stats.reports], [CalendarDays, 'Appointments', stats.appointments], [Activity, 'Open support tickets', stats.open_tickets]].map(([Icon, label, value]: any) => <Card className="stat-card" key={label}><Icon/><div><small>{label}</small><strong>{value}</strong></div></Card>)}
      </div>
      <Card style={{ marginTop: 16 }}><div className="card-head"><h3>Accounts</h3><ShieldCheck size={18}/></div>
        {users.length ? <div className="table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th></tr></thead><tbody>{users.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.is_active ? 'Active' : 'Disabled'}</td><td>{fmtDateTime(u.created_at)}</td></tr>)}</tbody></table></div> : <EmptyState icon={<Users/>} title="No accounts found"/>}
      </Card>
      <p className="small-note">Analytics source: {stats.data_source}. Review access scopes and consent requirements before using real patient information.</p>
    </>}
  </>;
}

export function DoctorPage() {
  const [stats, setStats] = useState<DoctorStats | null>(null);
  const [appointments, setAppointments] = useState<DoctorAppointment[]>([]);
  const [error, setError] = useState('');
  useEffect(() => { Promise.all([doctorsApi.myStats(), doctorsApi.myAppointments()]).then(([s, a]) => { setStats(s.data); setAppointments(a.data); }).catch(e => setError(apiError(e))); }, []);
  return <>
    <Heading eyebrow="DOCTOR WORKSPACE" title="Consultation overview" desc="Appointment queue for the doctor account. Patient chart access and consent workflows are not enabled in this prototype." />
    {error && <ErrorBox message={error} />}
    {!stats && !error ? <Spinner label="Loading doctor workspace…"/> : stats && <>
      <div className="stat-grid">{[[CalendarDays, 'Upcoming', stats.upcoming], [Users, 'Unique patients', stats.unique_patients], [Activity, 'Completed', stats.completed], [CalendarDays, 'Cancelled', stats.cancelled]].map(([Icon, label, value]: any) => <Card className="stat-card" key={label}><Icon/><div><small>{label}</small><strong>{value}</strong></div></Card>)}</div>
      <Card style={{ marginTop: 16 }}><h3>Appointments</h3>{appointments.length ? appointments.map(a => <div className="list-row" key={a.id}><div><b>{a.doctor_name} · {a.specialty}</b><small>{fmtDateTime(a.appointment_at)} · patient reference #{a.patient_id}</small></div><span>{a.status}</span></div>) : <EmptyState icon={<CalendarDays/>} title="No appointments" desc="Appointments assigned to this doctor account appear here."/>}</Card>
      {!stats.linked_profile && <p className="small-note">This doctor account has no directory profile linked yet. An administrator can create one.</p>}
    </>}
  </>;
}
