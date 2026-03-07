// src/components/ReportViewer.jsx
import { useState } from 'react';
import { THEMES } from '../themes';
import { api } from '../utils/api';
import { Card, SectionTitle, Alert, Spinner, EmptyState, Btn } from './UI';

export default function ReportViewer({ caseId, theme, caseData }) {
  const t = THEMES[theme];

  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(null); // { report_id, title, created_at }
  const [textReport, setTextReport] = useState(null);
  const [jsonReport, setJsonReport] = useState(null);
  const [loadingText, setLoadingText] = useState(false);
  const [loadingJson, setLoadingJson] = useState(false);
  const [error, setError] = useState('');
  const [activeView, setActiveView] = useState('summary'); // 'summary' | 'text' | 'json'

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const res = await api.generateReport(caseId, {
        include_graph: true,
        include_evidence: true,
        include_timeline: true,
      });
      setGenerated(res);
    } catch (e) {
      setError(`Failed to generate report: ${e.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleLoadText = async () => {
    setLoadingText(true);
    setError('');
    try {
      const res = await api.getTextReport(caseId);
      setTextReport(res.report || '');
      setActiveView('text');
    } catch (e) {
      setError(`Failed to load text report: ${e.message}`);
    } finally {
      setLoadingText(false);
    }
  };

  const handleLoadJson = async () => {
    setLoadingJson(true);
    setError('');
    try {
      const res = await api.getJsonReport(caseId);
      setJsonReport(res.report || {});
      setActiveView('json');
    } catch (e) {
      setError(`Failed to load JSON report: ${e.message}`);
    } finally {
      setLoadingJson(false);
    }
  };

  const handleDownloadJson = () => {
    if (!jsonReport) return;
    const blob = new Blob([JSON.stringify(jsonReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `osint-report-${caseId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadText = () => {
    if (!textReport) return;
    const blob = new Blob([textReport], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `osint-report-${caseId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Report Actions */}
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="📄" title="Report Generation" theme={theme} />

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 12,
          marginBottom: 20,
        }}>
          {/* Generate PDF */}
          <ReportActionCard
            icon="📋"
            title="Generate PDF"
            description="Full investigation report with chain of custody"
            buttonLabel={generating ? 'Generating...' : generated ? '✓ Generated' : 'Generate Report'}
            onClick={handleGenerate}
            loading={generating}
            done={!!generated}
            theme={theme}
          />

          {/* Text Report */}
          <ReportActionCard
            icon="📝"
            title="Text Report"
            description="Formatted text summary of all findings"
            buttonLabel={loadingText ? 'Loading...' : 'View Text Report'}
            onClick={handleLoadText}
            loading={loadingText}
            theme={theme}
          />

          {/* JSON Report */}
          <ReportActionCard
            icon="{ }"
            title="JSON Export"
            description="Complete structured JSON with all entities and edges"
            buttonLabel={loadingJson ? 'Loading...' : 'Load JSON'}
            onClick={handleLoadJson}
            loading={loadingJson}
            theme={theme}
          />
        </div>

        {error && <Alert type="danger" theme={theme}>{error}</Alert>}

        {generated && (
          <Alert type="success" theme={theme}>
            <strong>Report generated:</strong> {generated.title || 'OSINT Report'} · ID: {generated.report_id}
          </Alert>
        )}
      </Card>

      {/* Report Content View */}
      {(textReport || jsonReport) && (
        <Card theme={theme} style={{ padding: 24 }}>
          {/* View Switcher */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
            {textReport && (
              <button
                onClick={() => setActiveView('text')}
                style={viewBtnStyle(activeView === 'text', t)}
              >
                📝 Text Report
              </button>
            )}
            {jsonReport && (
              <button
                onClick={() => setActiveView('json')}
                style={viewBtnStyle(activeView === 'json', t)}
              >
                &#123;&#125; JSON Report
              </button>
            )}

            {/* Download buttons */}
            {activeView === 'text' && textReport && (
              <button onClick={handleDownloadText} style={downloadBtnStyle(t)}>
                ⬇ Download .txt
              </button>
            )}
            {activeView === 'json' && jsonReport && (
              <button onClick={handleDownloadJson} style={downloadBtnStyle(t)}>
                ⬇ Download .json
              </button>
            )}
          </div>

          {/* Text Report View */}
          {activeView === 'text' && textReport && (
            <div style={{
              background: t.surfaceAlt,
              border: `1px solid ${t.border}`,
              borderRadius: 10,
              padding: 20,
              maxHeight: 500,
              overflowY: 'auto',
            }}>
              <pre style={{
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: 11,
                color: t.text,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                margin: 0,
                lineHeight: 1.7,
              }}>
                {textReport}
              </pre>
            </div>
          )}

          {/* JSON Report View */}
          {activeView === 'json' && jsonReport && (
            <div style={{
              background: t.surfaceAlt,
              border: `1px solid ${t.border}`,
              borderRadius: 10,
              padding: 20,
              maxHeight: 500,
              overflowY: 'auto',
            }}>
              <JsonTree data={jsonReport} theme={theme} />
            </div>
          )}
        </Card>
      )}

      {/* Chain of Custody */}
      <Card theme={theme} style={{ padding: 24 }}>
        <SectionTitle icon="🔗" title="Chain of Custody" theme={theme} />
        {caseData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            <CustodyEntry
              time={caseData.created_at}
              action="Case Created"
              detail={`Investigation for @${caseData.username || caseId} initiated`}
              icon="🔍"
              theme={theme}
            />
            {caseData.started_at && (
              <CustodyEntry
                time={caseData.started_at}
                action="Scan Started"
                detail={`${(caseData.scan_depth || 'Light')} scan initiated`}
                icon="▶"
                theme={theme}
              />
            )}
            {caseData.completed_at && (
              <CustodyEntry
                time={caseData.completed_at}
                action="Scan Completed"
                detail={`Risk score: ${caseData.risk_score ?? '—'} · Level: ${caseData.risk_level || '—'}`}
                icon="✓"
                theme={theme}
                last
              />
            )}
          </div>
        ) : (
          <EmptyState icon="🔗" message="No chain of custody data available." theme={theme} />
        )}
      </Card>
    </div>
  );
}

/* ── Sub-components ───────────────────────── */

function ReportActionCard({ icon, title, description, buttonLabel, onClick, loading, done, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{
      background: t.surfaceAlt,
      border: `1px solid ${t.border}`,
      borderRadius: 12,
      padding: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      <div style={{ fontSize: 28 }}>{icon}</div>
      <div>
        <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 14, color: t.text }}>{title}</div>
        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginTop: 4 }}>{description}</div>
      </div>
      <button
        onClick={onClick}
        disabled={loading || done}
        style={{
          padding: '9px 0',
          background: done ? `${t.riskLow}22` : loading ? t.border : t.accentGrad,
          color: done ? t.riskLow : '#fff',
          border: done ? `1px solid ${t.riskLow}44` : 'none',
          borderRadius: 8,
          cursor: loading || done ? 'default' : 'pointer',
          fontFamily: "'Sora',sans-serif",
          fontWeight: 700,
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          transition: 'all 0.2s',
        }}
      >
        {loading && <Spinner size={14} />}
        {buttonLabel}
      </button>
    </div>
  );
}

function CustodyEntry({ time, action, detail, icon, theme, last }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: 'flex', gap: 14, paddingBottom: last ? 0 : 20 }}>
      {/* Timeline indicator */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 28, flexShrink: 0 }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: `${t.accent}22`, border: `2px solid ${t.accent}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, color: t.accent, flexShrink: 0,
        }}>
          {icon}
        </div>
        {!last && (
          <div style={{ flex: 1, width: 2, background: t.borderLight, marginTop: 4 }} />
        )}
      </div>
      {/* Content */}
      <div style={{ paddingTop: 2, paddingBottom: last ? 0 : 4 }}>
        <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text }}>{action}</div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, marginTop: 2 }}>
          {time ? new Date(time).toLocaleString() : '—'}
        </div>
        <div style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, color: t.textMuted, marginTop: 4 }}>{detail}</div>
      </div>
    </div>
  );
}

function viewBtnStyle(active, t) {
  return {
    padding: '8px 16px',
    background: active ? `${t.accent}22` : t.surfaceAlt,
    border: `1px solid ${active ? t.accent : t.border}`,
    borderRadius: 8,
    color: active ? t.accent : t.textMid,
    cursor: 'pointer',
    fontFamily: "'Sora',sans-serif",
    fontWeight: 700,
    fontSize: 12,
    transition: 'all 0.15s',
  };
}

function downloadBtnStyle(t) {
  return {
    padding: '8px 16px',
    background: `${t.riskLow}22`,
    border: `1px solid ${t.riskLow}44`,
    borderRadius: 8,
    color: t.riskLow,
    cursor: 'pointer',
    fontFamily: "'Sora',sans-serif",
    fontWeight: 700,
    fontSize: 12,
    marginLeft: 'auto',
  };
}

function JsonTree({ data, theme, depth = 0 }) {
  const t = THEMES[theme];
  if (data === null) return <span style={{ color: t.riskHigh, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>null</span>;
  if (typeof data === 'boolean') return <span style={{ color: t.riskMed, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>{String(data)}</span>;
  if (typeof data === 'number') return <span style={{ color: t.accentAlt, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>{data}</span>;
  if (typeof data === 'string') return <span style={{ color: t.riskLow, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>"{data}"</span>;
  if (Array.isArray(data)) {
    if (data.length === 0) return <span style={{ color: t.textMuted, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>[]</span>;
    return (
      <div style={{ paddingLeft: depth === 0 ? 0 : 16 }}>
        {data.slice(0, 50).map((item, i) => (
          <div key={i} style={{ marginBottom: 2 }}>
            <span style={{ color: t.textMuted, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>{i}: </span>
            <JsonTree data={item} theme={theme} depth={depth + 1} />
          </div>
        ))}
        {data.length > 50 && <div style={{ color: t.textMuted, fontSize: 10, fontFamily: "'JetBrains Mono',monospace" }}>... +{data.length - 50} more</div>}
      </div>
    );
  }
  if (typeof data === 'object') {
    const keys = Object.keys(data);
    if (keys.length === 0) return <span style={{ color: t.textMuted, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>{'{}'}</span>;
    return (
      <div style={{ paddingLeft: depth === 0 ? 0 : 16 }}>
        {keys.map(key => (
          <div key={key} style={{ marginBottom: 3, display: 'flex', alignItems: 'flex-start', gap: 4, flexWrap: 'wrap' }}>
            <span style={{ color: t.textSub, fontSize: 11, fontFamily: "'JetBrains Mono',monospace", flexShrink: 0 }}>{key}:</span>
            <JsonTree data={data[key]} theme={theme} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }
  return <span style={{ color: t.text, fontSize: 11, fontFamily: "'JetBrains Mono',monospace" }}>{String(data)}</span>;
}
