// src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

import { THEMES } from './themes';
import { api } from './utils/api';

import { CaseProvider } from './contexts/CaseContext';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import CasePage from './components/CasePage';
import ThemeButton from './components/ThemeButton';

export default function App() {
  const [theme,  setTheme]  = useState(() => localStorage.getItem('soko-theme') || 'dark');
  const [online, setOnline] = useState(false);

  // Persist theme
  useEffect(() => {
    localStorage.setItem('soko-theme', theme);
  }, [theme]);

  // Health-check every 30 s
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
      <CaseProvider>
        <div style={{
          minHeight: '100vh',
          background: t.bgGrad,
          color: t.text,
          fontFamily: "'Sora', sans-serif",
        }}>
          <Header theme={theme} online={online} />

          {/* Offline banner */}
          {!online && (
            <div style={{
              background: `${t.riskHigh}22`,
              border: `1px solid ${t.riskHigh}44`,
              padding: '8px 24px',
              fontFamily: "'Sora',sans-serif", fontSize: 13, color: t.riskHigh,
              textAlign: 'center',
            }}>
              ⚠ Backend offline — start the Flask server:{' '}
              <code style={{ fontFamily: "'JetBrains Mono',monospace" }}>python app.py</code>
            </div>
          )}

          <Routes>
            <Route path="/"         element={<Dashboard theme={theme} />} />
            <Route path="/case/:id" element={<CasePage  theme={theme} />} />
            <Route path="*"         element={<Navigate to="/" replace />} />
          </Routes>

          {/* Floating theme switcher */}
          <ThemeButton currentTheme={theme} onTheme={setTheme} />
        </div>
      </CaseProvider>
    </BrowserRouter>
  );
}
