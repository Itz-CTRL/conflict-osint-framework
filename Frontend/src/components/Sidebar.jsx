// src/components/Sidebar.jsx
import { useState } from 'react';
import { THEMES } from '../themes';

export default function Sidebar({ theme, isOpen, onClose }) {
  const t = THEMES[theme];
  const [expandedMenus, setExpandedMenus] = useState({ tools: true, utilities: false });

  const toggleMenu = (menu) => {
    setExpandedMenus(prev => ({ ...prev, [menu]: !prev[menu] }));
  };

  return (
    <>
      {/* Backdrop overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 9998,
            animation: 'fadeIn 0.2s ease',
          }}
        />
      )}

      {/* Sidebar drawer */}
      <div style={{
        position: 'fixed',
        left: 0,
        top: 0,
        width: 280,
        height: '100vh',
        background: t.surface,
        border: `1px solid ${t.border}`,
        borderRight: `2px solid ${t.accent}`,
        padding: '16px 0',
        overflowY: 'auto',
        fontFamily: "'Sora',sans-serif",
        zIndex: 9997,
        transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.3s ease',
        boxShadow: isOpen ? `0 4px 20px rgba(0,0,0,0.3)` : 'none',
      }}>
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            padding: '8px 12px',
            background: `${t.accent}22`,
            border: `1px solid ${t.accent}44`,
            borderRadius: 6,
            color: t.accent,
            cursor: 'pointer',
            fontSize: 16,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 32,
            height: 32,
            zIndex: 9999,
          }}
          title="Close menu"
        >
          ✕
        </button>
        {/* Tools Section */}
        <div style={{ marginBottom: 4, marginTop: 40 }}>
        <button
          onClick={() => toggleMenu('tools')}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: expandedMenus.tools ? `2px solid ${t.accent}` : 'none',
            color: expandedMenus.tools ? t.accent : t.textMid,
            fontWeight: 700,
            fontSize: 12,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            letterSpacing: 0.5,
            transition: 'all 0.2s',
            textAlign: 'left',
          }}
          onMouseEnter={e => {
            if (!expandedMenus.tools) e.currentTarget.style.color = t.text;
          }}
          onMouseLeave={e => {
            if (!expandedMenus.tools) e.currentTarget.style.color = t.textMid;
          }}
        >
          🛠 TOOL AGGREGATION
          <span style={{ fontSize: 10, marginLeft: 8 }}>
            {expandedMenus.tools ? '▼' : '▶'}
          </span>
        </button>

        {expandedMenus.tools && (
          <div className="animate-slideDown">
            <ToolItem
              icon="🔍"
              label="Username Tracker"
              description="Cross-platform username search"
              available={true}
              theme={theme}
            />
            <ToolItem
              icon="📧"
              label="Email Harvester"
              description="Collect emails from sources"
              available={false}
              theme={theme}
            />
            <ToolItem
              icon="🌐"
              label="DNS Enumeration"
              description="Domain & DNS records"
              available={false}
              theme={theme}
            />
            <ToolItem
              icon="📱"
              label="Phone Lookup"
              description="Phone number investigation"
              available={false}
              theme={theme}
            />
            <ToolItem
              icon="💰"
              label="Financial Trace"
              description="Track financial footprints"
              available={false}
              theme={theme}
            />
            <ToolItem
              icon="🎓"
              label="Educational Data"
              description="School & university records"
              available={false}
              theme={theme}
            />
          </div>
        )}
      </div>

      {/* Utilities Section */}
      <div>
        <button
          onClick={() => toggleMenu('utilities')}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: 'transparent',
            border: 'none',
            borderBottom: expandedMenus.utilities ? `2px solid ${t.accent}` : 'none',
            color: expandedMenus.utilities ? t.accent : t.textMid,
            fontWeight: 700,
            fontSize: 12,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            letterSpacing: 0.5,
            transition: 'all 0.2s',
            textAlign: 'left',
          }}
          onMouseEnter={e => {
            if (!expandedMenus.utilities) e.currentTarget.style.color = t.text;
          }}
          onMouseLeave={e => {
            if (!expandedMenus.utilities) e.currentTarget.style.color = t.textMid;
          }}
        >
          ⚙ UTILITIES
          <span style={{ fontSize: 10, marginLeft: 8 }}>
            {expandedMenus.utilities ? '▼' : '▶'}
          </span>
        </button>

        {expandedMenus.utilities && (
          <div className="animate-slideDown">
            <ToolItem
              icon="💾"
              label="Export Data"
              description="Export as JSON/CSV"
              available={true}
              theme={theme}
            />
            <ToolItem
              icon="🎨"
              label="Data Visualization"
              description="Create custom charts"
              available={true}
              theme={theme}
            />
            <ToolItem
              icon="📊"
              label="Report Generator"
              description="Generate full reports"
              available={true}
              theme={theme}
            />
          </div>
        )}
      </div>
      </div>
    </>
  );
}

function ToolItem({ icon, label, description, available, theme }) {
  const t = THEMES[theme];
  const [hovered, setHovered] = useState(false);

  return (
    <button
      disabled={!available}
      style={{
        width: '100%',
        padding: '12px 16px',
        background: hovered && available ? `${t.accent}11` : 'transparent',
        border: 'none',
        borderLeft: available ? `3px solid ${hovered ? t.accent : 'transparent'}` : `3px solid ${t.border}`,
        color: available ? (hovered ? t.accent : t.text) : t.textMuted,
        cursor: available ? 'pointer' : 'not-allowed',
        textAlign: 'left',
        transition: 'all 0.15s',
        opacity: available ? 1 : 0.5,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 2 }}>
            {label}
          </div>
          <div style={{ fontSize: 10, color: t.textMuted }}>
            {description}
          </div>
        </div>
      </div>
      {!available && (
        <span style={{
          display: 'inline-block',
          marginTop: 4,
          fontSize: 9,
          color: t.textMuted,
          fontWeight: 600,
          letterSpacing: 0.5,
        }}>
          COMING SOON
        </span>
      )}
    </button>
  );
}
