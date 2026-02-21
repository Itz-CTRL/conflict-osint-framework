// src/components/Dashboard.jsx
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { StatCard, Card, SectionTitle, StatusBadge, EmptyState, Alert, Spinner } from './UI';
import Sidebar from './Sidebar';

export default function Dashboard({ theme, sidebarOpen, onSidebarClose }) {
  const t = THEMES[theme];
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingInvs, setLoadingInvs] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [error, setError] = useState('');
  const [inputFocused, setInputFocused] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({ location: '', country: '', organization: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const loadInvestigations = useCallback(async () => {
    setLoadingInvs(true);
    try {
      const data = await api.getInvestigations();
      setInvestigations(data.sort((a, b) => b.id - a.id));
    } catch {
      setInvestigations([]);
    } finally {
      setLoadingInvs(false);
    }
  }, []);

  useEffect(() => { loadInvestigations(); }, [loadInvestigations]);

  const startInvestigation = async () => {
    const name = username.trim();
    if (!name || name.length < 2) {
      setError('Please enter a username (at least 2 characters).');
      return;
    }
    setError('');
    setLoading(true);

    try {
      setLoadingStatus(`Creating investigation for @${name}...`);
      const inv = await api.createInvestigation(name);

      setLoadingStatus(`Scanning all platforms for @${name}... (30–60 seconds)`);
      await api.runInvestigation(inv.id);

      navigate(`/case/${inv.id}`);
    } catch (e) {
      setError(`Error: ${e.message}`);
      setLoading(false);
    }
  };

  const deleteInvestigation = async (invId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this investigation?')) return;
    
    setDeleting(invId);
    try {
      await api.deleteInvestigation(invId);
      setInvestigations(investigations.filter(i => i.id !== invId));
    } catch (e) {
      setError(`Error deleting: ${e.message}`);
    } finally {
      setDeleting(null);
    }
  };

  // Extract filter options from investigations
  const getFilterOptions = () => {
    const locations = new Set();
    const countries = new Set();
    const organizations = new Set();

    investigations.forEach(inv => {
      // This is a simplified approach - in a real scenario you'd parse the investigation data
      // For now we'll add some placeholder structure that can be enhanced
      locations.add('Unknown');
    });

    return {
      locations: Array.from(locations),
      countries: Array.from(countries),
      organizations: Array.from(organizations),
    };
  };

  // Filter investigations based on active filters
  const filteredInvestigations = investigations.filter(inv => {
    // Apply any active filters here
    return true; // For now, return all
  });

  // Stats derived from investigations
  const completed = investigations.filter(i => i.status === 'completed').length;
  const running   = investigations.filter(i => i.status === 'running').length;
  const failed    = investigations.filter(i => i.status === 'failed').length;
  const total     = investigations.length;

  return (
    <>
      {/* Sidebar Drawer (controlled by App) */}
      <Sidebar theme={theme} isOpen={sidebarOpen} onClose={onSidebarClose} />

      {/* Main Content */}
      <div className="animate-fadeIn" style={{ padding: '24px 20px', maxWidth: 1400, margin: '0 auto' }}>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 28 }}>
        <StatCard theme={theme} label="Total Investigations" value={total} />
        <StatCard theme={theme} label="Completed"  value={completed} positive />
        <StatCard theme={theme} label="In Progress" value={running} />
        <StatCard theme={theme} label="Failed" value={failed} positive={false} />
      </div>

      {/* Investigation Input */}
      <Card theme={theme} style={{ padding: 28, marginBottom: 24 }}>
        <SectionTitle icon="◎" title="Start New Investigation" theme={theme} />

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && startInvestigation()}
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
            placeholder="Enter username to investigate (e.g. elonmusk, spez, torvalds)"
            disabled={loading}
            style={{
              flex: 1, minWidth: 240,
              padding: '12px 18px',
              background: t.inputBg,
              border: `1px solid ${inputFocused ? t.accent : t.border}`,
              borderRadius: 10, color: t.text,
              fontFamily: "'Sora',sans-serif", fontSize: 14,
              outline: 'none',
              transition: 'border-color 0.2s',
              boxShadow: inputFocused ? `0 0 0 3px ${t.accent}22` : 'none',
            }}
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            style={{
              padding: '12px 20px',
              background: showFilters ? `${t.accent}22` : t.border,
              color: showFilters ? t.accent : t.textMid,
              border: `1px solid ${showFilters ? t.accent : t.border}`,
              borderRadius: 10,
              cursor: 'pointer',
              fontFamily: "'Sora',sans-serif",
              fontWeight: 700,
              fontSize: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              transition: 'all 0.2s',
            }}
          >
            🔽 Filters
          </button>
          <button
            onClick={startInvestigation}
            disabled={loading}
            style={{
              padding: '12px 28px',
              background: loading ? t.border : t.accentGrad,
              color: '#fff', border: 'none', borderRadius: 10,
              fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 10,
              boxShadow: loading ? 'none' : `0 4px 20px ${t.accent}55`,
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            {loading ? <><Spinner size={16} /> Scanning...</> : '🔍 Start Investigation'}
          </button>
        </div>

        {/* Filters Section Below Input */}
        {showFilters && (
          <div className="animate-slideDown" style={{
            marginTop: 16,
            padding: '16px 20px',
            background: t.surfaceAlt,
            borderRadius: 8,
            border: `1px solid ${t.border}`,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 12,
          }}>
            <div>
              <label style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, fontWeight: 700, color: t.textSub, display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>
                LOCATION
              </label>
              <input
                type="text"
                placeholder="e.g. San Francisco, Tokyo"
                value={filters.location}
                onChange={e => setFilters({ ...filters, location: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: t.inputBg,
                  border: `1px solid ${t.border}`,
                  borderRadius: 6,
                  color: t.text,
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 12,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <div>
              <label style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, fontWeight: 700, color: t.textSub, display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>
                COUNTRY
              </label>
              <input
                type="text"
                placeholder="e.g. USA, Japan, UK"
                value={filters.country}
                onChange={e => setFilters({ ...filters, country: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: t.inputBg,
                  border: `1px solid ${t.border}`,
                  borderRadius: 6,
                  color: t.text,
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 12,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <div>
              <label style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, fontWeight: 700, color: t.textSub, display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>
                ORGANIZATION
              </label>
              <input
                type="text"
                placeholder="e.g. Google, Microsoft"
                value={filters.organization}
                onChange={e => setFilters({ ...filters, organization: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: t.inputBg,
                  border: `1px solid ${t.border}`,
                  borderRadius: 6,
                  color: t.text,
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 12,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
              <button
                onClick={() => setFilters({ location: '', country: '', organization: '' })}
                style={{
                  padding: '8px 16px',
                  background: t.surfaceAlt,
                  border: `1px solid ${t.border}`,
                  borderRadius: 6,
                  color: t.textMid,
                  cursor: 'pointer',
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}

        <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted }}>
          The system will check this username across 10 platforms: Facebook, Instagram, Twitter/X, TikTok, YouTube, GitHub, Reddit, LinkedIn, Pinterest, Telegram. Public data only.
        </p>

        {/* Loading status */}
        {loading && (
          <div className="animate-slideDown" style={{ marginTop: 16 }}>
            <Alert type="info" theme={theme}>
              <strong>Investigation in progress</strong><br />
              <span style={{ color: t.textMuted }}>{loadingStatus}</span>
            </Alert>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="animate-slideDown" style={{ marginTop: 12 }}>
            <Alert type="danger" theme={theme}>{error}</Alert>
          </div>
        )}
      </Card>

      {/* Recent Investigations */}
      <Card theme={theme}>
        <div style={{
          padding: '18px 24px', borderBottom: `1px solid ${t.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 15, color: t.text }}>
              Recent Investigations
            </span>
            {total > 0 && (
              <span style={{
                padding: '2px 10px', background: t.surfaceAlt,
                borderRadius: 20, fontFamily: "'JetBrains Mono',monospace",
                fontSize: 10, color: t.textSub,
              }}>{total}</span>
            )}
          </div>
          <button
            onClick={loadInvestigations}
            disabled={loadingInvs}
            style={{
              padding: '6px 16px', borderRadius: 8,
              border: `1px solid ${t.border}`, background: 'transparent',
              color: t.textMid, cursor: 'pointer',
              fontFamily: "'Sora',sans-serif", fontSize: 12, fontWeight: 600,
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            {loadingInvs ? <Spinner size={12} color={t.textMid} /> : '↻'} Refresh
          </button>
        </div>

        <div style={{ padding: '8px 0' }}>
          {loadingInvs ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <Spinner size={32} color={t.accent} />
            </div>
          ) : investigations.length === 0 ? (
            <EmptyState
              icon="🔍"
              message="No investigations yet. Enter a username above to begin."
              theme={theme}
            />
          ) : (
            filteredInvestigations.map((inv, i) => (
              <InvestigationRow 
                key={inv.id} 
                inv={inv} 
                theme={theme} 
                onDelete={deleteInvestigation}
                isDeleting={deleting === inv.id}
                style={{ animationDelay: `${i * 0.04}s` }} 
              />
            ))
          )}
        </div>
      </Card>
      </div>
    </>
  );
}

/* ── Investigation row ─────────────────────── */
function InvestigationRow({ inv, theme, onDelete, isDeleting, style }) {
  const t = THEMES[theme];
  const navigate = useNavigate();

  return (
    <div
      className="animate-rowIn"
      style={{
        display: 'grid',
        gridTemplateColumns: '50px 1fr auto auto auto',
        gap: 16,
        alignItems: 'center',
        padding: '14px 24px',
        borderBottom: `1px solid ${t.borderLight}`,
        transition: 'background 0.15s',
        cursor: 'default',
        ...style,
      }}
      onMouseEnter={e => e.currentTarget.style.background = t.rowHover}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {/* ID */}
      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: t.textMuted }}>
        #{inv.id}
      </span>

      {/* Username + date */}
      <div>
        <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>
          @{inv.username}
        </div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, marginTop: 2 }}>
          {new Date(inv.created_at).toLocaleString()}
        </div>
      </div>

      {/* Status */}
      <StatusBadge status={inv.status} theme={theme} />

      {/* Delete Button */}
      <button
        onClick={e => onDelete(inv.id, e)}
        disabled={isDeleting}
        style={{
          padding: '7px 14px',
          borderRadius: 8,
          background: isDeleting ? `${t.riskHigh}44` : `${t.riskHigh}22`,
          color: t.riskHigh,
          border: `1px solid ${t.riskHigh}44`,
          fontFamily: "'Sora',sans-serif",
          fontSize: 12,
          fontWeight: 700,
          cursor: isDeleting ? 'not-allowed' : 'pointer',
          whiteSpace: 'nowrap',
          transition: 'all 0.2s',
          opacity: isDeleting ? 0.6 : 1,
        }}
        onMouseEnter={e => {
          if (!isDeleting) {
            e.currentTarget.style.background = `${t.riskHigh}33`;
            e.currentTarget.style.boxShadow = `0 2px 8px ${t.riskHigh}44`;
          }
        }}
        onMouseLeave={e => {
          if (!isDeleting) {
            e.currentTarget.style.background = `${t.riskHigh}22`;
            e.currentTarget.style.boxShadow = 'none';
          }
        }}
      >
        {isDeleting ? '⊙ Deleting...' : '🗑 Delete'}
      </button>

      {/* Action */}
      {inv.status === 'completed' ? (
        <button
          onClick={() => navigate(`/case/${inv.id}`)}
          style={{
            padding: '7px 16px', borderRadius: 8,
            background: t.accentGrad, color: '#fff', border: 'none',
            fontFamily: "'Sora',sans-serif", fontSize: 12, fontWeight: 700,
            cursor: 'pointer', boxShadow: `0 2px 12px ${t.accent}44`,
            whiteSpace: 'nowrap',
          }}
        >
          View Report →
        </button>
      ) : (
        <span style={{ width: 100 }} />
      )}
    </div>
  );
}