// src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

import { THEMES } from './themes';
import { api } from './utils/api';

import Header from './components/Header';
import Ticker from './components/Ticker';
import Dashboard from './components/Dashboard';
import CasePage from './components/CasePage';
import ThemeButton from './components/ThemeButton';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('soko-theme') || 'dark');
  const [online, setOnline] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Persist theme
  useEffect(() => {
    localStorage.setItem('soko-theme', theme);
  }, [theme]);

  // Check backend health on mount and every 30s
  useEffect(() => {
    const check = async () => {
      try {
        await api.health();
        setOnline(true);
      } catch {
        setOnline(false);
      }
    };
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  const t = THEMES[theme];

  return (
    <BrowserRouter>
      <div style={{
        minHeight: '100vh',
        background: t.bgGrad,
        color: t.text,
        fontFamily: "'Sora', sans-serif",
        transition: 'background 0.4s, color 0.3s',
      }}>
        <Header theme={theme} online={online} />
        <Ticker theme={theme} />

        {/* Offline banner */}
        {!online && (
          <div style={{
            background: `${t.riskHigh}22`,
            border: `1px solid ${t.riskHigh}44`,
            borderRadius: 0,
            padding: '8px 24px',
            fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.riskHigh,
            textAlign: 'center',
          }}>
            ⚠ Backend offline — start the Flask server: <code style={{ fontFamily: "'JetBrains Mono',monospace" }}>python app.py</code>
          </div>
        )}

        <Routes>
          <Route path="/"          element={<Dashboard theme={theme} sidebarOpen={sidebarOpen} onSidebarClose={() => setSidebarOpen(false)} />} />
          <Route path="/case/:id"  element={<CasePage  theme={theme} sidebarOpen={sidebarOpen} onSidebarClose={() => setSidebarOpen(false)} />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>

        {/* Floating draggable theme switcher */}
        <ThemeButton currentTheme={theme} onTheme={setTheme} />
      </div>
    </BrowserRouter>
  );
}
