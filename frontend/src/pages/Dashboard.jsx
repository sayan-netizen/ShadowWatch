import React, { useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import {
  Activity, ShieldAlert, Shield, CheckCircle,
  AlertTriangle, Clock, ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

/* Risk score → bar fill color */
const riskBarColor = { high: '#FF4D8D', medium: '#FFD600', low: '#4D7CFE', safe: '#00C853' };

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [stats, setStats]   = useState(null);
  const [endpointStats, setEndpointStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/dashboard/stats'),
      api.get('/endpoint/status').catch(() => ({ data: { data: null } })) // fail gracefully
    ])
      .then(([dashRes, endRes]) => {
        setStats(dashRes.data.data);
        if (endRes.data?.data) {
          setEndpointStats(endRes.data.data);
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="loading-pulse" />
        <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700 }}>Loading dashboard…</span>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="alert-banner alert-banner--error">
        <AlertTriangle size={18} />
        Failed to load dashboard data. Check your connection.
      </div>
    );
  }

  const total = stats.total_scans || 0;
  const rb = stats.risk_breakdown || {};

  const calcPct = (n) => total > 0 ? Math.round((n / total) * 100) : 0;

  return (
    <div>
      {/* Page header */}
      <div className="dashboard__header">
        <p className="dashboard__welcome">
          // Operator: {user?.username} &nbsp;|&nbsp; Session Active
        </p>
        <h1 className="page-title cyber-heading">
          Threat <span className="title-accent">Intelligence</span>
        </h1>
      </div>

      {/* Alert banners */}
      {stats.unread_alerts_count > 0 && (
        <div className="alert-banner alert-banner--warning" style={{ marginBottom: '1rem' }}>
          <AlertTriangle size={20} />
          <span>
            You have <strong>{stats.unread_alerts_count}</strong> unread threat alert{stats.unread_alerts_count > 1 ? 's' : ''}.
          </span>
          <Link to="/profile" style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700, textDecoration: 'underline' }}>
            View alerts <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {endpointStats?.unread_alerts > 0 && (
        <div className="alert-banner alert-banner--error" style={{ marginBottom: '1rem', borderLeftColor: 'var(--accent-red)' }}>
          <ShieldAlert size={20} />
          <span>
            <strong>CRITICAL:</strong> You have <strong>{endpointStats.unread_alerts}</strong> unread endpoint threat{endpointStats.unread_alerts > 1 ? 's' : ''} detected by ShadowWatch.
          </span>
          <Link to="/endpoints" style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700, textDecoration: 'underline', color: 'var(--text-bright)' }}>
            Investigate endpoints <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Stat cards */}
      <div className="stats-grid">
        <div className="stat-card stat-card--total">
          <div className="stat-card__icon-row">
            <div className="stat-card__icon"><Activity size={22} /></div>
          </div>
          <div className="stat-card__label dot-label">Total Scans</div>
          <div className="stat-card__number cyber-heading">{total}</div>
          <div className="stat-card__sub">All-time scans performed</div>
        </div>

        <div className="stat-card stat-card--high">
          <div className="stat-card__icon-row">
            <div className="stat-card__icon"><ShieldAlert size={22} /></div>
          </div>
          <div className="stat-card__label dot-label">High Risk</div>
          <div className="stat-card__number cyber-heading">{rb.high || 0}</div>
          <div className="stat-card__sub">Keyloggers detected</div>
        </div>

        <div className="stat-card stat-card--medium">
          <div className="stat-card__icon-row">
            <div className="stat-card__icon"><Shield size={22} /></div>
          </div>
          <div className="stat-card__label dot-label">Medium / Low</div>
          <div className="stat-card__number cyber-heading">{(rb.medium || 0) + (rb.low || 0)}</div>
          <div className="stat-card__sub">Suspicious indicators found</div>
        </div>

        <div className="stat-card stat-card--safe">
          <div className="stat-card__icon-row">
            <div className="stat-card__icon"><CheckCircle size={22} /></div>
          </div>
          <div className="stat-card__label dot-label">Clean Scans</div>
          <div className="stat-card__number cyber-heading">{rb.safe || 0}</div>
          <div className="stat-card__sub">No threats detected</div>
        </div>
      </div>

      {/* Bottom section */}
      <div className="dashboard__bottom">

        {/* Recent Activity */}
        <div className="card">
          <h2 className="section-title matrix-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={18} /> Recent Activity
          </h2>
          {stats.recent_activity?.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-ui)', fontSize: '0.9rem' }}>
              No recent activity. Start by running a system scan!
            </p>
          ) : (
            <ul className="activity-feed">
              {stats.recent_activity.map(act => (
                <li className="activity-item" key={act._id}>
                  <span className="activity-item__dot" />
                  <span className="activity-item__action">
                    {act.action.replace(/_/g, ' ')}
                  </span>
                  <span className="activity-item__time">
                    {new Date(act.timestamp).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div style={{ marginTop: 'var(--space-lg)' }}>
            <Link to="/scan">
              <button className="btn btn--yellow btn--sm">
                Initiate System Scan
              </button>
            </Link>
          </div>
        </div>

        {/* Risk Breakdown */}
        <div className="card">
          <h2 className="section-title matrix-title">Risk Breakdown</h2>
          {total === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-ui)', fontSize: '0.9rem' }}>
              No data yet. Run a system scan to see breakdown.
            </p>
          ) : (
            <div className="risk-bars">
              {[
                { key: 'high',   label: 'High Risk',  count: rb.high   || 0, color: riskBarColor.high   },
                { key: 'medium', label: 'Medium',      count: rb.medium || 0, color: riskBarColor.medium },
                { key: 'low',    label: 'Low Risk',    count: rb.low    || 0, color: riskBarColor.low    },
                { key: 'safe',   label: 'Safe',        count: rb.safe   || 0, color: riskBarColor.safe   },
              ].map(({ key, label, count, color }) => (
                <div className="risk-bar-item" key={key}>
                  <div className="risk-bar-item__header">
                    <span className="risk-bar-item__label">{label}</span>
                    <span className="risk-bar-item__count">{count}</span>
                  </div>
                  <div className="score-bar-wrap">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${calcPct(count)}%`,
                        background: color,
                        border: count > 0 ? `2px solid ${color}` : 'none',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
