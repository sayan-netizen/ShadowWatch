import React, { useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import { Server, ShieldAlert, Activity, CheckCircle, AlertTriangle, X, Terminal, Clock } from 'lucide-react';
import './Endpoints.css';

const Endpoints = () => {
  const { user } = useContext(AuthContext);
  const [statusData, setStatusData] = useState(null);
  const [alertsData, setAlertsData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [newHostName, setNewHostName] = useState('');
  const [newOsInfo, setNewOsInfo] = useState('');
  const [registrationResult, setRegistrationResult] = useState(null);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      const statusRes = await api.get('/endpoint/status');
      setStatusData(statusRes.data.data);
      
      const alertsRes = await api.get('/endpoint/alerts?limit=10');
      setAlertsData(alertsRes.data.data.alerts);
    } catch (err) {
      console.error(err);
      setError('Failed to load endpoint data. Check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 30 seconds
    const intervalId = setInterval(fetchData, 30000);
    return () => clearInterval(intervalId);
  }, []);

  const handleRegisterHost = async (e) => {
    e.preventDefault();
    setRegistering(true);
    setError('');
    try {
      const res = await api.post('/endpoint/register', {
        hostname: newHostName,
        os_info: newOsInfo || 'unknown'
      });
      setRegistrationResult(res.data.data);
      fetchData(); // Refresh list
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed');
    } finally {
      setRegistering(false);
    }
  };

  const markAlertRead = async (alertId) => {
    try {
      await api.put(`/endpoint/alerts/${alertId}/read`);
      // Optimistically update UI
      setAlertsData(prev => 
        prev.map(a => a._id === alertId ? { ...a, is_read: true } : a)
      );
      // Refresh stats
      const statusRes = await api.get('/endpoint/status');
      setStatusData(statusRes.data.data);
    } catch (err) {
      console.error('Failed to mark alert as read', err);
    }
  };

  const closeAndResetModal = () => {
    setShowModal(false);
    setRegistrationResult(null);
    setNewHostName('');
    setNewOsInfo('');
    setError('');
  };

  if (loading && !statusData) {
    return (
      <div className="loading-screen">
        <span className="loading-pulse" />
        <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700 }}>Initializing Telemetry Link...</span>
      </div>
    );
  }

  return (
    <div className="endpoints-page">
      <div className="endpoints__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p className="endpoints__welcome">
            // ShadowWatch Module Active
          </p>
          <h1 className="page-title cyber-heading">
          Endpoint <span className="title-accent">Monitoring</span>
        </h1>
        </div>
        <button className="btn btn--yellow" onClick={() => setShowModal(true)}>
          <Terminal size={18} /> Provision Agent
        </button>
      </div>

      {error && (
        <div className="alert-banner alert-banner--error" style={{ marginBottom: 'var(--space-lg)' }}>
          <AlertTriangle size={18} /> {error}
        </div>
      )}

      {/* Top Stats Grid */}
      <div className="endpoints-grid">
        <div className="endpoint-stat-card">
          <Server size={24} className="endpoint-stat-card__icon" />
          <div className="endpoint-stat-card__value cyber-heading">{statusData?.host_count || 0}</div>
          <div className="endpoint-stat-card__label dot-label">Active Endpoints</div>
        </div>
        <div className={`endpoint-stat-card ${statusData?.unread_alerts > 0 ? 'endpoint-stat-card--danger' : ''}`}>
          <ShieldAlert size={24} className="endpoint-stat-card__icon" style={{ color: statusData?.unread_alerts > 0 ? 'var(--accent-red)' : '' }} />
          <div className="endpoint-stat-card__value cyber-heading" style={{ color: statusData?.unread_alerts > 0 ? 'var(--accent-red)' : '' }}>
            {statusData?.unread_alerts || 0}
          </div>
          <div className="endpoint-stat-card__label dot-label">Unread Threats</div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr', gap: 'var(--space-lg)' }}>
        {/* Monitored Hosts Table */}
        <div className="card">
          <h2 className="section-title matrix-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={18} /> Connected Hosts
          </h2>
          {statusData?.monitored_hosts?.length === 0 ? (
             <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '1rem' }}>
               No endpoints are currently being monitored. Click "Provision Agent" to begin.
             </p>
          ) : (
            <div className="hosts-table-container">
              <table className="hosts-table">
                <thead>
                  <tr>
                    <th>Hostname</th>
                    <th>OS</th>
                    <th>Status</th>
                    <th>Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {statusData?.monitored_hosts?.map(host => (
                    <tr key={host.host_id}>
                      <td style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{host.hostname}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{host.os_info}</td>
                      <td>
                        <span className={`status-badge status-badge--${host.status.toLowerCase()}`}>
                          {host.status === 'online' ? <Activity size={12} /> : null}
                          {host.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>
                        {host.last_seen ? new Date(host.last_seen).toLocaleString() : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Threat Feed */}
        <div className="card">
          <h2 className="section-title matrix-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldAlert size={18} /> Threat Feed
          </h2>
          {alertsData.length === 0 ? (
             <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '1rem' }}>
               No alerts. All endpoints are secure.
             </p>
          ) : (
            <ul className="alerts-feed">
              {alertsData.map(alert => (
                <li key={alert._id} className={`alert-item ${!alert.is_read ? 'alert-item--unread' : ''}`}>
                  <div className="alert-item__icon">
                    {alert.threat_level === 'MALICIOUS' ? (
                      <AlertTriangle size={18} color="var(--accent-red)" />
                    ) : alert.threat_level === 'SUSPICIOUS' ? (
                      <AlertTriangle size={18} color="var(--accent-yellow)" />
                    ) : (
                      <CheckCircle size={18} color="var(--accent-green)" />
                    )}
                  </div>
                  <div className="alert-item__content">
                    <div className="alert-item__message">{alert.message}</div>
                    <div className="alert-item__meta">
                      <span><Clock size={12} style={{ display: 'inline', marginRight: 4 }}/>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                      <span>Host: {alert.hostname}</span>
                    </div>
                  </div>
                  {!alert.is_read && (
                    <div className="alert-item__action">
                      <button 
                        className="btn btn--outline" 
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        onClick={() => markAlertRead(alert._id)}
                      >
                        Mark Read
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Provision Agent Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close" onClick={closeAndResetModal}>
              <X size={24} />
            </button>
            <h2 className="modal-title matrix-title">Provision New Agent</h2>
            
            {registrationResult ? (
              <div>
                <div className="alert-banner alert-banner--success" style={{ marginBottom: '1rem' }}>
                  <CheckCircle size={18} /> Host Registered Successfully
                </div>
                <p style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>
                  Deploy the ShadowWatch agent on <strong>{newHostName}</strong> using the following command. 
                  <br/><br/>
                  <span style={{ color: 'var(--accent-red)', fontWeight: 'bold' }}>WARNING:</span> This API key will only be shown once.
                </p>
                
                <div className="api-key-box">
                  {registrationResult.api_key}
                </div>
                
                <div className="form-group">
                  <label className="form-label">Deployment Command (Powershell/CMD)</label>
                  <textarea 
                    className="form-input" 
                    readOnly 
                    rows="2" 
                    style={{ fontFamily: 'var(--font-code)', fontSize: '0.85rem' }}
                    value={`python monitor.py --server ${window.location.origin.replace('5173', '5000')} --api-key ${registrationResult.api_key}`}
                  />
                </div>
                
                <button className="btn btn--primary btn--full" onClick={closeAndResetModal} style={{ marginTop: '1rem' }}>
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleRegisterHost}>
                <p style={{ marginBottom: '1.5rem', color: 'var(--text-muted)' }}>
                  Register a new host to receive an API key for the ShadowWatch endpoint agent.
                </p>
                <div className="form-group">
                  <label className="form-label">Hostname</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newHostName}
                    onChange={(e) => setNewHostName(e.target.value)}
                    placeholder="e.g., DESKTOP-X1Y2Z3"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">OS Info (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newOsInfo}
                    onChange={(e) => setNewOsInfo(e.target.value)}
                    placeholder="e.g., Windows 11"
                  />
                </div>
                <button 
                  type="submit" 
                  className="btn btn--yellow btn--full" 
                  disabled={registering || !newHostName}
                  style={{ marginTop: '1rem' }}
                >
                  {registering ? 'Generating Key...' : 'Generate API Key'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default Endpoints;
