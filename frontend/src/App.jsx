import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import AppRoutes from './components/AppRoutes';
import GooeyBackground from './components/GooeyBackground';
import LightGooeyBackground from './components/LightGooeyBackground';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

const AppContent = () => {
  const { user } = React.useContext(AuthContext);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <>
      {/* Dark mode atmospheric glow — hidden in light mode via CSS */}
      <GooeyBackground />
      {/* Light mode warm ambient glow — hidden in dark mode via CSS */}
      <LightGooeyBackground />

      <div className="app-shell">
        <Navbar
          toggleSidebar={() => setSidebarOpen(s => !s)}
          sidebarOpen={sidebarOpen}
        />

        <div className="app-body">
          <Sidebar open={!!user && sidebarOpen} />

          {user && sidebarOpen && (
            <div
              onClick={() => setSidebarOpen(false)}
              style={{
                display: 'none',
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.6)',
                zIndex: 140,
              }}
              className="sidebar-overlay"
            />
          )}

          <main className="page-content">
            <Routes>
              <Route path="/login"    element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/*"        element={<AppRoutes />} />
            </Routes>
          </main>
        </div>
      </div>
    </>
  );
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
