// src/components/RateLimitWarning.jsx
import { useState, useEffect } from 'react';
import { THEMES } from '../themes';

export default function RateLimitWarning({ theme, rateLimitInfo, visible = false }) {
  const t = THEMES[theme];
  const [show, setShow] = useState(visible);

  useEffect(() => {
    setShow(visible && rateLimitInfo && rateLimitInfo.status !== 'ok');
  }, [visible, rateLimitInfo]);

  if (!show || !rateLimitInfo) {
    return null;
  }

  const isWarning = rateLimitInfo.status === 'warning';
  const isBlocked = rateLimitInfo.status === 'blocked';

  const bgColor = isBlocked 
    ? 'rgba(239, 68, 68, 0.1)' 
    : 'rgba(245, 158, 11, 0.1)';
  
  const borderColor = isBlocked 
    ? '#ef4444' 
    : '#f59e0b';
  
  const textColor = isBlocked 
    ? '#dc2626' 
    : '#d97706';

  const icon = isBlocked ? '⏸️' : '⚠️';

  return (
    <div
      style={{
        background: bgColor,
        border: `2px solid ${borderColor}`,
        borderRadius: 12,
        padding: '16px 20px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        animation: isBlocked ? 'pulse 1s infinite' : 'none',
      }}
    >
      <span style={{ fontSize: '20px' }}>{icon}</span>
      
      <div style={{ flex: 1 }}>
        <p
          style={{
            margin: '0 0 4px 0',
            fontWeight: 'bold',
            color: textColor,
            fontSize: '14px',
            fontFamily: "'Sora', sans-serif",
          }}
        >
          {rateLimitInfo.message}
        </p>
        
        <p
          style={{
            margin: 0,
            color: textColor,
            fontSize: '12px',
            fontFamily: "'Sora', sans-serif",
            opacity: 0.8,
          }}
        >
          {rateLimitInfo.remaining}/{rateLimitInfo.limit} requests remaining in{' '}
          {rateLimitInfo.window_seconds}s window
          {rateLimitInfo.reset_in > 0 && ` • Reset in ${Math.ceil(rateLimitInfo.reset_in)}s`}
        </p>
      </div>

      {isBlocked && (
        <button
          onClick={() => setShow(false)}
          style={{
            background: 'none',
            border: 'none',
            color: textColor,
            cursor: 'pointer',
            fontSize: '20px',
            padding: 0,
          }}
        >
          ×
        </button>
      )}

      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
        `}
      </style>
    </div>
  );
}
