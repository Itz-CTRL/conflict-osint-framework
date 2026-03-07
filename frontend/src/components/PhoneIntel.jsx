import React, { useState, useRef, useEffect } from 'react';
import '../styles/PhoneIntel.css';
import { COUNTRY_CODES } from './CountryCodePicker';
import { api } from '../utils/api';
import { THEMES } from '../themes';

/**
 * Phone Intelligence Component - OSINT Phone Lookup Tool
 * 
 * Features:
 * - Phone number normalization (+<countrycode><localnumber> format)
 * - Automatic country detection from phone prefix
 * - Optional country selection with searchable dropdown
 * - Scan modes: Light (fast) and Deep (comprehensive)
 * - Risk scoring and findings display
 * - Real-time progress tracking
 */
const PhoneIntel = ({ theme }) => {
  const t = THEMES[theme || 'dark'];
  
  // ============ STATE ============
  const [phoneInput, setPhoneInput] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [countrySearch, setCountrySearch] = useState('');
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [detectedCountry, setDetectedCountry] = useState(null);
  
  const [scanMode, setScanMode] = useState('light');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const [lookupResult, setLookupResult] = useState(null);
  const [error, setError] = useState(null);
  
  const countryDropdownRef = useRef(null);

  // ============ UTILITIES ============
  
  const normalizePhoneNumber = (phone, countryObj = null) => {
    if (!phone) return '';
    
    let cleaned = phone.replace(/[^\d+]/g, '');
    
    if (cleaned.startsWith('+')) {
      return cleaned;
    }
    
    if (countryObj?.dial) {
      const dialCode = countryObj.dial.replace(/\D/g, '');
      const localDigits = cleaned.replace(/^0+/, '');
      return `+${dialCode}${localDigits}`;
    }
    
    if (cleaned.length > 5) {
      return `+${cleaned}`;
    }
    
    return '';
  };

  const detectCountryFromPhone = (normalizedPhone) => {
    if (!normalizedPhone || !normalizedPhone.startsWith('+')) {
      return null;
    }
    
    const dialCodeMatch = normalizedPhone.match(/^\+(\d{1,4})/);
    if (!dialCodeMatch) return null;
    
    const dialCode = `+${dialCodeMatch[1]}`;
    const country = COUNTRY_CODES.find(c => c.dial === dialCode);
    
    return country || null;
  };

  const getRiskLevel = (score) => {
    if (score >= 0.8) return { level: 'CRITICAL', color: t.riskHigh || '#EF4444', emoji: '🔴' };
    if (score >= 0.6) return { level: 'HIGH', color: t.riskMed || '#F97316', emoji: '🟠' };
    if (score >= 0.4) return { level: 'MEDIUM', color: '#FFC107', emoji: '🟡' };
    if (score >= 0.2) return { level: 'LOW', color: t.riskLow || '#22C55E', emoji: '🟢' };
    return { level: 'SAFE', color: '#10B981', emoji: '✅' };
  };

  const filteredCountries = COUNTRY_CODES.filter(c =>
    c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
    c.dial.includes(countrySearch)
  );

  // ============ EFFECTS ============
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (countryDropdownRef.current && !countryDropdownRef.current.contains(event.target)) {
        setShowCountryDropdown(false);
      }
    };
    
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && showCountryDropdown) {
        setShowCountryDropdown(false);
      }
    };
    
    if (showCountryDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
      
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleEscapeKey);
      };
    }
  }, [showCountryDropdown]);

  // ============ HANDLERS ============

  const handlePhoneChange = (e) => {
    const value = e.target.value;
    setPhoneInput(value);
    setError(null);
    
    const normalized = normalizePhoneNumber(value);
    const detected = detectCountryFromPhone(normalized);
    setDetectedCountry(detected);
  };

  const handleCountrySelect = (countryName) => {
    setSelectedCountry(countryName);
    setCountrySearch(countryName);
    setShowCountryDropdown(false);
  };

  const handleClearCountry = (e) => {
    e.stopPropagation();
    setSelectedCountry('');
    setCountrySearch('');
    setDetectedCountry(detectCountryFromPhone(normalizePhoneNumber(phoneInput)));
  };

  const validateInputs = () => {
    if (!phoneInput.trim()) {
      setError('Please enter a phone number');
      return false;
    }
    
    const countryObj = selectedCountry 
      ? COUNTRY_CODES.find(c => c.name === selectedCountry)
      : null;
    
    const normalized = normalizePhoneNumber(phoneInput, countryObj);
    if (!normalized || normalized.replace(/\D/g, '').length < 10) {
      setError('Phone number must be at least 10 digits');
      return false;
    }
    
    return true;
  };

  const handleScan = async () => {
    if (!validateInputs()) return;

    setIsLoading(true);
    setError(null);
    setLookupResult(null);
    setProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setProgress((prev) => (prev < 90 ? prev + Math.random() * 20 : prev));
      }, 300);

      const countryToUse = selectedCountry || detectedCountry?.name;
      const countryObj = COUNTRY_CODES.find(c => c.name === countryToUse);
      
      const normalizedPhone = normalizePhoneNumber(phoneInput, countryObj);

      if (!normalizedPhone) {
        setError('Could not format phone number. Please check your input.');
        clearInterval(progressInterval);
        setIsLoading(false);
        return;
      }

      const response = await api.phoneLookup(
        normalizedPhone,
        countryObj?.code || null,
        scanMode
      );

      clearInterval(progressInterval);
      setProgress(100);

      if (response.status === 'success' && response.data) {
        setLookupResult({
          ...response.data,
          scannedAt: new Date().toLocaleString(),
          scanMode,
          country: countryToUse || response.data.country || 'Unknown',
          normalizedPhone
        });
      } else {
        setError(response.message || 'Lookup failed. Please try again.');
      }
    } catch (err) {
      setError(`Error: ${err.message || 'Failed to perform scan'}`);
    } finally {
      setIsLoading(false);
      setTimeout(() => setProgress(0), 500);
    }
  };

  const handleClear = () => {
    setPhoneInput('');
    setSelectedCountry('');
    setCountrySearch('');
    setDetectedCountry(null);
    setLookupResult(null);
    setError(null);
    setProgress(0);
  };

  const handleExport = () => {
    if (!lookupResult) return;
    
    const data = JSON.stringify(lookupResult, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `phone-intel-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // ============ RENDER ============

  return (
    <div className="phone-intel-container" style={{ color: t.text }}>
      {/* Header */}
      <div style={{
        marginBottom: 28,
        paddingBottom: 20,
        borderBottom: `1px solid ${t.border}`
      }}>
        <h2 style={{
          fontFamily: "'Sora',sans-serif",
          fontWeight: 800,
          fontSize: 24,
          color: t.text,
          margin: '0 0 8px 0'
        }}>
          📱 Phone Intelligence
        </h2>
        <p style={{
          fontFamily: "'Sora',sans-serif",
          fontSize: 13,
          color: t.textMuted,
          margin: 0
        }}>
          Advanced phone lookup with carrier detection, risk scoring, and social intelligence
        </p>
      </div>

      {/* Input Panel */}
      <div style={{
        background: t.surface,
        border: `1px solid ${t.border}`,
        borderRadius: 10,
        padding: 24,
        marginBottom: 24
      }}>
        <h3 style={{
          fontFamily: "'Sora',sans-serif",
          fontSize: 14,
          fontWeight: 700,
          color: t.textSub,
          margin: '0 0 18px 0',
          textTransform: 'uppercase',
          letterSpacing: 1
        }}>
          📡 Input Panel
        </h3>

        {/* Phone Input */}
        <div style={{ marginBottom: 18 }}>
          <label style={{
            display: 'block',
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 10,
            fontWeight: 700,
            color: t.textSub,
            marginBottom: 8,
            letterSpacing: 1.5,
            textTransform: 'uppercase'
          }}>
            Phone Number *
          </label>
          <input
            type="tel"
            value={phoneInput}
            onChange={handlePhoneChange}
            placeholder="e.g., +233201234567 or 020 123 4567"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px 14px',
              background: t.inputBg,
              border: `1px solid ${t.border}`,
              borderRadius: 8,
              color: t.text,
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: 14,
              outline: 'none',
              boxSizing: 'border-box',
              transition: 'all 0.2s',
              opacity: isLoading ? 0.6 : 1,
              cursor: isLoading ? 'not-allowed' : 'text'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = t.accent;
              e.target.style.boxShadow = `0 0 0 3px ${t.accent}22`;
            }}
            onBlur={(e) => {
              e.target.style.borderColor = t.border;
              e.target.style.boxShadow = 'none';
            }}
          />
          {detectedCountry && !selectedCountry && (
            <div style={{
              marginTop: 8,
              fontSize: 12,
              color: t.textMuted,
              fontFamily: "'Sora',sans-serif"
            }}>
              🔍 Detected: {detectedCountry.flag} {detectedCountry.name} ({detectedCountry.dial})
            </div>
          )}
        </div>

        {/* Country Selection */}
        <div style={{ marginBottom: 18, position: 'relative' }} ref={countryDropdownRef}>
          <label style={{
            display: 'block',
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 10,
            fontWeight: 700,
            color: t.textSub,
            marginBottom: 8,
            letterSpacing: 1.5,
            textTransform: 'uppercase'
          }}>
            Country Code (Optional)
          </label>

          <div style={{ position: 'relative' }}>
            <input
              type="text"
              value={selectedCountry}
              onChange={(e) => {
                const val = e.target.value;
                setCountrySearch(val);
                if (selectedCountry) {
                  setSelectedCountry('');
                }
              }}
              onFocus={() => {
                setCountrySearch('');
                setShowCountryDropdown(true);
              }}
              placeholder="Select country (optional)"
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px 14px',
                paddingRight: selectedCountry ? '38px' : '14px',
                background: t.inputBg,
                border: `1px solid ${showCountryDropdown ? t.accent : t.border}`,
                borderRadius: showCountryDropdown ? '8px 8px 0 0' : 8,
                color: t.text,
                fontFamily: "'Sora',sans-serif",
                fontSize: 13,
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'all 0.2s',
                opacity: isLoading ? 0.6 : 1,
                cursor: isLoading ? 'not-allowed' : 'text'
              }}
            />

            {selectedCountry && (
              <button
                onClick={handleClearCountry}
                disabled={isLoading}
                style={{
                  position: 'absolute',
                  right: 10,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: t.textMuted,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  fontSize: 16,
                  padding: 0,
                  lineHeight: 1,
                  opacity: 0.8,
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.opacity = '1';
                  e.target.style.color = t.accent;
                }}
                onMouseLeave={(e) => {
                  e.target.style.opacity = '0.8';
                  e.target.style.color = t.textMuted;
                }}
                title="Clear country"
              >
                ✕
              </button>
            )}

            {showCountryDropdown && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                maxHeight: 240,
                overflowY: 'auto',
                background: t.surface,
                border: `1px solid ${t.accent}66`,
                borderTop: 'none',
                borderRadius: '0 0 8px 8px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
                zIndex: 1000
              }}>
                {filteredCountries.length > 0 ? (
                  filteredCountries.map((country) => (
                    <div
                      key={country.code}
                      onClick={() => handleCountrySelect(country.name)}
                      style={{
                        padding: '10px 14px',
                        cursor: 'pointer',
                        borderBottom: `1px solid ${t.borderLight || `${t.border}44`}`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        transition: 'background 0.15s',
                        background: selectedCountry === country.name ? `${t.accent}22` : 'transparent'
                      }}
                      onMouseEnter={(e) => {
                        if (selectedCountry !== country.name) {
                          e.currentTarget.style.background = `${t.accent}0a`;
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = selectedCountry === country.name ? `${t.accent}22` : 'transparent';
                      }}
                    >
                      <span style={{ fontSize: 18 }}>{country.flag}</span>
                      <span style={{
                        fontFamily: "'Sora',sans-serif",
                        fontSize: 12,
                        color: selectedCountry === country.name ? t.accent : t.text,
                        flex: 1
                      }}>
                        {country.name}
                      </span>
                      <span style={{
                        fontFamily: "'JetBrains Mono',monospace",
                        fontSize: 11,
                        color: t.textMuted,
                        fontWeight: 700
                      }}>
                        {country.dial}
                      </span>
                    </div>
                  ))
                ) : (
                  <div style={{
                    padding: '12px 14px',
                    textAlign: 'center',
                    fontFamily: "'Sora',sans-serif",
                    fontSize: 12,
                    color: t.textMuted
                  }}>
                    No countries found
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Scan Mode */}
        <div style={{ marginBottom: 20 }}>
          <label style={{
            display: 'block',
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 10,
            fontWeight: 700,
            color: t.textSub,
            marginBottom: 10,
            letterSpacing: 1.5,
            textTransform: 'uppercase'
          }}>
            Scan Mode
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { mode: 'light', label: '⚡ Light Scan', desc: 'Fast lookup' },
              { mode: 'deep', label: '🔍 Deep Scan', desc: 'Full OSINT' }
            ].map(({ mode, label, desc }) => (
              <button
                key={mode}
                onClick={() => setScanMode(mode)}
                disabled={isLoading}
                style={{
                  padding: '12px 14px',
                  background: scanMode === mode ? `${t.accent}18` : t.inputBg,
                  border: `2px solid ${scanMode === mode ? t.accent : t.border}`,
                  borderRadius: 8,
                  color: scanMode === mode ? t.accent : t.text,
                  fontFamily: "'Sora',sans-serif",
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                  opacity: isLoading ? 0.6 : 1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4
                }}
              >
                <span>{label}</span>
                <span style={{ fontSize: 10, color: t.textMuted, fontWeight: 500 }}>
                  {desc}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
          <button
            onClick={handleScan}
            disabled={isLoading || !phoneInput.trim()}
            style={{
              padding: '12px 16px',
              background: isLoading ? t.border : (t.accentGrad || t.accent),
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontFamily: "'Sora',sans-serif",
              fontSize: 13,
              fontWeight: 700,
              cursor: isLoading || !phoneInput.trim() ? 'not-allowed' : 'pointer',
              opacity: isLoading || !phoneInput.trim() ? 0.6 : 1,
              transition: 'all 0.2s',
              boxShadow: isLoading ? 'none' : `0 4px 12px ${t.accent}33`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8
            }}
          >
            {isLoading ? (
              <>
                <span style={{ animation: 'spin 1s linear infinite' }}>⟳</span>
                Scanning...
              </>
            ) : (
              <>🔍 Start Scan</>
            )}
          </button>

          <button
            onClick={handleClear}
            disabled={isLoading}
            style={{
              padding: '12px 16px',
              background: t.surfaceAlt || t.inputBg,
              color: t.text,
              border: `1px solid ${t.border}`,
              borderRadius: 8,
              fontFamily: "'Sora',sans-serif",
              fontSize: 13,
              fontWeight: 700,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.6 : 1,
              transition: 'all 0.2s'
            }}
          >
            🗑️ Clear
          </button>

          <button
            onClick={handleExport}
            disabled={!lookupResult || isLoading}
            style={{
              padding: '12px 16px',
              background: lookupResult ? (t.surfaceAlt || t.inputBg) : t.inputBg,
              color: lookupResult ? t.text : t.textMuted,
              border: `1px solid ${lookupResult ? t.border : t.borderLight || `${t.border}44`}`,
              borderRadius: 8,
              fontFamily: "'Sora',sans-serif",
              fontSize: 13,
              fontWeight: 700,
              cursor: lookupResult && !isLoading ? 'pointer' : 'not-allowed',
              opacity: lookupResult ? 1 : 0.5,
              transition: 'all 0.2s'
            }}
          >
            📥 Export
          </button>
        </div>

        {/* Progress */}
        {isLoading && progress > 0 && (
          <div style={{
            marginTop: 16,
            height: 4,
            background: t.inputBg,
            borderRadius: 2,
            overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              background: t.accentGrad || t.accent,
              width: `${progress}%`,
              transition: 'width 0.3s'
            }} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            marginTop: 12,
            padding: 12,
            background: `${t.riskHigh || '#EF4444'}15`,
            border: `1px solid ${t.riskHigh || '#EF4444'}`,
            borderRadius: 6,
            color: t.riskHigh || '#EF4444',
            fontFamily: "'Sora',sans-serif",
            fontSize: 12
          }}>
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Results */}
      {lookupResult && (
        <div style={{
          background: t.surface,
          border: `1px solid ${t.border}`,
          borderRadius: 10,
          padding: 24
        }}>
          <h3 style={{
            fontFamily: "'Sora',sans-serif",
            fontSize: 14,
            fontWeight: 700,
            color: t.textSub,
            margin: '0 0 18px 0',
            textTransform: 'uppercase',
            letterSpacing: 1
          }}>
            📊 Results
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 16,
            marginBottom: 20
          }}>
            <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Phone</div>
              <div style={{ fontSize: 13, color: t.text, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, wordBreak: 'break-all' }}>
                {lookupResult.normalizedPhone || 'N/A'}
              </div>
            </div>

            <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Country</div>
              <div style={{ fontSize: 13, color: t.text, fontFamily: "'Sora',sans-serif", fontWeight: 700 }}>
                {lookupResult.country || 'Unknown'}
              </div>
            </div>

            <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Carrier</div>
              <div style={{ fontSize: 13, color: t.text, fontFamily: "'Sora',sans-serif", fontWeight: 700 }}>
                {lookupResult.carrier || 'N/A'}
              </div>
            </div>

            <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Mode</div>
              <div style={{ fontSize: 13, color: t.text, fontFamily: "'Sora',sans-serif", fontWeight: 700 }}>
                {lookupResult.scanMode === 'deep' ? '🔍 Deep' : '⚡ Light'}
              </div>
            </div>

            {lookupResult.risk_score !== undefined && (
              <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
                <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Risk</div>
                <div style={{ fontSize: 13, color: t.text, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700 }}>
                  {Math.round(lookupResult.risk_score * 100)}%
                </div>
              </div>
            )}

            <div style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}` }}>
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>Time</div>
              <div style={{ fontSize: 11, color: t.text, fontFamily: "'Sora',sans-serif", fontWeight: 500 }}>
                {lookupResult.scannedAt}
              </div>
            </div>
          </div>

          {lookupResult.valid && (
            <details style={{ background: t.inputBg, padding: 12, borderRadius: 6, border: `1px solid ${t.border}`, cursor: 'pointer' }}>
              <summary style={{ fontSize: 11, color: t.textMuted, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, textTransform: 'uppercase', userSelect: 'none' }}>
                📄 Raw Data
              </summary>
              <pre style={{
                margin: '10px 0 0 0',
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: 10,
                color: t.text,
                overflow: 'auto',
                maxHeight: 300,
                background: t.surface,
                padding: 10,
                borderRadius: 4,
                border: `1px solid ${t.border}`
              }}>
                {JSON.stringify(lookupResult, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      {!lookupResult && !isLoading && (
        <div style={{
          textAlign: 'center',
          padding: '60px 40px',
          background: t.surface,
          border: `1px dashed ${t.border}`,
          borderRadius: 10,
          color: t.textMuted
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📱</div>
          <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 15, margin: '0 0 8px 0', color: t.text, fontWeight: 600 }}>
            Enter a phone number to begin
          </p>
          <p style={{ fontFamily: "'Sora',sans-serif", fontSize: 12, margin: 0, color: t.textMuted }}>
            Supports international format with or without country codes
          </p>
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default PhoneIntel;
