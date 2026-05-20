import React, { useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import { Bell, User, Lock, Mail, CheckCircle, AlertCircle, ShieldAlert } from 'lucide-react';
import './Profile.css';

const Profile = () => {
  const { user } = useContext(AuthContext);
  const [alerts,   setAlerts]   = useState([]);
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [message,  setMessage]  = useState({ text: '', type: '' });

  useEffect(() => {
    if (user) setEmail(user.email || '');
    fetchAlerts();
  }, [user]);

  const fetchAlerts = async () => {
    try {
      const res = await api.get('/user/alerts');
      setAlerts(res.data.data?.alerts || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setMessage({ text: '', type: '' });
    try {
      const data = {};
      if (email !== user.email) data.email = email;
      if (password)             data.password = password;

      if (Object.keys(data).length === 0) {
        setMessage({ text: 'No changes to save.', type: 'info' });
        return;
      }

      await api.put('/user/profile', data);
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      setPassword('');
    } catch (err) {
      setMessage({ text: err.response?.data?.message || 'Failed to update profile.', type: 'error' });
    }
  };

  const markAlertRead = async (id) => {
    try {
      await api.put(`/user/alerts/${id}/read`);
      fetchAlerts();
    } catch (err) {
      console.error(err);
    }
  };

  if (!user) return null;

  const unreadCount = alerts.filter(a => !a.is_read).length;

  const initials = user.username
    ? user.username.slice(0, 2).toUpperCase()
    : '??';

  return (
    <div>
      <h1 className="page-title">
        My <span className="title-accent">Profile</span>
      </h1>

      <div className="profile-page">

        {/* ─── Left: account settings ─── */}
        <div>
          {/* Avatar block */}
          <div className="profile-avatar-block">
            <div className="profile-avatar">{initials}</div>
            <div>
              <div className="profile-avatar-block__name">{user.username}</div>
              <div className="profile-avatar-block__meta">{user.email}</div>
              {user.created_at && (
                <div className="profile-avatar-block__meta">
                  Member since {new Date(user.created_at).toLocaleDateString()}
                </div>
              )}
              <span className="profile-avatar-block__badge">Active User</span>
            </div>
          </div>

          {/* Edit form */}
          <div className="card">
            <h2 className="section-title">
              <User size={16} style={{ display: 'inline', marginRight: 6 }} />
              Account Settings
            </h2>

            {message.text && (
              <div
                className={`alert-banner ${
                  message.type === 'success' ? 'alert-banner--success' :
                  message.type === 'error'   ? 'alert-banner--error'   :
                  'alert-banner--warning'
                }`}
                style={{ marginBottom: 'var(--space-lg)' }}
              >
                {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                {message.text}
              </div>
            )}

            <form className="profile-form" onSubmit={handleUpdateProfile} id="profile-form">
              <div className="field">
                <label htmlFor="profile-email">
                  <Mail size={11} style={{ display: 'inline', marginRight: 4 }} />
                  Email Address
                </label>
                <input
                  id="profile-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="profile-password">
                  <Lock size={11} style={{ display: 'inline', marginRight: 4 }} />
                  New Password
                </label>
                <input
                  id="profile-password"
                  type="password"
                  placeholder="Leave blank to keep current"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength="6"
                />
              </div>

              <button
                type="submit"
                className="btn btn--yellow btn--full"
                id="profile-save-btn"
              >
                <CheckCircle size={16} />
                Save Changes
              </button>
            </form>
          </div>
        </div>

        {/* ─── Right: alerts panel ─── */}
        <div>
          <div className="card">
            <div className="alerts-section-title">
              <h2 className="section-title" style={{ marginBottom: 0, borderBottom: 'none' }}>
                <Bell size={16} style={{ display: 'inline', marginRight: 6 }} />
                Alerts
              </h2>
              {unreadCount > 0 && (
                <span className="badge badge--high">{unreadCount} NEW</span>
              )}
            </div>

            {alerts.length === 0 ? (
              <div className="alerts-empty">
                <ShieldAlert size={40} strokeWidth={1.5} style={{ margin: '0 auto 1rem', display: 'block', opacity: 0.3 }} />
                No alerts yet. High-risk scans will appear here.
              </div>
            ) : (
              <div className="alerts-list">
                {alerts.map(alert => (
                  <div
                    key={alert._id}
                    className={`alert-card ${alert.is_read ? 'alert-card--read' : 'alert-card--unread'}`}
                  >
                    <span className={`alert-card__dot ${alert.is_read ? 'alert-card__dot--read' : ''}`} />
                    <div className="alert-card__body">
                      <div className="alert-card__message">{alert.message}</div>
                      <div className="alert-card__time">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                    {!alert.is_read && (
                      <button
                        className="btn btn--sm"
                        onClick={() => markAlertRead(alert._id)}
                        title="Mark as read"
                      >
                        ✓ Read
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Profile;
