// ─── MediSense API Service ─────────────────────────────────────────────────────
// Centralised axios instance. Every function maps to a real backend route; there
// are no mock/fallback data generators here on purpose.

import axios from 'axios';
import type {
  ActivityEntry,
  AdminStats,
  AdminUser,
  AnalyticsSummary,
  Appointment,
  AssistantAvailability,
  AssistantReply,
  AuditEntry,
  AuthResult,
  ChatMessage,
  CompareResult,
  Conversation,
  ConversationDetail,
  Doctor,
  DoctorAppointment,
  DoctorDirectory,
  DoctorProfileResponse,
  DoctorStats,
  FamilyMember,
  FaqEntry,
  HealthMetric,
  HealthRecord,
  HealthSummary,
  Medication,
  Notification,
  OcrStatus,
  ReportAnalysis,
  ReportListItem,
  ReportTrends,
  SupportTicket,
  TimelineEvent,
  User,
  UserSettings,
  VoiceConfig,
  VoiceReply,
  WearableArchitecture,
  WearableDevice,
  AppMeta,
} from '../types';

export const TOKEN_KEY = 'ms_token';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/**
 * A 401 means the session is gone. We clear the token and let the app render its
 * own login screen — we never force a hard reload to /login because the SPA may
 * be mounted on a different base path.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url: string = error?.config?.url ?? '';
    // Login/register failures legitimately return 401/409 — do not treat them
    // as an expired session.
    const isAuthAttempt = url.includes('/auth/login') || url.includes('/auth/register');
    if (status === 401 && !isAuthAttempt) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event('ms:unauthorized'));
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable message from an axios error. */
export function apiError(error: unknown, fallback = 'Something went wrong.'): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined;
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : undefined;
      return field ? `${String(field)}: ${first.msg}` : first.msg;
    }
  }
  const message = (error as { message?: string })?.message;
  if (message && message !== 'Network Error') return message;
  if (message === 'Network Error') {
    return 'Cannot reach the MediSense API. Check that the backend is running.';
  }
  return fallback;
}

// ── Auth & profile ─────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, name: string, password: string) =>
    api.post<AuthResult>('/auth/register', { email, name, password }),
  login: (email: string, password: string) =>
    api.post<AuthResult>('/auth/login', { email, password }),
  me: () => api.get<User>('/auth/me'),
  updateProfile: (data: Partial<User>) => api.put<User>('/auth/me', data),
  changePassword: (current_password: string, new_password: string) =>
    api.post<{ status: string; message: string }>('/auth/change-password', {
      current_password,
      new_password,
    }),
  providers: () => api.get<Record<string, unknown>>('/auth/providers'),
};

// ── Reports ────────────────────────────────────────────────────────────────────
export const reportsApi = {
  ocrStatus: () => api.get<OcrStatus>('/reports/ocr-status'),
  analyze: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post<ReportAnalysis>('/reports/analyze', fd);
  },
  list: () => api.get<ReportListItem[]>('/reports'),
  detail: (id: number) => api.get<ReportAnalysis>(`/reports/${id}`),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/reports/${id}`),
  compare: (ids: number[]) => api.post<CompareResult>('/reports/compare', { report_ids: ids }),
  trends: () => api.get<ReportTrends>('/analytics/report-trends'),
};

// ── Assistant & voice ──────────────────────────────────────────────────────────
export const assistantApi = {
  availability: () => api.get<AssistantAvailability>('/assistant/availability'),
  chat: (message: string, conversation_id?: number) =>
    api.post<AssistantReply>('/assistant', { message, conversation_id }),
  conversations: () => api.get<Conversation[]>('/assistant/conversations'),
  createConversation: (title: string) =>
    api.post<Conversation>('/assistant/conversations', { title }),
  conversation: (id: number) => api.get<ConversationDetail>(`/assistant/conversations/${id}`),
  deleteConversation: (id: number) =>
    api.delete<{ status: string; id: number }>(`/assistant/conversations/${id}`),
};

export const voiceApi = {
  config: () => api.get<VoiceConfig>('/voice/config'),
  ask: (message: string) => api.post<VoiceReply>('/voice/ask', { message }),
};

// ── Clinical ───────────────────────────────────────────────────────────────────
export const appointmentsApi = {
  list: () => api.get<Appointment[]>('/appointments'),
  create: (data: {
    doctor_name: string;
    specialty: string;
    appointment_at: string;
    notes?: string;
    doctor_id?: number;
  }) => api.post<Appointment>('/appointments', data),
  cancel: (id: number) => api.patch<Appointment>(`/appointments/${id}/cancel`),
  setStatus: (id: number, status: string) =>
    api.patch<Appointment>(`/appointments/${id}/status`, { status }),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/appointments/${id}`),
};

export const medicationsApi = {
  list: () => api.get<Medication[]>('/medications'),
  create: (data: { name: string; dosage: string; frequency: string }) =>
    api.post<Medication>('/medications', data),
  update: (id: number, data: Partial<Medication>) =>
    api.put<Medication>(`/medications/${id}`, data),
  toggle: (id: number) => api.patch<Medication>(`/medications/${id}/toggle`),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/medications/${id}`),
};

export const metricsApi = {
  list: (metric?: string) =>
    api.get<HealthMetric[]>('/metrics', { params: metric ? { metric } : undefined }),
  create: (data: {
    metric: string;
    value: number;
    unit?: string;
    recorded_at?: string;
    notes?: string;
  }) => api.post<HealthMetric>('/metrics', data),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/metrics/${id}`),
};

export const recordsApi = {
  list: () => api.get<HealthRecord[]>('/health-records'),
  create: (data: { title: string; record_type: string; date?: string; description?: string }) =>
    api.post<HealthRecord>('/health-records', data),
  remove: (id: number | string) =>
    api.delete<{ status: string; id: number }>(`/health-records/${id}`),
};

export const doctorsApi = {
  directory: (params?: { search?: string; specialty?: string }) =>
    api.get<DoctorDirectory>('/doctors', { params }),
  detail: (id: number) => api.get<Doctor>(`/doctors/${id}`),
  myProfile: () => api.get<DoctorProfileResponse>('/doctor/profile'),
  myAppointments: () => api.get<DoctorAppointment[]>('/doctor/appointments'),
  myStats: () => api.get<DoctorStats>('/doctor/stats'),
};

// ── Notifications / settings / family ──────────────────────────────────────────
export const notificationsApi = {
  list: (unreadOnly = false) =>
    api.get<Notification[]>('/notifications', {
      params: unreadOnly ? { unread_only: true } : undefined,
    }),
  create: (data: { title: string; message: string; type?: string }) =>
    api.post<Notification>('/notifications', data),
  markRead: (id: number) => api.patch<Notification>(`/notifications/${id}/read`),
  markAllRead: () => api.patch<{ status: string; updated: number }>('/notifications/read-all'),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/notifications/${id}`),
};

export const settingsApi = {
  get: () => api.get<UserSettings>('/settings'),
  update: (data: Partial<UserSettings>) => api.put<UserSettings>('/settings', data),
};

export const familyApi = {
  list: () => api.get<FamilyMember[]>('/family'),
  create: (data: {
    name: string;
    relationship_type: string;
    date_of_birth?: string;
    blood_group?: string;
    notes?: string;
  }) => api.post<FamilyMember>('/family', data),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/family/${id}`),
};

// ── Support ────────────────────────────────────────────────────────────────────
export const supportApi = {
  faq: () => api.get<FaqEntry[]>('/support/faq'),
  tickets: () => api.get<SupportTicket[]>('/support/tickets'),
  createTicket: (data: {
    subject: string;
    description: string;
    category: string;
    priority?: string;
  }) => api.post<SupportTicket>('/support/tickets', data),
  ticket: (id: number) => api.get<SupportTicket>(`/support/tickets/${id}`),
  reply: (id: number, message: string) =>
    api.post<SupportTicket>(`/support/tickets/${id}/messages`, { message }),
  setStatus: (id: number, status: string) =>
    api.patch<SupportTicket>(`/support/tickets/${id}/status`, { status }),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/support/tickets/${id}`),
};

// ── Wearables ──────────────────────────────────────────────────────────────────
export const wearablesApi = {
  list: () => api.get<WearableDevice[]>('/wearables'),
  architecture: () => api.get<WearableArchitecture>('/wearables/architecture'),
  register: (data: { device_type: string; device_name: string }) =>
    api.post<WearableDevice>('/wearables', data),
  /** Server-side ingestion payload: `samples` is what a real vendor bridge posts. */
  sync: (
    id: number,
    samples: { metric: string; value: number; unit?: string; recorded_at?: string }[]
  ) =>
    api.post<{ stored: number; rejected: { index: number; reason: string }[]; device: WearableDevice }>(`/wearables/${id}/sync`, { samples }),
  remove: (id: number) => api.delete<{ status: string; id: number }>(`/wearables/${id}`),
};

// ── Analytics & admin ──────────────────────────────────────────────────────────
export const analyticsApi = {
  summary: () => api.get<AnalyticsSummary>('/analytics/summary'),
  healthSummary: () => api.get<HealthSummary>('/analytics/health-summary'),
  timeline: (limit = 50) => api.get<TimelineEvent[]>('/analytics/timeline', { params: { limit } }),
  reportTrends: () => api.get<ReportTrends>('/analytics/report-trends'),
};

export const adminApi = {
  stats: () => api.get<AdminStats>('/admin/stats'),
  users: () => api.get<AdminUser[]>('/admin/users'),
  setRole: (userId: number, role: string) =>
    api.patch<AdminUser>(`/admin/users/${userId}/role`, { role }),
  setActive: (userId: number, is_active: boolean) =>
    api.patch<AdminUser>(`/admin/users/${userId}/active`, { is_active }),
  audit: () => api.get<AuditEntry[]>('/admin/audit'),
  activity: () => api.get<ActivityEntry[]>('/admin/activity'),
  doctors: () => api.get<Doctor[]>('/admin/doctors'),
  addDoctor: (data: Partial<Doctor>) => api.post<Doctor>('/admin/doctors', data),
  updateDoctor: (id: number, data: Partial<Doctor>) => api.put<Doctor>(`/admin/doctors/${id}`, data),
  removeDoctor: (id: number) => api.delete<{ status: string; id: number }>(`/admin/doctors/${id}`),
};

export const metaApi = {
  get: () => api.get<AppMeta>('/meta'),
  health: () => api.get<{ status: string }>('/health'),
};

export type { ChatMessage };
export default api;
