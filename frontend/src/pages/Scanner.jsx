import React, { useState } from 'react';
import api from '../services/api';
import {
  ScanSearch, ShieldAlert, ShieldCheck, Shield,
  AlertCircle, Activity, List
} from 'lucide-react';
import './Scanner.css';

const RISK_HEADER_CLASS = {
  High:   'result-header--high',
  Medium: 'result-header--medium',
  Low:    'result-header--low',
  Safe:   'result-header--safe',
};

const RISK_ICON = {
  High:   <ShieldAlert size={32} />,
  Medium: <Shield size={32} />,
  Low:    <Shield size={32} />,
  Safe:   <ShieldCheck size={32} />,
};

const RISK_SCORE_BAR_COLOR = {
  High:   '#FF4D8D',
  Medium: '#FFD600',
  Low:    '#4D7CFE',
  Safe:   '#00C853',
};

const Scanner = () => {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const handleScan = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await api.post('/scans/analyze', {});
      setResult(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Error scanning URL. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title cyber-heading">
        System <span className="title-accent">Scanner</span>
      </h1>

      {/* Hero input panel */}
      <div className="scanner__hero">
        <p className="scanner__hero-eyebrow">
          Heuristic Keylogger Detection Engine
        </p>
        <h2 className="scanner__hero-title cyber-heading">
          Analyze <span>Local Threats</span>
        </h2>

        <form onSubmit={handleScan} id="scanner-form">
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-lg)' }}>
            <button
              type="submit"
              className="btn btn--yellow btn--lg"
              id="scan-submit-btn"
              disabled={loading}
              style={{ paddingLeft: '3rem', paddingRight: '3rem' }}
            >
              {loading ? 'Scanning System...' : 'Initiate System Scan'}
            </button>
          </div>
        </form>

        <div className="scanner__tips">
          <span className="scanner__tip">process analysis</span>
          <span className="scanner__tip">hook detection</span>
          <span className="scanner__tip">signature matching</span>
          <span className="scanner__tip">behavioral heuristics</span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="alert-banner alert-banner--error">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Scan Result */}
      {result && (
        <div className="result-panel" style={{ boxShadow: 'var(--shadow-xl)' }}>
          {/* Colored header */}
          <div className={`result-header ${RISK_HEADER_CLASS[result.risk_level] || ''}`}>
            <div className="result-header__icon">
              {RISK_ICON[result.risk_level] || <Shield size={24} />}
            </div>
            <div style={{ flex: 1 }}>
              <div className="result-header__level">Risk Assessment</div>
              <div className="result-header__verdict cyber-heading">
                {result.risk_level.toUpperCase()} RISK
              </div>
              <div className="result-header__score-label">Threat Score</div>
              <div className="result-header__score-bar">
                <span className="result-header__score-number">{result.risk_score}<span style={{ fontSize: '0.7rem', opacity: 0.5 }}>/100</span></span>
                <div style={{ flex: 1, maxWidth: 160 }}>
                  <div className="score-bar-wrap">
                    <div
                      className="score-bar-fill"
                      style={{ width: `${result.risk_score}%`, background: RISK_SCORE_BAR_COLOR[result.risk_level] || '#333' }}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div>
              <span className={`badge badge--${result.risk_level.toLowerCase()}`}>
                {result.risk_level}
              </span>
            </div>
          </div>

          {/* Body: Target + Indicators */}
          <div className="result-body">
            {/* Target section */}
            <div className="result-body__section">
              <div className="result-body__section-title">
                <Activity size={12} />
                Analyzed Target
              </div>
              <div className="result-url">{result.url || 'Local System'}</div>
            </div>

            {/* Indicators section */}
            <div className="result-body__section">
              <div className="result-body__section-title">
                <List size={12} />
                Indicators Found ({result.indicators?.length || 0})
              </div>
              {result.indicators?.length > 0 ? (
                <ul className={`indicators-list${result.risk_level === 'Safe' ? ' indicators-list--safe' : ''}`}>
                  {result.indicators.map((ind, idx) => (
                    <li key={idx}>{ind}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  No indicators detected.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Scanner;
