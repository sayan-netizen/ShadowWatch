import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import AppRoutes from './components/AppRoutes';
import GooeyBackground from './components/GooeyBackground';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

const AppContent = () => {
  const { user } = React.useContext(AuthContext);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <>
      {/* Cinematic atmospheric layer — fixed, z-index 0, behind everything */}
      <GooeyBackground />

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
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
