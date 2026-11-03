import { useState } from 'react';
import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Activity,
  Bell,
  Bone,
  CalendarDays,
  ChartNoAxesCombined,
  ChevronDown,
  FileHeart,
  FileText,
  HeartPulse,
  Home,
  Hospital,
  LogOut,
  Menu,
  MessageCircle,
  Moon,
  Pill,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  Stethoscope,
  Sun,
  UserRound,
  Users,
  Watch,
  LifeBuoy,
} from 'lucide-react';
import { useAuth, hasRole } from '../context/AuthContext';
import { useTheme } from '../hooks/useAsync';
import { initials } from './ui';
import type { Role } from '../types';

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  roles?: Role[];
  badge?: string;
}

const PATIENT_NAV: NavItem[] = [
  { to: '/', label: 'Overview', icon: <Home size={18} /> },
  { to: '/assistant', label: 'AI Assistant', icon: <MessageCircle size={18} />, badge: 'AI' },
  { to: '/reports', label: 'Report Analyzer', icon: <FileText size={18} /> },
  { to: '/appointments', label: 'Appointments', icon: <CalendarDays size={18} /> },
  { to: '/records', label: 'Health Records', icon: <FileHeart size={18} /> },
  { to: '/insights', label: 'Health Insights', icon: <ChartNoAxesCombined size={18} /> },
  { to: '/medications', label: 'Medications', icon: <Pill size={18} /> },
  { to: '/doctors', label: 'Doctors & Hospitals', icon: <Hospital size={18} /> },
  { to: '/anatomy', label: '3D Anatomy', icon: <Bone size={18} /> },
  { to: '/wearables', label: 'Wearables', icon: <Watch size={18} /> },
];

const DOCTOR_NAV: NavItem[] = [
  { to: '/doctor', label: 'Doctor Console', icon: <Stethoscope size={18} /> },
  { to: '/doctor/patients', label: 'Appointments', icon: <CalendarDays size={18} /> },
];

const ADMIN_NAV: NavItem[] = [
  { to: '/admin', label: 'Admin Console', icon: <ShieldCheck size={18} /> },
  { to: '/admin/users', label: 'Users', icon: <Users size={18} /> },
  { to: '/admin/directory', label: 'Directory', icon: <Hospital size={18} /> },
];

const ACCOUNT_NAV: NavItem[] = [
  { to: '/notifications', label: 'Notifications', icon: <Bell size={18} /> },
  { to: '/support', label: 'Help & Support', icon: <LifeBuoy size={18} /> },
  { to: '/profile', label: 'Profile & Settings', icon: <UserRound size={18} /> },
];

function Section({ label, items, collapsed }: { label: string; items: NavItem[]; collapsed: boolean }) {
  if (!items.length) return null;
  return (
    <>
      <div className="nav-label">{collapsed ? '' : label}</div>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          title={item.label}
        >
          {item.icon}
          {!collapsed && <span>{item.label}</span>}
          {!collapsed && item.badge && <i className="nav-ai">{item.badge}</i>}
        </NavLink>
      ))}
    </>
  );
}

export default function Layout({
  children,
  search,
  onSearch,
  unread,
}: {
  children: ReactNode;
  search?: string;
  onSearch?: (value: string) => void;
  unread?: number;
}) {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [dark, toggleDark] = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const patientNav = PATIENT_NAV.filter((n) => !n.roles || hasRole(user, ...n.roles));
  const roleLabel =
    user?.role === 'admin' ? 'Administrator' : user?.role === 'doctor' ? 'Clinician' : 'Patient account';

  return (
    <div className="app-shell">
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <HeartPulse size={23} />
          </div>
          {!collapsed && (
            <div>
              <b>MediSense</b>
              <small>HEALTH INTELLIGENCE</small>
            </div>
          )}
        </div>

        <div className="sidebar-scroll">
          <Section label="WORKSPACE" items={patientNav} collapsed={collapsed} />
          {hasRole(user, 'doctor') && (
            <Section label="CLINICIAN" items={DOCTOR_NAV} collapsed={collapsed} />
          )}
          {hasRole(user, 'admin') && <Section label="ADMIN" items={ADMIN_NAV} collapsed={collapsed} />}
          <Section label="ACCOUNT" items={ACCOUNT_NAV} collapsed={collapsed} />
        </div>

        <div className="sidebar-bottom">
          <NavLink to="/profile" className="nav-link" title="Settings">
            <SettingsIcon size={18} />
            {!collapsed && 'Settings'}
          </NavLink>
          <div className="profile-mini">
            <div className="avatar">{initials(user?.name)}</div>
            {!collapsed && (
              <div>
                <b>{user?.name ?? 'Account'}</b>
                <small>{roleLabel}</small>
              </div>
            )}
            <button onClick={logout} title="Sign out" aria-label="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button
            className="icon-btn"
            onClick={() => setCollapsed((c) => !c)}
            aria-label="Toggle sidebar"
          >
            <Menu size={19} />
          </button>

          <div className="crumb">
            MediSense <span>/</span> <b>{roleLabel}</b>
          </div>

          <div className="top-actions">
            {onSearch && (
              <div className="searchbox">
                <Search size={16} />
                <input
                  placeholder="Search doctors, reports, health topics…"
                  value={search ?? ''}
                  onChange={(e) => onSearch(e.target.value)}
                  aria-label="Search"
                />
              </div>
            )}
            <button
              className="icon-btn"
              onClick={() => navigate('/notifications')}
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell size={18} />
              {Boolean(unread) && <i className="notification-dot" />}
            </button>
            <button
              className="icon-btn"
              onClick={toggleDark}
              aria-label="Toggle colour theme"
              title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="top-user" onClick={() => setMenuOpen((m) => !m)} role="button" tabIndex={0}>
              <div className="avatar">{initials(user?.name)}</div>
              <span>{user?.name ?? 'Account'}</span>
              <ChevronDown size={15} />
              {menuOpen && (
                <div className="user-menu">
                  <button onClick={() => { setMenuOpen(false); navigate('/profile'); }}>
                    <UserRound size={14} /> Profile
                  </button>
                  <button onClick={() => { setMenuOpen(false); navigate('/support'); }}>
                    <LifeBuoy size={14} /> Support
                  </button>
                  <button onClick={logout}>
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="content">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
}

/** Compact activity strip reused on overview + doctor console. */
export function LivePulse({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-line">
      <Activity size={14} />
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}
