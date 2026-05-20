import React, { useState, useContext } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { Shield, ShieldCheck, AlertCircle, Lock, User } from 'lucide-react';
import './Auth.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const { login, user } = useContext(AuthContext);
  const navigate = useNavigate();

  if (user) return <Navigate to="/dashboard" />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Hero panel */}
      <div className="auth-hero">
        <p className="auth-hero__eyebrow">
          Threat Detection Platform
        </p>
        <h1 className="auth-hero__title">
          Keylogger<br />
          <span>Detection</span> System
        </h1>
        <p className="auth-hero__desc">
          ShadowWatch applies process scanning and behavioral heuristics to 
          detect active keyloggers on the local system.
        </p>
        <ul className="auth-hero__features">
          <li>Real-time local system scanning</li>
          <li>Process heuristic scoring engine</li>
          <li>Persistent scan log</li>
          <li>High-risk incident alerts</li>
        </ul>
      </div>

      {/* Form panel */}
      <div className="auth-form-panel">
        <p className="auth-form-panel__eyebrow">// Operator Authentication</p>
        <h2 className="auth-form-panel__title">
          Access <span>Control</span>
        </h2>

        {error && (
          <div className="alert-banner alert-banner--error" style={{ marginBottom: 'var(--space-lg)' }}>
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} id="login-form">
          <div className="field">
            <label htmlFor="login-username">
              <User size={12} style={{ display: 'inline', marginRight: 4 }} />
              Username
            </label>
            <input
              id="login-username"
              type="text"
              placeholder="e.g. john_doe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="login-password">
              <Lock size={12} style={{ display: 'inline', marginRight: 4 }} />
              Password
            </label>
            <input
              id="login-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn--yellow btn--full auth-form__submit"
            disabled={loading}
            id="login-submit-btn"
          >
            {loading ? 'Authenticating...' : 'Authenticate'}
          </button>
        </form>

        <div className="auth-form__footer">
          No account? &nbsp;
          <a href="/register">Request access →</a>
        </div>
      </div>
    </div>
  );
};

export default Login;
