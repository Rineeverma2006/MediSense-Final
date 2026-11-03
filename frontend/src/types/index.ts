// ─── MediSense Type Definitions ────────────────────────────────────────────────
// These mirror the FastAPI response builders in backend/app/api/routers/*.py.
// Keeping them exact avoids optional-chaining noise and silent undefined renders.

export type Role = 'patient' | 'doctor' | 'admin';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  phone: string;
  profile_image: string;
  blood_group: string;
  date_of_birth: string;
  gender: string;
  address: string;
  emergency_contact: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string | null;
}

export interface AuthResult {
  access_token: string;
  token_type: string;
  role: Role;
  name: string;
  user: User;
}

// ── Reports ────────────────────────────────────────────────────────────────────
export type ParameterStatus =
  | 'within_range'
  | 'below_range'
  | 'above_range'
  | 'no_reference_range';

export interface ReportParameter {
  name: string;
  value: number;
  unit: string;
  ref_low: number | null;
  ref_high: number | null;
  status: ParameterStatus;
  source?: string;
  source_page?: number | null;
  confidence?: number;
}

export interface ReportCounts {
  total: number;
  flagged: number;
  within_range: number;
  below_range?: number;
  above_range?: number;
  no_reference_range?: number;
}

export interface ReportAnalysis {
  id: number;
  filename: string;
  created_at: string;
  parameters: ReportParameter[];
  counts: ReportCounts;
  summary: string;
  disclaimer: string;
  extraction?: { method: string; pages: number; ocr_used: boolean };
}

export interface ReportListItem {
  id: number;
  filename: string;
  created_at: string;
  flagged: number;
  total_parameters: number;
}

export interface CompareRow {
  name: string;
  previous: number | null;
  current: number;
  change: number | null;
  percent_change: number | null;
  unit: string;
  direction: 'up' | 'down' | 'stable' | 'new';
  status: ParameterStatus;
  previous_status?: ParameterStatus;
}

export interface CompareResult {
  older: { id: number; filename: string; created_at: string };
  newer: { id: number; filename: string; created_at: string };
  rows: CompareRow[];
  compared: number;
  new_parameters: number;
  improved: string[];
  worsened: string[];
  summary: string;
  disclaimer: string;
}

export interface OcrStatus {
  available: boolean;
  engine?: string;
  detail?: string;
  supports?: string[];
}

// ── Assistant ──────────────────────────────────────────────────────────────────
export interface AssistantAvailability {
  mode: 'demo' | 'gemini' | 'openai' | string;
  live: boolean;
  provider?: string;
  detail?: string;
}

export interface AssistantReply {
  conversation_id: number;
  conversation_title: string;
  answer: string;
  mode: string;
  disclaimer: string;
  notice?: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string | null;
  message_count: number;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationDetail {
  id: number;
  title: string;
  created_at: string;
  messages: ChatMessage[];
}

export interface VoiceConfig {
  recognition: string;
  synthesis: string;
  server_tts: boolean;
  languages: { code: string; label: string }[];
  notes: string;
  privacy: string;
}

export interface VoiceReply {
  conversation_id: number;
  speech: { text: string; lang: string };
  mode: string;
}

// ── Clinical ───────────────────────────────────────────────────────────────────
export interface Appointment {
  id: number;
  doctor_name: string;
  specialty: string;
  appointment_at: string;
  status: string;
  notes: string;
  doctor_id: number | null;
  created_at: string | null;
}

export interface Medication {
  id: number;
  name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date: string;
  active: boolean;
  created_at: string | null;
}

export interface HealthMetric {
  id: number;
  metric: string;
  value: number;
  unit: string;
  recorded_at: string;
  notes: string;
  source: string;
}

export interface HealthRecord {
  id: number | string;
  title: string;
  type: string;
  record_type: string;
  date: string;
  description: string;
  created_at: string | null;
  report_id?: number;
}

export interface Doctor {
  id: number;
  name: string;
  specialty: string;
  qualification: string;
  experience: string;
  hospital: string;
  rating: number;
  consultation_fee: number;
  image: string;
  image_url: string;
  about: string;
  email: string;
  phone: string;
  is_active: boolean;
  is_demo: boolean;
}

export interface DoctorDirectory {
  doctors: Doctor[];
  specialties: string[];
  count: number;
}

export interface DoctorProfileResponse {
  linked: boolean;
  detail?: string;
  name?: string;
  doctor?: Doctor;
}

export interface DoctorStats {
  total_appointments: number;
  upcoming: number;
  completed: number;
  cancelled: number;
  unique_patients: number;
  by_status: Record<string, number>;
  linked_profile: boolean;
}

export interface DoctorAppointment {
  id: number;
  patient_id: number;
  doctor_name: string;
  specialty: string;
  appointment_at: string;
  status: string;
  notes: string;
}

// ── Notification / support / settings / wearables ──────────────────────────────
export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string | null;
}

export interface UserSettings {
  theme: string;
  language: string;
  notifications_enabled: boolean;
  email_notifications: boolean;
}

export interface TicketMessage {
  id: number;
  message: string;
  is_staff: boolean;
  created_at: string | null;
}

export interface SupportTicket {
  id: number;
  subject: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  created_at: string | null;
  updated_at: string | null;
  messages?: TicketMessage[];
}

export interface FaqEntry {
  question: string;
  answer: string;
}

export interface WearableDevice {
  id: number;
  device_type: string;
  device_name: string;
  connection_status: string;
  last_synced: string | null;
}

export interface WearableArchitecture {
  supported_devices: { type: string; label: string }[];
  vendors: { vendor: string; status: string; requires: string }[];
  ingest_endpoint: string;
  notes: string;
}

// ── Analytics ──────────────────────────────────────────────────────────────────
export interface AnalyticsSummary {
  reports: number;
  appointments: number;
  active_medications: number;
  metrics: number;
  flagged_parameters: number;
  upcoming_appointments: number;
  unread_notifications: number;
  health_records: number;
  wearables: number;
  conversations: number;
  data_source: string;
}

export interface MetricPoint {
  value: number;
  recorded_at: string;
}

export interface MetricSummary {
  metric: string;
  unit: string;
  latest: number;
  previous: number | null;
  delta: number | null;
  direction: 'up' | 'down' | 'flat';
  readings: number;
  recorded_at: string;
  series: MetricPoint[];
}

export interface HealthSummary {
  metrics: MetricSummary[];
  tracked: number;
  data_source: string;
}

export interface TimelineEvent {
  type: 'report' | 'appointment' | 'medication' | 'record';
  title: string;
  at: string;
  ref_id: number;
}

export interface ReportTrendPoint {
  report_id: number;
  filename: string;
  created_at: string;
  total: number;
  flagged: number;
  within_range: number;
}

export interface ReportTrends {
  points: ReportTrendPoint[];
  count: number;
}

export interface AdminStats {
  users: number;
  patients: number;
  doctors: number;
  admins: number;
  reports: number;
  appointments: number;
  medications: number;
  metrics: number;
  conversations: number;
  support_tickets: number;
  open_tickets: number;
  directory_doctors: number;
  wearables: number;
  by_role: Record<string, number>;
  appointments_by_status: Record<string, number>;
  data_source: string;
}

export interface AdminUser {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  created_at: string | null;
}

export interface AuditEntry {
  id: number;
  user_id: number | null;
  action: string;
  at: string | null;
}

export interface ActivityEntry {
  action: string;
  count: number;
}

export interface FamilyMember {
  id: number;
  name: string;
  relationship_type: string;
  date_of_birth: string;
  blood_group: string;
  notes: string;
}

export interface AppMeta {
  app: string;
  version: string;
  environment: string;
  ai: AssistantAvailability;
  ocr: OcrStatus;
  features: Record<string, unknown>;
  warnings: string[];
}
