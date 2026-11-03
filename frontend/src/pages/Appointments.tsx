import { useState } from 'react';
import {
  Ban,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Hospital,
  Plus,
  Trash2,
  UserRound,
} from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { apiError, appointmentsApi, doctorsApi } from '../services/api';
import {
  Button,
  Card,
  EmptyState,
  ErrorBox,
  Heading,
  Notice,
  Spinner,
  Tag,
  fmtDateTime,
  fmtNumber,
} from '../components/ui';

const STATUS_TONE: Record<string, string> = {
  scheduled: 'blue',
  completed: 'green',
  cancelled: 'amber',
};

export default function Appointments() {
  const list = useAsync(() => appointmentsApi.list().then((r) => r.data), []);
  const doctors = useAsync(() => doctorsApi.directory().then((r) => r.data), []);

  const [doctorName, setDoctorName] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [when, setWhen] = useState('');
  const [notes, setNotes] = useState('');
  const [doctorId, setDoctorId] = useState<number | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const filteredDoctors = (doctors.data?.doctors ?? []).filter(
    (d) => !specialty || d.specialty === specialty
  );

  const book = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await appointmentsApi.create({
        doctor_name: doctorName.trim(),
        specialty: specialty.trim(),
        appointment_at: new Date(when).toISOString(),
        notes: notes.trim(),
        doctor_id: doctorId,
      });
      setDoctorName('');
      setSpecialty('');
      setWhen('');
      setNotes('');
      setDoctorId(undefined);
      await list.reload();
    } catch (err) {
      setError(apiError(err, 'Could not book that appointment.'));
    } finally {
      setBusy(false);
    }
  };

  const act = async (fn: () => Promise<unknown>) => {
    setError('');
    try {
      await fn();
      await list.reload();
    } catch (err) {
      setError(apiError(err, 'Could not update that appointment.'));
    }
  };

  const rows = list.data ?? [];
  const upcoming = rows.filter(
    (a) => a.status === 'scheduled' && new Date(a.appointment_at) >= new Date()
  );
  const past = rows.filter(
    (a) => a.status !== 'scheduled' || new Date(a.appointment_at) < new Date()
  );

  return (
    <>
      <Heading
        eyebrow="CARE COORDINATION"
        title="Appointments"
        desc="Book a visit, track its status and keep a record of completed consultations."
      />

      {error && <ErrorBox message={error} />}

      <div className="dashboard-grid">
        <Card className="form-card">
          <div className="card-head">
            <b>Book an appointment</b>
            <CalendarDays size={15} />
          </div>
          <form className="inline-form" onSubmit={book}>
            <label>
              Doctor
              <select
                value={doctorId ?? ''}
                onChange={(e) => {
                  const id = e.target.value ? Number(e.target.value) : undefined;
                  setDoctorId(id);
                  const picked = (doctors.data?.doctors ?? []).find((d) => d.id === id);
                  if (picked) {
                    setDoctorName(picked.name);
                    setSpecialty(picked.specialty);
                  }
                }}
              >
                <option value="">Enter manually</option>
                {(doctors.data?.doctors ?? []).map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} — {d.specialty}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Doctor name
              <input
                value={doctorName}
                onChange={(e) => setDoctorName(e.target.value)}
                placeholder="Dr. Arjun Mehta"
                required
              />
            </label>
            <label>
              Specialty
              <input
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                placeholder="Cardiology"
                list="specialty-list"
                required
              />
              <datalist id="specialty-list">
                {(doctors.data?.specialties ?? []).map((s) => (
                  <option key={s} value={s} />
                ))}
              </datalist>
            </label>
            <label>
              Date &amp; time
              <input
                type="datetime-local"
                value={when}
                onChange={(e) => setWhen(e.target.value)}
                required
              />
            </label>
            <label>
              Notes
              <input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Reason for visit"
              />
            </label>
            <Button type="submit" disabled={busy}>
              {busy ? 'Booking…' : <><Plus size={14} /> Book</>}
            </Button>
          </form>

          {filteredDoctors.length > 0 && (
            <p className="small-note" style={{ marginTop: 12 }}>
              {doctorId
                ? 'Booking against a directory profile links your visit to that doctor.'
                : 'Pick a directory doctor to link the visit, or type any name for an external clinician.'}
            </p>
          )}
        </Card>

        <Card>
          <div className="card-head">
            <div>
              <b>Summary</b>
              <small className="small-note">From your appointment records</small>
            </div>
          </div>
          <div className="metric-line">
            <span><Clock3 size={13} /> Upcoming</span>
            <b>{upcoming.length}</b>
          </div>
          <div className="metric-line">
            <span><CheckCircle2 size={13} /> Completed</span>
            <b>{rows.filter((a) => a.status === 'completed').length}</b>
          </div>
          <div className="metric-line">
            <span><Ban size={13} /> Cancelled</span>
            <b>{rows.filter((a) => a.status === 'cancelled').length}</b>
          </div>
          <div className="metric-line">
            <span><Hospital size={13} /> Directory profiles</span>
            <b>{doctors.data?.count ?? 0}</b>
          </div>
        </Card>
      </div>

      <Card style={{ marginTop: 16 }}>
        <div className="card-head">
          <div>
            <b>Upcoming visits</b>
            <small className="small-note">Scheduled appointments</small>
          </div>
          <Tag tone="blue">{upcoming.length}</Tag>
        </div>

        {list.loading && <Spinner label="Loading appointments…" />}
        {!list.loading && upcoming.length === 0 && (
          <EmptyState
            icon={<CalendarDays size={18} />}
            title="No upcoming appointments"
            desc="Use the form above to schedule a consultation."
          />
        )}

        {upcoming.map((a) => (
          <div className="list-row" key={a.id}>
            <div className="file-icon">
              <UserRound size={15} />
            </div>
            <div>
              <b>{a.doctor_name}</b>
              <small>
                {a.specialty} · {fmtDateTime(a.appointment_at)}
                {a.notes ? ` · ${a.notes}` : ''}
              </small>
            </div>
            <Tag tone={STATUS_TONE[a.status] ?? 'neutral'}>{a.status}</Tag>
            <button
              className="text-btn"
              onClick={() => void act(() => appointmentsApi.setStatus(a.id, 'completed'))}
              title="Mark completed"
            >
              <CheckCircle2 size={13} /> Done
            </button>
            <button
              className="text-btn"
              onClick={() => void act(() => appointmentsApi.cancel(a.id))}
              title="Cancel appointment"
            >
              <Ban size={13} /> Cancel
            </button>
          </div>
        ))}
      </Card>

      {past.length > 0 && (
        <Card style={{ marginTop: 16 }}>
          <div className="card-head">
            <div>
              <b>History</b>
              <small className="small-note">Completed and cancelled visits</small>
            </div>
            <Tag tone="neutral">{past.length}</Tag>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Doctor</th>
                  <th>Specialty</th>
                  <th>When</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {past.map((a) => (
                  <tr key={a.id}>
                    <td><b>{a.doctor_name}</b></td>
                    <td>{a.specialty}</td>
                    <td>{fmtDateTime(a.appointment_at)}</td>
                    <td><Tag tone={STATUS_TONE[a.status] ?? 'neutral'}>{a.status}</Tag></td>
                    <td>
                      <button
                        className="icon-btn"
                        onClick={() => void act(() => appointmentsApi.remove(a.id))}
                        aria-label="Delete appointment"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {!list.loading && rows.length > 0 && (
        <Notice>
          Reminders are only sent for notifications MediSense actually creates. Nothing is emailed or
          SMSed unless email delivery is configured on the server.
        </Notice>
      )}

      <p className="small-note" style={{ marginTop: 12 }}>
        {fmtNumber(rows.length)} appointment record(s) stored in your account.
      </p>
    </>
  );
}
