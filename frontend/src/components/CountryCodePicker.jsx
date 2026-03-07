// src/components/CountryCodePicker.jsx
/**
 * Searchable country code (dial code) picker with Ghana (+233) as default.
 * Renders as a compact button that opens a floating searchable dropdown.
 */
import { useState, useRef, useEffect } from 'react';
import { THEMES } from '../themes';

export const COUNTRY_CODES = [
  { name: 'Ghana',              code: 'GH', dial: '+233', flag: '🇬🇭' }, // DEFAULT
  { name: 'Afghanistan',        code: 'AF', dial: '+93',  flag: '🇦🇫' },
  { name: 'Albania',            code: 'AL', dial: '+355', flag: '🇦🇱' },
  { name: 'Algeria',            code: 'DZ', dial: '+213', flag: '🇩🇿' },
  { name: 'Argentina',          code: 'AR', dial: '+54',  flag: '🇦🇷' },
  { name: 'Australia',          code: 'AU', dial: '+61',  flag: '🇦🇺' },
  { name: 'Austria',            code: 'AT', dial: '+43',  flag: '🇦🇹' },
  { name: 'Bangladesh',         code: 'BD', dial: '+880', flag: '🇧🇩' },
  { name: 'Belgium',            code: 'BE', dial: '+32',  flag: '🇧🇪' },
  { name: 'Brazil',             code: 'BR', dial: '+55',  flag: '🇧🇷' },
  { name: 'Burkina Faso',       code: 'BF', dial: '+226', flag: '🇧🇫' },
  { name: 'Cameroon',           code: 'CM', dial: '+237', flag: '🇨🇲' },
  { name: 'Canada',             code: 'CA', dial: '+1',   flag: '🇨🇦' },
  { name: 'China',              code: 'CN', dial: '+86',  flag: '🇨🇳' },
  { name: 'Colombia',           code: 'CO', dial: '+57',  flag: '🇨🇴' },
  { name: "Côte d'Ivoire",      code: 'CI', dial: '+225', flag: '🇨🇮' },
  { name: 'DR Congo',           code: 'CD', dial: '+243', flag: '🇨🇩' },
  { name: 'Denmark',            code: 'DK', dial: '+45',  flag: '🇩🇰' },
  { name: 'Egypt',              code: 'EG', dial: '+20',  flag: '🇪🇬' },
  { name: 'Ethiopia',           code: 'ET', dial: '+251', flag: '🇪🇹' },
  { name: 'France',             code: 'FR', dial: '+33',  flag: '🇫🇷' },
  { name: 'Germany',            code: 'DE', dial: '+49',  flag: '🇩🇪' },
  { name: 'Greece',             code: 'GR', dial: '+30',  flag: '🇬🇷' },
  { name: 'Guinea',             code: 'GN', dial: '+224', flag: '🇬🇳' },
  { name: 'India',              code: 'IN', dial: '+91',  flag: '🇮🇳' },
  { name: 'Indonesia',          code: 'ID', dial: '+62',  flag: '🇮🇩' },
  { name: 'Iran',               code: 'IR', dial: '+98',  flag: '🇮🇷' },
  { name: 'Iraq',               code: 'IQ', dial: '+964', flag: '🇮🇶' },
  { name: 'Ireland',            code: 'IE', dial: '+353', flag: '🇮🇪' },
  { name: 'Israel',             code: 'IL', dial: '+972', flag: '🇮🇱' },
  { name: 'Italy',              code: 'IT', dial: '+39',  flag: '🇮🇹' },
  { name: 'Japan',              code: 'JP', dial: '+81',  flag: '🇯🇵' },
  { name: 'Jordan',             code: 'JO', dial: '+962', flag: '🇯🇴' },
  { name: 'Kenya',              code: 'KE', dial: '+254', flag: '🇰🇪' },
  { name: 'Lebanon',            code: 'LB', dial: '+961', flag: '🇱🇧' },
  { name: 'Libya',              code: 'LY', dial: '+218', flag: '🇱🇾' },
  { name: 'Malaysia',           code: 'MY', dial: '+60',  flag: '🇲🇾' },
  { name: 'Mali',               code: 'ML', dial: '+223', flag: '🇲🇱' },
  { name: 'Mexico',             code: 'MX', dial: '+52',  flag: '🇲🇽' },
  { name: 'Morocco',            code: 'MA', dial: '+212', flag: '🇲🇦' },
  { name: 'Mozambique',         code: 'MZ', dial: '+258', flag: '🇲🇿' },
  { name: 'Netherlands',        code: 'NL', dial: '+31',  flag: '🇳🇱' },
  { name: 'New Zealand',        code: 'NZ', dial: '+64',  flag: '🇳🇿' },
  { name: 'Niger',              code: 'NE', dial: '+227', flag: '🇳🇪' },
  { name: 'Nigeria',            code: 'NG', dial: '+234', flag: '🇳🇬' },
  { name: 'North Korea',        code: 'KP', dial: '+850', flag: '🇰🇵' },
  { name: 'Norway',             code: 'NO', dial: '+47',  flag: '🇳🇴' },
  { name: 'Pakistan',           code: 'PK', dial: '+92',  flag: '🇵🇰' },
  { name: 'Palestine',          code: 'PS', dial: '+970', flag: '🇵🇸' },
  { name: 'Peru',               code: 'PE', dial: '+51',  flag: '🇵🇪' },
  { name: 'Philippines',        code: 'PH', dial: '+63',  flag: '🇵🇭' },
  { name: 'Poland',             code: 'PL', dial: '+48',  flag: '🇵🇱' },
  { name: 'Portugal',           code: 'PT', dial: '+351', flag: '🇵🇹' },
  { name: 'Romania',            code: 'RO', dial: '+40',  flag: '🇷🇴' },
  { name: 'Russia',             code: 'RU', dial: '+7',   flag: '🇷🇺' },
  { name: 'Rwanda',             code: 'RW', dial: '+250', flag: '🇷🇼' },
  { name: 'Saudi Arabia',       code: 'SA', dial: '+966', flag: '🇸🇦' },
  { name: 'Senegal',            code: 'SN', dial: '+221', flag: '🇸🇳' },
  { name: 'Sierra Leone',       code: 'SL', dial: '+232', flag: '🇸🇱' },
  { name: 'Somalia',            code: 'SO', dial: '+252', flag: '🇸🇴' },
  { name: 'South Africa',       code: 'ZA', dial: '+27',  flag: '🇿🇦' },
  { name: 'South Korea',        code: 'KR', dial: '+82',  flag: '🇰🇷' },
  { name: 'South Sudan',        code: 'SS', dial: '+211', flag: '🇸🇸' },
  { name: 'Spain',              code: 'ES', dial: '+34',  flag: '🇪🇸' },
  { name: 'Sudan',              code: 'SD', dial: '+249', flag: '🇸🇩' },
  { name: 'Sweden',             code: 'SE', dial: '+46',  flag: '🇸🇪' },
  { name: 'Switzerland',        code: 'CH', dial: '+41',  flag: '🇨🇭' },
  { name: 'Syria',              code: 'SY', dial: '+963', flag: '🇸🇾' },
  { name: 'Tanzania',           code: 'TZ', dial: '+255', flag: '🇹🇿' },
  { name: 'Thailand',           code: 'TH', dial: '+66',  flag: '🇹🇭' },
  { name: 'Togo',               code: 'TG', dial: '+228', flag: '🇹🇬' },
  { name: 'Tunisia',            code: 'TN', dial: '+216', flag: '🇹🇳' },
  { name: 'Turkey',             code: 'TR', dial: '+90',  flag: '🇹🇷' },
  { name: 'Uganda',             code: 'UG', dial: '+256', flag: '🇺🇬' },
  { name: 'Ukraine',            code: 'UA', dial: '+380', flag: '🇺🇦' },
  { name: 'United Arab Emirates', code: 'AE', dial: '+971', flag: '🇦🇪' },
  { name: 'United Kingdom',     code: 'GB', dial: '+44',  flag: '🇬🇧' },
  { name: 'United States',      code: 'US', dial: '+1',   flag: '🇺🇸' },
  { name: 'Venezuela',          code: 'VE', dial: '+58',  flag: '🇻🇪' },
  { name: 'Vietnam',            code: 'VN', dial: '+84',  flag: '🇻🇳' },
  { name: 'Yemen',              code: 'YE', dial: '+967', flag: '🇾🇪' },
  { name: 'Zambia',             code: 'ZM', dial: '+260', flag: '🇿🇲' },
  { name: 'Zimbabwe',           code: 'ZW', dial: '+263', flag: '🇿🇼' },
];

const DEFAULT = COUNTRY_CODES[0]; // Ghana

export default function CountryCodePicker({ value, onChange, disabled, theme }) {
  const t = THEMES[theme];
  const [open,   setOpen]   = useState(false);
  const [search, setSearch] = useState('');
  const wrapRef  = useRef(null);
  const searchRef = useRef(null);

  const selected = COUNTRY_CODES.find(c => c.dial === value) || DEFAULT;

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Focus search when opened
  useEffect(() => {
    if (open) setTimeout(() => searchRef.current?.focus(), 60);
  }, [open]);

  const filtered = COUNTRY_CODES.filter(c => {
    const q = search.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      c.dial.includes(q) ||
      c.code.toLowerCase().includes(q)
    );
  });

  const select = (country) => {
    onChange(country.dial);
    setOpen(false);
    setSearch('');
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative', flexShrink: 0 }}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        style={{
          height: '100%',
          minHeight: 44,
          padding: '0 12px',
          background: open ? `${t.accent}18` : t.inputBg,
          border: `1px solid ${open ? t.accent : t.border}`,
          borderRadius: 8,
          color: t.text,
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', gap: 6,
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 13, fontWeight: 700,
          whiteSpace: 'nowrap',
          transition: 'all 0.15s',
          boxShadow: open ? `0 0 0 3px ${t.accent}22` : 'none',
          opacity: disabled ? 0.6 : 1,
        }}
      >
        <span style={{ fontSize: 18, lineHeight: 1 }}>{selected.flag}</span>
        <span style={{ color: t.accent }}>{selected.dial}</span>
        <span style={{ fontSize: 9, color: t.textMuted, marginLeft: 2 }}>{open ? '▲' : '▼'}</span>
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 4px)',
          left: 0,
          width: 280,
          background: t.surface,
          border: `1px solid ${t.accent}66`,
          borderRadius: 10,
          boxShadow: `0 8px 32px rgba(0,0,0,0.3)`,
          zIndex: 2000,
          overflow: 'hidden',
        }}>
          {/* Search */}
          <div style={{ padding: '10px 10px 6px' }}>
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search country or +code..."
              style={{
                width: '100%',
                padding: '8px 10px',
                background: t.inputBg,
                border: `1px solid ${t.border}`,
                borderRadius: 6,
                color: t.text,
                fontFamily: "'Sora',sans-serif",
                fontSize: 12,
                outline: 'none',
                boxSizing: 'border-box',
              }}
              onFocus={e => { e.target.style.borderColor = t.accent; }}
              onBlur={e => { e.target.style.borderColor = t.border; }}
            />
          </div>

          {/* List */}
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {filtered.length === 0 ? (
              <div style={{
                padding: '14px 14px',
                fontFamily: "'Sora',sans-serif",
                fontSize: 12, color: t.textMuted,
                textAlign: 'center',
              }}>
                No results
              </div>
            ) : filtered.map((c, i) => {
              const isSelected = c.dial === selected.dial;
              return (
                <div
                  key={`${c.code}-${i}`}
                  onClick={() => select(c)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px',
                    background: isSelected ? `${t.accent}18` : 'transparent',
                    cursor: 'pointer',
                    transition: 'background 0.1s',
                    borderLeft: `3px solid ${isSelected ? t.accent : 'transparent'}`,
                  }}
                  onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = `${t.accent}0a`; }}
                  onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                >
                  <span style={{ fontSize: 18, lineHeight: 1, flexShrink: 0 }}>{c.flag}</span>
                  <span style={{
                    fontFamily: "'Sora',sans-serif", fontSize: 12,
                    color: isSelected ? t.accent : t.text,
                    flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {c.name}
                  </span>
                  <span style={{
                    fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
                    color: isSelected ? t.accent : t.textMuted,
                    fontWeight: 700, flexShrink: 0,
                  }}>
                    {c.dial}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
