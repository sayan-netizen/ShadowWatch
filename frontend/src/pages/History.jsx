import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Clock, ScanSearch, ShieldAlert, ShieldCheck, Shield } from 'lucide-react';
import './History.css';

const BADGE_CLASS = {
  High:   'badge--high',
  Medium: 'badge--medium',
  Low:    'badge--low',
  Safe:   'badge--safe',
};

const SCORE_BAR_COLOR = {
  High:   '#FF4D8D',
  Medium: '#FFD600',
  Low:    '#4D7CFE',
  Safe:   '#00C853',
};

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/scans/history')
      .then(r => setHistory(r.data.data.history || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="loading-pulse" />
        <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700 }}>Loading history…</span>
      </div>
    );
  }

  const totalScans  = history.length;
  const highCount   = history.filter(s => s.risk_level === 'High').length;
  const safeCount   = history.filter(s => s.risk_level === 'Safe').length;

  return (
    <div>
      <h1 className="page-title">
        Scan <span className="title-accent">History</span>
      </h1>

      {/* Stats strip */}
      {totalScans > 0 && (
        <div className="history-stats-strip">
          <div className="history-stats-strip__chip">
            <Clock size={16} />
            <strong>{totalScans}</strong>
            Total Scans
          </div>
          <div className="history-stats-strip__chip" style={{ background: 'var(--pink)', color: 'white', borderColor: '#000' }}>
            <ShieldAlert size={16} />
            <strong>{highCount}</strong>
            High Risk
          </div>
          <div className="history-stats-strip__chip" style={{ background: 'var(--green)', borderColor: '#000' }}>
            <ShieldCheck size={16} />
            <strong>{safeCount}</strong>
            Safe
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {totalScans === 0 ? (
          <div className="history-empty">
            <div className="history-empty__icon">
              <ScanSearch size={36} />
            </div>
            <h3 className="history-empty__title">No Scans Yet</h3>
            <p className="history-empty__desc">
              Your scan history will appear here. Start by analyzing your local system.
            </p>
            <Link to="/scan">
              <button className="btn btn--yellow">Go to Scanner</button>
            </Link>
          </div>
        ) : (
          <div className="history-table-wrap" style={{ overflowX: 'auto' }}>
            <table className="neo-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th><Clock size={12} style={{ display: 'inline', marginRight: 4 }} />Date &amp; Time</th>
                  <th>Target</th>
                  <th>Risk Level</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {history.map((scan, index) => (
                  <tr key={scan._id}>
                    <td style={{ color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.8rem', width: 40 }}>
                      {index + 1}
                    </td>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {new Date(scan.timestamp).toLocaleString()}
                    </td>
                    <td className="url-cell">
                      <span className="url-cell__text" title={scan.url}>
                        {scan.url}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${BADGE_CLASS[scan.risk_level] || ''}`}>
                        {scan.risk_level?.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div className="score-chip">
                        <span>{scan.risk_score}</span>
                        <span className="score-chip__bar">
                          <span
                            className="score-chip__bar-fill"
                            style={{
                              width: `${scan.risk_score}%`,
                              background: SCORE_BAR_COLOR[scan.risk_level] || '#999',
                            }}
                          />
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
