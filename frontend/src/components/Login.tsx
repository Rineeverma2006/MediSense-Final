import { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, ArrowRight, HeartPulse, Lock, Mail, ShieldCheck, Stethoscope, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiError } from '../services/api';
import { ErrorBox } from './ui';

type Mode = 'login' | 'register';

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'register') {
      if (password.length < 8) {
        setError('Password must be at least 8 characters.');
        return;
      }
      if (password !== confirm) {
        setError('Passwords do not match.');
        return;
      }
    }

    setBusy(true);
    try {
      if (mode === 'login') await login(email.trim(), password);
      else await register(email.trim(), name.trim(), password);
    } catch (err) {
      setError(apiError(err, 'Authentication failed. Please try again.'));
    } finally {
      setBusy(false);
    }
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setError('');
  };

  return (
    <div className="login-screen">
      <div className="login-art">
        <div className="login-anatomy-glow" aria-hidden="true" />
        <img className="login-anatomy-figure" src="/images/login-anatomy.png" alt="" aria-hidden="true" />
        <div className="brand-mark">
          <HeartPulse size={26} />
        </div>
        <div className="art-copy">
          <div className="eyebrow" style={{ color: '#D7B879' }}>
            HEALTH INTELLIGENCE
          </div>
          <h1>
            Your health,
            <br />
            finally legible.
          </h1>
          <p>
            Upload a lab report and get every parameter decoded against its reference range, track
            vitals over time, and talk to an AI assistant grounded in your own records.
          </p>
        </div>

        <div className="art-pulse">
          <span />
          <span />
          <span />
        </div>

        <div className="art-foot">
          <div>
            <Stethoscope size={16} />
            <span>Report analyzer</span>
          </div>
          <div>
            <Activity size={16} />
            <span>Vitals timeline</span>
          </div>
          <div>
            <ShieldCheck size={16} />
            <span>Per-user isolation</span>
          </div>
        </div>
      </div>

      <div className="login-panel">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'CREATE ACCOUNT'}</div>
          <h2>{mode === 'login' ? 'Sign in to MediSense' : 'Start your health record'}</h2>
          <p className="muted" style={{ marginBottom: 20 }}>
            {mode === 'login'
              ? 'Use the email and password you registered with.'
              : 'Patients receive a private workspace. Clinician and admin roles are assigned by an administrator.'}
          </p>

          <form onSubmit={submit} className="auth-form">
            {mode === 'register' && (
              <label>
                Full name
                <div className="input-wrap">
                  <UserRound size={14} />
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Rohit Sharma"
                    autoComplete="name"
                    required
                    minLength={2}
                  />
                </div>
              </label>
            )}

            <label>
              Email address
              <div className="input-wrap">
                <Mail size={14} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </div>
            </label>

            <label>
              Password
              <div className="input-wrap">
                <Lock size={14} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  required
                  minLength={8}
                />
              </div>
            </label>

            {mode === 'register' && (
              <label>
                Confirm password
                <div className="input-wrap">
                  <Lock size={14} />
                  <input
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="Repeat your password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                  />
                </div>
              </label>
            )}

            {error && <ErrorBox message={error} />}

            <button type="submit" className="btn primary full" disabled={busy}>
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
              {!busy && <ArrowRight size={15} />}
            </button>
          </form>

          <div className="auth-switch">
            {mode === 'login' ? (
              <>
                New to MediSense?{' '}
                <button type="button" className="text-btn" onClick={() => switchMode('register')}>
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already registered?{' '}
                <button type="button" className="text-btn" onClick={() => switchMode('login')}>
                  Sign in instead
                </button>
              </>
            )}
          </div>

          <p className="small-note" style={{ marginTop: 22, lineHeight: 1.7 }}>
            MediSense provides informational analysis only and is not a substitute for professional
            medical advice, diagnosis or treatment. In an emergency, contact local emergency services.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
