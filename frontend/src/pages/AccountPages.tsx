import { useEffect, useState, type FormEvent } from 'react';
import { Activity, Bell, Check, LifeBuoy, Trash2, Watch } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiError, authApi, familyApi, notificationsApi, settingsApi, supportApi, wearablesApi } from '../services/api';
import type { FamilyMember, FaqEntry, Notification, UserSettings, WearableArchitecture, WearableDevice } from '../types';
import { Button, Card, ErrorBox, Heading, Notice, Spinner, Tag, fmtDateTime } from '../components/ui';

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ name: '', phone: '', date_of_birth: '', gender: '', address: '', emergency_contact: '', blood_group: '' });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [family, setFamily] = useState<FamilyMember[]>([]);
  const [familyName, setFamilyName] = useState('');
  const [familyRelation, setFamilyRelation] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    if (user) setForm({ name: user.name, phone: user.phone || '', date_of_birth: user.date_of_birth || '', gender: user.gender || '', address: user.address || '', emergency_contact: user.emergency_contact || '', blood_group: user.blood_group || '' });
  }, [user]);
  useEffect(() => {
    void Promise.all([settingsApi.get(), familyApi.list()]).then(([s, f]) => { setSettings(s.data); setFamily(f.data); }).catch(err => setError(apiError(err)));
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try { const response = await authApi.updateProfile(form); setUser(response.data); setMessage('Profile saved.'); }
    catch (err) { setError(apiError(err)); }
    finally { setBusy(false); }
  }
  async function saveSettings() { if (!settings) return; try { const r = await settingsApi.update(settings); setSettings(r.data); setMessage('Preferences saved.'); } catch (err) { setError(apiError(err)); } }
  async function addFamily(event: FormEvent) {
    event.preventDefault(); setError('');
    try { await familyApi.create({ name: familyName, relationship_type: familyRelation }); setFamilyName(''); setFamilyRelation(''); setFamily((await familyApi.list()).data); }
    catch (err) { setError(apiError(err)); }
  }
  async function removeFamily(id: number) {
    try { await familyApi.remove(id); setFamily(rows => rows.filter(row => row.id !== id)); } catch (err) { setError(apiError(err)); }
  }
  async function changePassword(event: FormEvent) {
    event.preventDefault(); setError(''); setMessage('');
    try { const response = await authApi.changePassword(currentPassword, newPassword); setMessage(response.data.message); setCurrentPassword(''); setNewPassword(''); }
    catch (err) { setError(apiError(err)); }
  }

  return <>
    <Heading eyebrow="ACCOUNT" title="My profile" desc="Manage the personal information you choose to keep in MediSense." />
    <Notice>Health details are optional and are not inferred. Only enter information you choose to store.</Notice>
    <Card className="form-card" style={{ marginTop: 16 }}>
      <form className="inline-form" onSubmit={save}>
        <label>Full name<input required maxLength={120} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
        <label>Email<input disabled value={user?.email || ''} /></label>
        <label>Mobile number<input maxLength={20} value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></label>
        <label>Date of birth<input type="date" value={form.date_of_birth} onChange={e => setForm({ ...form, date_of_birth: e.target.value })} /></label>
        <label>Gender<input maxLength={20} value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })} /></label>
        <label>Blood group (self-reported)<input maxLength={10} value={form.blood_group} onChange={e => setForm({ ...form, blood_group: e.target.value })} /></label>
        <label>Address<input value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} /></label>
        <label>Emergency contact<input maxLength={255} value={form.emergency_contact} onChange={e => setForm({ ...form, emergency_contact: e.target.value })} /></label>
        {error && <ErrorBox message={error} />}{message && <p role="status">{message}</p>}
        <Button type="submit" disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</Button>
      </form>
    </Card>
    <Card style={{ marginTop: 16 }}><h3>Preferences</h3>{settings ? <div className="inline-form" style={{ marginTop: 14 }}>
      <label>Language<select value={settings.language} onChange={e => setSettings({ ...settings, language: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option><option value="hinglish">Hinglish</option></select></label>
      <label><input type="checkbox" checked={settings.notifications_enabled} onChange={e => setSettings({ ...settings, notifications_enabled: e.target.checked })}/> In-app notifications</label>
      <label><input type="checkbox" checked={settings.email_notifications} onChange={e => setSettings({ ...settings, email_notifications: e.target.checked })}/> Email notifications (delivery requires email setup)</label>
      <Button onClick={saveSettings}>Save preferences</Button>
    </div> : <Spinner label="Loading preferences…"/>}</Card>
    <Card style={{ marginTop: 16 }}><h3>Family profiles</h3><p className="small-note">These are names and details you choose to store. Family members do not receive access to your account.</p>
      <form className="inline-form" onSubmit={addFamily}><label>Name<input required value={familyName} onChange={e => setFamilyName(e.target.value)}/></label><label>Relationship<input required value={familyRelation} onChange={e => setFamilyRelation(e.target.value)}/></label><Button type="submit">Add family member</Button></form>
      {family.map(member => <div className="list-row" key={member.id}><div><b>{member.name}</b><small>{member.relationship_type}</small></div><Button variant="secondary" onClick={() => removeFamily(member.id)}>Remove</Button></div>)}
    </Card>
    <Card style={{ marginTop: 16 }}><h3>Change password</h3><form className="inline-form" onSubmit={changePassword}>
      <label>Current password<input required type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)}/></label>
      <label>New password (at least 8 characters)<input required minLength={8} type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)}/></label>
      <Button type="submit">Update password</Button>
    </form></Card>
  </>;
}

export function NotificationsPage() {
  const [items, setItems] = useState<Notification[] | null>(null);
  const [error, setError] = useState('');
  const load = () => notificationsApi.list().then(r => setItems(r.data)).catch(e => setError(apiError(e)));
  useEffect(() => { void load(); }, []);
  async function markAll() {
    try { await notificationsApi.markAllRead(); await load(); } catch (e) { setError(apiError(e)); }
  }
  async function markOne(id: number) {
    try { await notificationsApi.markRead(id); await load(); } catch (e) { setError(apiError(e)); }
  }
  return <>
    <Heading eyebrow="ACCOUNT" title="Notifications" desc="Updates from your saved MediSense records." action={<Button onClick={markAll}><Check size={15} /> Mark all read</Button>} />
    {error && <ErrorBox message={error} />}
    {items === null ? <Spinner label="Loading notifications…" /> : items.length === 0 ? <Card><div className="empty-state"><Bell/><b>You're all caught up</b><p>New record updates will appear here.</p></div></Card> : <Card>
      {items.map(item => <div className="list-row" key={item.id}>
        <div className="file-icon"><Bell/></div><div><b>{item.title}</b><small>{item.message} · {fmtDateTime(item.created_at)}</small></div>
        {!item.is_read && <Button onClick={() => markOne(item.id)}><Check size={14}/> Mark read</Button>}
      </div>)}
    </Card>}
  </>;
}

export function SupportPage() {
  const [faq, setFaq] = useState<FaqEntry[]>([]);
  const [tickets, setTickets] = useState<{ id: number; subject: string; status: string; category: string }[]>([]);
  const [subject, setSubject] = useState(''); const [description, setDescription] = useState('');
  const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const load = () => Promise.all([supportApi.faq(), supportApi.tickets()]).then(([f, t]) => { setFaq(f.data); setTickets(t.data); }).catch(e => setError(apiError(e)));
  useEffect(() => { void load(); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('');
    try { await supportApi.createTicket({ subject, description, category: 'general' }); setSubject(''); setDescription(''); setNotice('Support request created.'); await load(); }
    catch (e) { setError(apiError(e)); }
  }
  return <>
    <Heading eyebrow="HELP CENTRE" title="Help & support" desc="Browse common answers or create a support request." />
    {error && <ErrorBox message={error} />}{notice && <Notice>{notice}</Notice>}
    <div className="dashboard-grid" style={{ marginTop: 16 }}>
      <Card><div className="card-head"><h3>Frequently asked questions</h3><LifeBuoy size={18}/></div>
        {faq.length ? faq.map((item, i) => <details key={i} className="list-row"><summary><b>{item.question}</b></summary><p>{item.answer}</p></details>) : <p className="small-note">Help articles are unavailable.</p>}
      </Card>
      <Card><h3>Contact support</h3><form className="inline-form" onSubmit={submit}>
        <label>Subject<input required maxLength={160} value={subject} onChange={e => setSubject(e.target.value)}/></label>
        <label>Describe the issue<textarea required maxLength={4000} value={description} onChange={e => setDescription(e.target.value)}/></label>
        <Button type="submit">Create support request</Button>
      </form></Card>
    </div>
    <Card style={{ marginTop: 16 }}><h3>Your support requests</h3>{tickets.length ? tickets.map(t => <div className="list-row" key={t.id}><b>#{t.id} · {t.subject}</b><span>{t.category} · {t.status}</span></div>) : <p className="small-note">No support requests yet.</p>}</Card>
  </>;
}

export function WearablesPage() {
  const [devices, setDevices] = useState<WearableDevice[]>([]);
  const [architecture, setArchitecture] = useState<WearableArchitecture | null>(null);
  const [name, setName] = useState(''); const [type, setType] = useState('smartwatch');
  const [selectedId, setSelectedId] = useState('');
  const [metric, setMetric] = useState('heart_rate'); const [value, setValue] = useState('');
  const [unit, setUnit] = useState('bpm'); const [recordedAt, setRecordedAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false);
  const load = () => Promise.all([wearablesApi.list(), wearablesApi.architecture()]).then(([d, a]) => { setDevices(d.data); setArchitecture(a.data); setSelectedId(current => current || String(d.data[0]?.id ?? '')); }).catch(e => setError(apiError(e)));
  useEffect(() => { void load(); }, []);
  async function add(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('');
    try { const { data } = await wearablesApi.register({ device_type: type, device_name: name }); setName(''); setSelectedId(String(data.id)); setNotice('Device added. You can now record a measurement for it.'); await load(); }
    catch (e) { setError(apiError(e)); }
  }
  async function remove(id: number) { setError(''); setNotice(''); try { await wearablesApi.remove(id); if (selectedId === String(id)) setSelectedId(''); setNotice('Device removed.'); await load(); } catch (e) { setError(apiError(e)); } }
  async function saveMeasurement(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('');
    if (!selectedId) { setError('Add a device before recording a measurement.'); return; }
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) { setError('Enter a valid number for the measurement.'); return; }
    setBusy(true);
    try {
      const { data } = await wearablesApi.sync(Number(selectedId), [{ metric, value: numericValue, unit, recorded_at: new Date(recordedAt).toISOString() }]);
      setValue(''); setNotice(`Measurement saved to your health records${data.stored === 1 ? '.' : ` (${data.stored} saved).`}`); await load();
    } catch (e) { setError(apiError(e)); } finally { setBusy(false); }
  }
  return <>
    <Heading eyebrow="CONNECTED HEALTH" title="Wearable devices" desc="Keep your devices organized and add readings to your health timeline." />
    <Notice>Automatic Fitbit, Health Connect, and Apple Health sync needs a companion integration. You can still enter real readings below and save them to your records.</Notice>
    {error && <ErrorBox message={error} />}{notice && <Notice>{notice}</Notice>}
    <Card className="form-card" style={{ marginTop: 16 }}><form className="inline-form" onSubmit={add}>
      <label>Device label<input required maxLength={100} value={name} onChange={e => setName(e.target.value)} placeholder="My fitness tracker"/></label>
      <label>Device type<select value={type} onChange={e => setType(e.target.value)}>{(architecture?.supported_devices ?? [{type:'smartwatch',label:'Smartwatch'},{type:'fitness_band',label:'Fitness band'},{type:'smart_ring',label:'Smart ring'},{type:'glucose_monitor',label:'Glucose monitor'},{type:'blood_pressure_cuff',label:'Blood pressure cuff'}]).map(d => <option key={d.type} value={d.type}>{d.label}</option>)}</select></label>
      <Button type="submit"><Watch size={15}/> Add device</Button>
    </form></Card>
    <div className="wearable-layout" style={{ marginTop: 16 }}>
      <Card><div className="card-head"><div><span className="eyebrow">YOUR DEVICES</span><h3>Connected health tools</h3></div><Tag>{devices.length} saved</Tag></div>
        {devices.length ? devices.map(d => <div className="wearable-device" key={d.id}><span className="wearable-device-icon"><Watch size={18}/></span><div className="wearable-device-copy"><b>{d.device_name}</b><small>{d.device_type.replace(/_/g,' ')} · {d.connection_status === 'connected' ? 'Measurement received' : 'Ready for manual readings'}</small>{d.last_synced && <small>Last update · {fmtDateTime(d.last_synced)}</small>}</div><button className="icon-btn wearable-remove" title={`Remove ${d.device_name}`} aria-label={`Remove ${d.device_name}`} onClick={() => void remove(d.id)}><Trash2 size={15}/></button></div>) : <div className="empty-state"><div><Watch size={19}/></div><b>No devices added</b><p>Add a device above, then record a measurement to start your health timeline.</p></div>}
      </Card>
      <Card><div className="card-head"><div><span className="eyebrow">MANUAL MEASUREMENT</span><h3>Record a reading</h3></div><Activity size={18}/></div>
        {devices.length ? <form className="wearable-measure-form" onSubmit={saveMeasurement}>
          <label>Save under<select value={selectedId} onChange={e => setSelectedId(e.target.value)}>{devices.map(d => <option key={d.id} value={d.id}>{d.device_name}</option>)}</select></label>
          <label>Measurement<select value={metric} onChange={e => { setMetric(e.target.value); setUnit(e.target.value === 'heart_rate' ? 'bpm' : e.target.value === 'blood_pressure_systolic' || e.target.value === 'blood_pressure_diastolic' ? 'mmHg' : e.target.value === 'blood_glucose' ? 'mg/dL' : e.target.value === 'weight' ? 'kg' : e.target.value === 'sleep_duration' ? 'hours' : 'steps'); }}><option value="heart_rate">Heart rate</option><option value="blood_pressure_systolic">Systolic pressure</option><option value="blood_pressure_diastolic">Diastolic pressure</option><option value="blood_glucose">Blood glucose</option><option value="steps">Steps</option><option value="sleep_duration">Sleep duration</option><option value="weight">Weight</option></select></label>
          <div className="wearable-value-row"><label>Value<input type="number" inputMode="decimal" step="any" required value={value} onChange={e => setValue(e.target.value)} placeholder="e.g. 72"/></label><label>Unit<input required maxLength={20} value={unit} onChange={e => setUnit(e.target.value)} /></label></div>
          <label>Recorded at<input type="datetime-local" required value={recordedAt} onChange={e => setRecordedAt(e.target.value)} /></label>
          <Button type="submit" disabled={busy || !selectedId}><Activity size={15}/>{busy ? 'Saving reading…' : 'Save measurement'}</Button>
        </form> : <p className="small-note">Add a device first to enable measurement entry.</p>}
      </Card>
    </div>
    <Card style={{ marginTop: 16 }}><div className="card-head"><div><span className="eyebrow">INTEGRATION STATUS</span><h3>Automatic sync availability</h3></div></div>
      <p className="small-note">Automatic vendor sync requires credentials and a mobile companion app. Manual measurements are available now.</p>
      <div className="vendor-grid">{architecture?.vendors.map(v => <div className="vendor-status" key={v.vendor}><span className="vendor-status-dot"/><div><b>{v.vendor}</b><small>{v.status === 'requires_mobile_app' ? 'Mobile app integration needed' : 'Setup required for automatic sync'}</small></div><Tag tone="neutral">Not connected</Tag></div>)}</div>
    </Card>
  </>;
}
