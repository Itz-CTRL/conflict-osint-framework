// src/components/SocialProfiles.jsx
import { useState } from 'react';
import { THEMES } from '../themes';
import { Card, SectionTitle, EmptyState, Pill } from './UI';

const PLATFORM_ICONS = {
  'Twitter/X': '𝕏',
  'Twitter': '𝕏',
  'Facebook': 'f',
  'Instagram': '📷',
  'GitHub': '🐙',
  'Reddit': '🔗',
  'LinkedIn': '💼',
  'TikTok': '🎵',
  'YouTube': '▶️',
  'Telegram': '✈️',
  'Pinterest': '📌',
  'Snapchat': '👻',
  'Twitch': '🎮',
  'Medium': '📝',
};

const PLATFORM_COLORS = {
  'Twitter/X': '#000',
  'Twitter': '#1DA1F2',
  'Facebook': '#1877F2',
  'Instagram': '#E4405F',
  'GitHub': '#333',
  'Reddit': '#FF4500',
  'LinkedIn': '#0077B5',
  'TikTok': '#000',
  'YouTube': '#FF0000',
  'Telegram': '#0088cc',
  'Pinterest': '#E60023',
};

export default function SocialProfiles({ theme, socials = {}, loading = false }) {
  const t = THEMES[theme];
  const [hoveredPlatform, setHoveredPlatform] = useState(null);

  const foundProfiles = socials.found || [];
  const notFoundProfiles = socials.not_found || [];
  const errors = socials.errors || [];
  const summary = socials.summary || {};

  if (loading) {
    return (
      <Card theme={theme} style={{ padding: 24, marginBottom: 20 }}>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <div style={{ fontSize: 24, marginBottom: 10 }}>🔍</div>
          <p style={{ color: t.textMuted, margin: 0 }}>Searching for social profiles...</p>
        </div>
      </Card>
    );
  }

  if (!foundProfiles.length && !notFoundProfiles.length && !errors.length) {
    return (
      <Card theme={theme} style={{ padding: 24, marginBottom: 20 }}>
        <SectionTitle icon="🔗" title="Social Profiles" theme={theme} />
        <EmptyState message="No social profiles checked yet." />
      </Card>
    );
  }

  return (
    <>
      {/* Found Profiles */}
      {foundProfiles.length > 0 && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 20 }}>
          <SectionTitle 
            icon="✅" 
            title={`Found Profiles (${foundProfiles.length})`} 
            theme={theme} 
          />

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 16,
              marginTop: 16,
            }}
          >
            {foundProfiles.map((profile, idx) => (
              <a
                key={idx}
                href={profile.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  textDecoration: 'none',
                  cursor: 'pointer',
                }}
                onMouseEnter={() => setHoveredPlatform(idx)}
                onMouseLeave={() => setHoveredPlatform(null)}
              >
                <div
                  style={{
                    background: hoveredPlatform === idx ? `${t.accent}20` : t.cardBg,
                    border: `2px solid ${hoveredPlatform === idx ? t.accent : t.border}`,
                    borderRadius: 12,
                    padding: 16,
                    transition: 'all 0.3s ease',
                    transform: hoveredPlatform === idx ? 'translateY(-4px)' : 'none',
                    boxShadow: hoveredPlatform === idx ? `0 8px 24px ${t.accent}20` : 'none',
                  }}
                >
                  {/* Platform header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <span style={{ fontSize: 24 }}>
                      {PLATFORM_ICONS[profile.platform] || '🌐'}
                    </span>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: 0, color: t.text, fontSize: 14, fontWeight: 600 }}>
                        {profile.platform}
                      </h4>
                      {profile.verified && (
                        <Pill 
                          text="Verified" 
                          color="#10b981"
                          style={{ marginTop: 4, fontSize: 10 }}
                        />
                      )}
                    </div>
                  </div>

                  {/* Profile Picture */}
                  {profile.profile_picture && (
                    <img
                      src={profile.profile_picture}
                      alt={profile.username}
                      style={{
                        width: '100%',
                        height: 100,
                        objectFit: 'cover',
                        borderRadius: 8,
                        marginBottom: 12,
                      }}
                    />
                  )}

                  {/* Username */}
                  <p
                    style={{
                      margin: '8px 0',
                      color: t.text,
                      fontSize: 13,
                      fontWeight: 500,
                      wordBreak: 'break-all',
                    }}
                  >
                    {profile.username}
                  </p>

                  {/* Clickable URL hint */}
                  <p
                    style={{
                      margin: '8px 0 0 0',
                      color: PLATFORM_COLORS[profile.platform] || t.accent,
                      fontSize: 12,
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    Click to verify →
                  </p>

                  {/* Risk Indicators */}
                  {(profile.risk_indicators?.spam_reported || profile.risk_indicators?.dangerous) && (
                    <Pill 
                      text="⚠️ Risk Detected"
                      color="#ef4444"
                      style={{ marginTop: 8 }}
                    />
                  )}
                </div>
              </a>
            ))}
          </div>
        </Card>
      )}

      {/* Not Found Profiles */}
      {notFoundProfiles.length > 0 && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 20, opacity: 0.7 }}>
          <SectionTitle 
            icon="❌" 
            title={`Not Found (${notFoundProfiles.length})`} 
            theme={theme} 
          />

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 12 }}>
            {notFoundProfiles.map((profile, idx) => (
              <Pill
                key={idx}
                text={profile.platform}
                color={t.textMuted}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <Card theme={theme} style={{ padding: 24, marginBottom: 20, borderLeft: `4px solid #ef4444` }}>
          <SectionTitle icon="⚠️" title="Verification Errors" theme={theme} />

          <div style={{ marginTop: 12 }}>
            {errors.map((error, idx) => (
              <p
                key={idx}
                style={{
                  margin: '8px 0',
                  color: '#ef4444',
                  fontSize: 12,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                <strong>{error.platform}:</strong> {error.error}
              </p>
            ))}
          </div>
        </Card>
      )}

      {/* Summary */}
      {summary.total_checked > 0 && (
        <Card theme={theme} style={{ padding: 16, marginBottom: 20, background: `${t.accent}10` }}>
          <p style={{ margin: 0, color: t.text, fontSize: 13, fontWeight: 500 }}>
            Checked {summary.total_checked} platforms • Found {summary.found_count} •{' '}
            <span style={{ color: t.textMuted }}>
              Not found {summary.not_found_count}
            </span>
          </p>
        </Card>
      )}
    </>
  );
}
