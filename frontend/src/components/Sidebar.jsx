import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ScanSearch, Clock, User, Zap } from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/endpoints', icon: Zap,             label: 'Endpoints', badge: 'NEW' },
  { to: '/scan',      icon: ScanSearch,       label: 'System Scanner', badge: 'HOT' },
  { to: '/history',   icon: Clock,             label: 'History' },
  { to: '/profile',   icon: User,              label: 'Profile' },
];

const Sidebar = ({ open }) => {
  return (
    <aside className={`sidebar ${open ? 'sidebar--open' : 'sidebar--closed'}`} aria-label="Sidebar navigation">
      <div className="sidebar__header">
        <span className="sidebar__header-label">Navigation</span>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' active' : ''}`
            }
          >
            <Icon size={18} className="sidebar__link-icon" />
            <span className="sidebar__link-text">{label}</span>
            {badge && <span className="sidebar__link-badge">{badge}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Zap size={12} />
          ShadowWatch v1.0
        </span>
      </div>
    </aside>
  );
};

export default Sidebar;
