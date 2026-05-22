import React, { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Menu, X, LogOut, Sun, Moon } from 'lucide-react';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import './Navbar.css';

/* ─────────────────────────────────────────────────────
   ThemeToggle — Premium animated sun/moon pill switch.

   DESIGN:
   - 56×28px pill, CSS spring transition
   - Dark: moon icon, right-side orb, deep fill
   - Light: sun icon, left-side orb, warm amber fill
   - Smooth spring cubic-bezier (overshoot) on orb
   - Glow pulse on orb matches current theme accent

   ACCESSIBILITY:
   - role="switch", aria-checked, aria-label
   ───────────────────────────────────────────────────── */
const ThemeToggle = () => {
  const { isLight, toggleTheme } = useContext(ThemeContext);

  return (
    <button
      className={`theme-toggle ${isLight ? 'theme-toggle--light' : 'theme-toggle--dark'}`}
      onClick={toggleTheme}
      role="switch"
      aria-checked={isLight}
      aria-label={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
      title={isLight ? 'Dark mode' : 'Light mode'}
    >
      {/* Track */}
      <span className="theme-toggle__track">
        {/* Sliding orb */}
        <span className="theme-toggle__orb" aria-hidden="true">
          <span className="theme-toggle__icon theme-toggle__icon--moon">
            <Moon size={12} strokeWidth={2.5} />
          </span>
          <span className="theme-toggle__icon theme-toggle__icon--sun">
            <Sun size={12} strokeWidth={2.5} />
          </span>
        </span>
      </span>
    </button>
  );
};

const Navbar = ({ toggleSidebar, sidebarOpen }) => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      {/* Left section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        {user && (
          <button
            className="navbar__toggle"
            onClick={toggleSidebar}
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            style={{ position: 'relative', width: 34, height: 34, overflow: 'hidden' }}
          >
            <Menu 
              size={20} 
              style={{ 
                position: 'absolute', 
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', 
                opacity: sidebarOpen ? 0 : 1, 
                transform: sidebarOpen ? 'rotate(90deg) scale(0.5)' : 'rotate(0) scale(1)' 
              }} 
            />
            <X 
              size={20} 
              style={{ 
                position: 'absolute', 
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', 
                opacity: sidebarOpen ? 1 : 0, 
                transform: sidebarOpen ? 'rotate(0) scale(1)' : 'rotate(-90deg) scale(0.5)' 
              }} 
            />
          </button>
        )}

        <Link to="/" className="navbar__brand">
          <span className="navbar__logo-icon">
            <Shield size={22} strokeWidth={3} color="#fff" />
          </span>
          <span>
            <span className="navbar__brand-name cyber-heading">ShadowWatch</span>
            <span className="navbar__brand-tag">Threat Detection Platform</span>
          </span>
        </Link>
      </div>

      {/* Right section */}
      <div className="navbar__right">
        {user ? (
          <>
            <div className="navbar__user-chip">
              <span className="navbar__user-dot" />
              {user.username}
            </div>
            <button
              className="btn btn--sm navbar__logout-btn"
              style={{ background: '#111', color: '#888', borderColor: '#333' }}
              onClick={handleLogout}
            >
              <LogOut size={14} />
              Logout
            </button>
          </>
        ) : (
          <div className="navbar__auth-links">
            <Link to="/login">
              <button className="btn btn--sm navbar__login-btn" style={{ background: 'transparent', color: 'white', borderColor: '#666' }}>
                Login
              </button>
            </Link>
            <Link to="/register">
              <button className="btn btn--sm btn--yellow">
                Register
              </button>
            </Link>
          </div>
        )}

        {/* Theme toggle — always visible */}
        <ThemeToggle />
      </div>
    </nav>
  );
};

export default Navbar;
