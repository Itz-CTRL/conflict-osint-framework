// src/components/Dashboard.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { useCaseContext } from '../contexts/CaseContext';
import { StatCard, Card, SectionTitle, StatusBadge, RiskBadge, EmptyState, Alert, Spinner, TabBar, Btn } from './UI';
import Sidebar from './Sidebar';
import NewInvestigation from './NewInvestigation';
import PhoneIntel from './PhoneIntel';

const TABS = [
  { key: 'investigations', icon: '📋', label: 'Investigations' },
  { key: 'new',            icon: '🔍', label: 'New Scan'       },
  { key: 'phone',          icon: '📱', label: 'Phone Intel'    },
];

export default function Dashboard({ theme, sidebarOpen, onSidebarClose }) {
  const t = THEMES[theme];
  const navigate = useNavigate();
  const { investigations, setInvestigations, loadingList, refreshInvestigations, activeTab, setActiveTab } = useCaseContext();

  const [deleting, setDeleting] = useState(null);
  const [error,    setError]    = useState('');

  useEffect(() => { refreshInvestigations(); }, [refreshInvestigations]);

  const handleDelete = async (caseId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this investigation permanently?')) return;
    setDeleting(caseId);
    try {
      await api.deleteInvestigation(caseId);
      setInvestigations(prev => prev.filter(i => i.id !== caseId));
    } catch (err) {
      setError(`Delete failed: ${err.message}`);
    } finally {
      setDeleting(null);
    }
  };

  const completed = investigations.filter(i => i.status === 'completed').length;
  const running   = investigations.filter(i => i.status === 'running').length;
  const failed    = investigations.filter(i => i.status === 'failed').length;
  const total     = investigations.length;

  return (
    <>
      <Sidebar theme={theme} isOpen={sidebarOpen} onClose={onSidebarClose} />

      <div className="animate-fadeIn" style={{ padding: '24px 20px', maxWidth: 1400, margin: '0 auto' }}>

        {/* Stat strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 28 }}>
          <StatCard theme={theme} label="Total Investigations" value={total} />
          <StatCard theme={theme} label="Completed"  value={completed} positive />
          <StatCard theme={theme} label="Running"    value={running} />
          <StatCard theme={theme} label="Failed"     value={failed} />
        </div>

        {/* Error */}
        {error && (
          <div style={{ marginBottom: 16 }}>
            <Alert type="danger" theme={theme}>{error}</Alert>
          </div>
        )}

        {/* Tab navigation */}
        <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} theme={theme} />

        {/* ── Investigations tab ── */}
        {activeTab === 'investigations' && (
          <div className="animate-fadeIn">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <SectionTitle icon="📋" title="Investigations" theme={theme} />
              <div style={{ display: 'flex', gap: 10 }}>
                <Btn variant="secondary" size="sm" theme={theme} onClick={refreshInvestigations} disabled={loadingList}>
                  {loadingList ? <><Spinner size={13} color={t.textMuted} /> Refreshing</> : '↻ Refresh'}
                </Btn>
                <Btn variant="primary" size="sm" theme={theme} onClick={() => setActiveTab('new')}>
                  + New Scan
                </Btn>
              </div>
            </div>

            {loadingList ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
                <Spinner size={36} color={t.accent} />
              </div>
            ) : investigations.length === 0 ? (
              <EmptyState
                icon="🔍"
                message="No investigations yet. Launch your first scan."
                theme={theme}
              />
            ) : (
              <Card theme={theme} style={{ overflow: 'hidden' }}>
                {/* Table header */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto',
                  gap: 12,
                  padding: '10px 20px',
                  background: t.tableHeaderBg,
                  borderBottom: `1px solid ${t.border}`,
                }}>
                  {['USERNAME', 'STATUS', 'RISK LEVEL', 'RISK SCORE', 'CREATED', ''].map(h => (
                    <div key={h} style={{
                      fontFamily: "'JetBrains Mono',monospace",
                      fontSize: 9, fontWeight: 700,
                      color: t.textMuted, letterSpacing: 2,
                    }}>{h}</div>
                  ))}
                </div>

                {/* Rows */}
                {investigations.map((inv, idx) => (
                  <InvestigationRow
                    key={inv.id}
                    inv={inv}
                    theme={theme}
                    deleting={deleting === inv.id}
                    onOpen={() => navigate(`/case/${inv.id}`)}
                    onDelete={(e) => handleDelete(inv.id, e)}
                    idx={idx}
                  />
                ))}
              </Card>
            )}
          </div>
        )}

        {/* ── New Scan tab ── */}
        {activeTab === 'new' && (
          <div className="animate-fadeIn">
            <NewInvestigation theme={theme} />
          </div>
        )}

        {/* ── Phone Intel tab ── */}
        {activeTab === 'phone' && (
          <div className="animate-fadeIn">
            <PhoneIntel theme={theme} />
          </div>
        )}
      </div>
    </>
  );
}

/* ── Investigation Row ─────────────────────── */
function InvestigationRow({ inv, theme, deleting, onOpen, onDelete, idx }) {
  const t = THEMES[theme];
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="animate-rowIn"
      onClick={onOpen}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto',
        gap: 12,
        alignItems: 'center',
        padding: '14px 20px',
        borderBottom: `1px solid ${t.borderLight}`,
        cursor: 'pointer',
        background: hovered ? t.rowHover : 'transparent',
        transition: 'background 0.15s',
        animationDelay: `${idx * 40}ms`,
      }}
    >
      {/* Username */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: `${t.accent}22`, border: `1.5px solid ${t.accent}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: "'Sora',sans-serif", fontSize: 13, fontWeight: 700, color: t.accent,
          flexShrink: 0,
        }}>
          {(inv.username || '?')[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text }}>
            @{inv.username}
          </div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: t.textMuted, marginTop: 1 }}>
            {inv.id}
          </div>
        </div>
      </div>

      {/* Status */}
      <StatusBadge status={inv.status} theme={theme} />

      {/* Risk Level */}
      <RiskBadge level={inv.risk_level} theme={theme} />

      {/* Risk Score */}
      <div style={{
        fontFamily: "'JetBrains Mono',monospace", fontSize: 14, fontWeight: 800,
        color: inv.risk_score >= 67 ? t.riskHigh : inv.risk_score >= 34 ? t.riskMed : t.riskLow,
      }}>
        {inv.risk_score ?? '—'}
      </div>

      {/* Date */}
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted }}>
        {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : '—'}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 6 }}>
        <button
          onClick={(e) => { e.stopPropagation(); onOpen(); }}
          title="Open case"
          style={{
            padding: '5px 12px',
            background: `${t.accent}22`, border: `1px solid ${t.accent}44`,
            borderRadius: 6, color: t.accent, cursor: 'pointer',
            fontFamily: "'Sora',sans-serif", fontSize: 11, fontWeight: 700,
          }}
        >
          Open →
        </button>
        <button
          onClick={onDelete}
          disabled={deleting}
          title="Delete"
          style={{
            padding: '5px 9px',
            background: `${t.riskHigh}11`, border: `1px solid ${t.riskHigh}33`,
            borderRadius: 6, color: t.riskHigh, cursor: deleting ? 'not-allowed' : 'pointer',
            fontFamily: "'Sora',sans-serif", fontSize: 12,
          }}
        >
          {deleting ? '…' : '🗑'}
        </button>
      </div>
    </div>
  );
}
