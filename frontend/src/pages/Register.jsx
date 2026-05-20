import React, { useState, useContext } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { ShieldAlert, AlertCircle, Lock, User, Mail, CheckCircle } from 'lucide-react';
import './Auth.css';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const { register, user } = useContext(AuthContext);
  const navigate = useNavigate();

  if (user) return <Navigate to="/dashboard" />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await register(username, email, password);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Hero panel */}
      <div className="auth-hero">
        <p className="auth-hero__eyebrow">
          <ShieldAlert size={14} />
          Join PhishGuard
        </p>
        <h1 className="auth-hero__title">
          Protect Your<br />
          <span>Digital Life.</span>
        </h1>
        <p className="auth-hero__desc">
          Create a free PhishGuard account and start scanning suspicious URLs
          instantly. Your security intelligence dashboard awaits.
        </p>
        <ul className="auth-hero__features">
          <li>Free account — no credit card</li>
          <li>Unlimited URL scans</li>
          <li>Persistent scan history</li>
          <li>Real-time threat alerts</li>
        </ul>
      </div>

      {/* Form panel */}
      <div className="auth-form-panel">
        <p className="auth-form-panel__eyebrow">Get started</p>
        <h2 className="auth-form-panel__title">
          Create <span>Account</span>
        </h2>

        {error && (
          <div className="alert-banner alert-banner--error" style={{ marginBottom: 'var(--space-lg)' }}>
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} id="register-form">
          <div className="field">
            <label htmlFor="reg-username">
              <User size={12} style={{ display: 'inline', marginRight: 4 }} />
              Username
            </label>
            <input
              id="reg-username"
              type="text"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-email">
              <Mail size={12} style={{ display: 'inline', marginRight: 4 }} />
              Email Address
            </label>
            <input
              id="reg-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="reg-password">
              <Lock size={12} style={{ display: 'inline', marginRight: 4 }} />
              Password
            </label>
            <input
              id="reg-password"
              type="password"
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              minLength="6"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn--yellow btn--lg btn--full auth-form__submit"
            disabled={loading}
            id="register-submit-btn"
          >
            <CheckCircle size={18} />
            {loading ? 'Creating Account...' : 'Create My Account'}
          </button>
        </form>

        <div className="auth-form__footer">
          Already have an account?&nbsp;
          <Link to="/login">Sign in →</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
