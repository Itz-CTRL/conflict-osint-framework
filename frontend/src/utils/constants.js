/**
 * Frontend constants and configuration for OSINT Investigation Platform
 */

// Platform definitions for filter selection
export const PLATFORMS = {
  TWITTER: { id: 'twitter', label: 'Twitter/X', icon: '𝕏', color: '#000000' },
  FACEBOOK: { id: 'facebook', label: 'Facebook', icon: 'f', color: '#1877f2' },
  INSTAGRAM: { id: 'instagram', label: 'Instagram', icon: '📷', color: '#e4405f' },
  TIKTOK: { id: 'tiktok', label: 'TikTok', icon: '♪', color: '#000000' },
  LINKEDIN: { id: 'linkedin', label: 'LinkedIn', icon: 'in', color: '#0a66c2' },
  GITHUB: { id: 'github', label: 'GitHub', icon: '⚫', color: '#333333' },
  YOUTUBE: { id: 'youtube', label: 'YouTube', icon: '▶', color: '#ff0000' },
  REDDIT: { id: 'reddit', label: 'Reddit', icon: '🔴', color: '#ff4500' },
  TELEGRAM: { id: 'telegram', label: 'Telegram', icon: '📱', color: '#0088cc' },
  PINTEREST: { id: 'pinterest', label: 'Pinterest', icon: 'P', color: '#e60023' },
  SNAPCHAT: { id: 'snapchat', label: 'Snapchat', icon: '👻', color: '#fffc00' },
  WHATSAPP: { id: 'whatsapp', label: 'WhatsApp', icon: '💬', color: '#25d366' },
  DISCORD: { id: 'discord', label: 'Discord', icon: '🎮', color: '#5865f2' },
  TWITCH: { id: 'twitch', label: 'Twitch', icon: '▶', color: '#9146ff' },
  MEDIUM: { id: 'medium', label: 'Medium', icon: '◆', color: '#000000' },
};

export const PLATFORM_LIST = Object.values(PLATFORMS);

// Country/Location definitions
export const COUNTRIES = {
  US: { code: 'US', name: 'United States', flag: '🇺🇸', dialCode: '+1' },
  UK: { code: 'UK', name: 'United Kingdom', flag: '🇬🇧', dialCode: '+44' },
  CA: { code: 'CA', name: 'Canada', flag: '🇨🇦', dialCode: '+1' },
  AU: { code: 'AU', name: 'Australia', flag: '🇦🇺', dialCode: '+61' },
  DE: { code: 'DE', name: 'Germany', flag: '🇩🇪', dialCode: '+49' },
  FR: { code: 'FR', name: 'France', flag: '🇫🇷', dialCode: '+33' },
  IN: { code: 'IN', name: 'India', flag: '🇮🇳', dialCode: '+91' },
  CN: { code: 'CN', name: 'China', flag: '🇨🇳', dialCode: '+86' },
  BR: { code: 'BR', name: 'Brazil', flag: '🇧🇷', dialCode: '+55' },
  RU: { code: 'RU', name: 'Russia', flag: '🇷🇺', dialCode: '+7' },
  JP: { code: 'JP', name: 'Japan', flag: '🇯🇵', dialCode: '+81' },
  KR: { code: 'KR', name: 'South Korea', flag: '🇰🇷', dialCode: '+82' },
  GH: { code: 'GH', name: 'Ghana', flag: '🇬🇭', dialCode: '+233' },
  NG: { code: 'NG', name: 'Nigeria', flag: '🇳🇬', dialCode: '+234' },
  MX: { code: 'MX', name: 'Mexico', flag: '🇲🇽', dialCode: '+52' },
};

export const COUNTRY_LIST = Object.values(COUNTRIES);

// Account types
export const ACCOUNT_TYPES = {
  PERSONAL: { id: 'personal', label: 'Personal Account', icon: '👤' },
  BUSINESS: { id: 'business', label: 'Business Account', icon: '🏢' },
  BOT: { id: 'bot', label: 'Bot/Service Account', icon: '🤖' },
};

export const ACCOUNT_TYPE_LIST = Object.values(ACCOUNT_TYPES);

// Verification status options
export const VERIFICATION_STATUS = {
  ALL: { id: 'all', label: 'All Accounts', icon: '⚪' },
  VERIFIED: { id: 'verified', label: 'Verified Only', icon: '✅' },
  NOT_VERIFIED: { id: 'not-verified', label: 'Not Verified', icon: '❌' },
};

// Scan types and phases
export const SCAN_TYPES = {
  LIGHT: {
    id: 'light',
    label: 'Light Scan',
    description: 'Quick scan across major platforms (15-30 seconds)',
    estimatedTime: 15,
    phases: [
      { id: 1, name: 'Initialize Search', progress: 10 },
      { id: 2, name: 'Platform Lookup', progress: 30 },
      { id: 3, name: 'Email Verification', progress: 50 },
      { id: 4, name: 'Phone Validation', progress: 70 },
      { id: 5, name: 'Compiling Results', progress: 90 },
      { id: 6, name: 'Complete', progress: 100 },
    ],
  },
  DEEP: {
    id: 'deep',
    label: 'Deep Scan',
    description: 'Comprehensive search with network analysis (60-120 seconds)',
    estimatedTime: 90,
    phases: [
      { id: 1, name: 'Initialize Deep Scan', progress: 8 },
      { id: 2, name: 'Platform Scanning', progress: 20 },
      { id: 3, name: 'Email Cross-Reference', progress: 35 },
      { id: 4, name: 'Phone Intelligence', progress: 50 },
      { id: 5, name: 'Network Mapping', progress: 65 },
      { id: 6, name: 'Behavior Analysis', progress: 75 },
      { id: 7, name: 'Risk Scoring', progress: 85 },
      { id: 8, name: 'Graph Generation', progress: 95 },
      { id: 9, name: 'Complete', progress: 100 },
    ],
  },
};

// Risk score descriptions
export const RISK_SCORES = {
  CRITICAL: { min: 85, max: 100, label: 'Critical', color: '#dc2626', icon: '🔴' },
  HIGH: { min: 60, max: 84, label: 'High', color: '#f97316', icon: '🟠' },
  MEDIUM: { min: 40, max: 59, label: 'Medium', color: '#f59e0b', icon: '🟡' },
  LOW: { min: 20, max: 39, label: 'Low', color: '#84cc16', icon: '🟢' },
  MINIMAL: { min: 0, max: 19, label: 'Minimal', color: '#22c55e', icon: '🟢' },
};

// Investigation statuses
export const INVESTIGATION_STATUS = {
  PENDING: { id: 'pending', label: 'Pending', icon: '⏳', color: '#94a3b8' },
  RUNNING: { id: 'running', label: 'Running', icon: '⏱️', color: '#3b82f6' },
  COMPLETED: { id: 'completed', label: 'Completed', icon: '✅', color: '#10b981' },
  FAILED: { id: 'failed', label: 'Failed', icon: '❌', color: '#ef4444' },
  CANCELLED: { id: 'cancelled', label: 'Cancelled', icon: '⛔', color: '#6b7280' },
};

// Entity type colors (for graph visualization)
export const ENTITY_TYPES = {
  username: { color: '#ef4444', label: 'Username', icon: '👤' },
  email: { color: '#f59e0b', label: 'Email', icon: '📧' },
  phone: { color: '#a855f7', label: 'Phone', icon: '☎️' },
  location: { color: '#f97316', label: 'Location', icon: '📍' },
  keyword: { color: '#10b981', label: 'Keyword', icon: '🔑' },
  mention: { color: '#3b82f6', label: 'Mention', icon: '💬' },
  organization: { color: '#ec4899', label: 'Organization', icon: '🏢' },
};

// API configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
  POLL_INTERVAL_LIGHT: 500, // 500ms for light scans
  POLL_INTERVAL_DEEP: 2000, // 2s for deep scans
  POLL_MAX_ATTEMPTS: 300, // 5 minutes max
};

// Theme configuration
export const THEME_CONFIG = {
  colors: {
    primary: '#3b82f6',
    primaryLight: '#60a5fa',
    primaryDark: '#1e40af',
    accent: '#f59e0b',
    success: '#10b981',
    warning: '#f97316',
    danger: '#ef4444',
    info: '#3b82f6',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '40px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  fontSize: {
    xs: '12px',
    sm: '14px',
    md: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  },
};

// Notification types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// Tab definitions for case pages
export const CASE_TABS = {
  OVERVIEW: { id: 'overview', label: 'Overview', icon: '📊' },
  USERNAME: { id: 'username', label: 'Username', icon: '👤' },
  EMAILS: { id: 'emails', label: 'Emails', icon: '📧' },
  PHONES: { id: 'phones', label: 'Phones', icon: '☎️' },
  MENTIONS: { id: 'mentions', label: 'Mentions', icon: '💬' },
  GRAPH: { id: 'graph', label: 'Network Graph', icon: '🕸️' },
  RISK: { id: 'risk', label: 'Risk Assessment', icon: '⚠️' },
  REPORT: { id: 'report', label: 'Report', icon: '📄' },
};

// Graph export formats
export const EXPORT_FORMATS = {
  JSON: { id: 'json', label: 'JSON', mime: 'application/json' },
  CSV: { id: 'csv', label: 'CSV', mime: 'text/csv' },
  PNG: { id: 'png', label: 'PNG Image', mime: 'image/png' },
  SVG: { id: 'svg', label: 'SVG Vector', mime: 'image/svg+xml' },
  GRAPHML: { id: 'graphml', label: 'GraphML', mime: 'application/xml' },
};

// Report formats
export const REPORT_FORMATS = {
  PDF: { id: 'pdf', label: 'PDF Document', mime: 'application/pdf' },
  JSON: { id: 'json', label: 'JSON Data', mime: 'application/json' },
  HTML: { id: 'html', label: 'HTML Report', mime: 'text/html' },
  TEXT: { id: 'text', label: 'Plain Text', mime: 'text/plain' },
};

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
  INVALID_INPUT: 'Please check your input and try again.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNKNOWN_ERROR: 'An unknown error occurred. Please try again.',
};

// Success messages
export const SUCCESS_MESSAGES = {
  INVESTIGATION_CREATED: 'Investigation created successfully.',
  SCAN_STARTED: 'Scan started successfully.',
  REPORT_GENERATED: 'Report generated successfully.',
  DATA_EXPORTED: 'Data exported successfully.',
};

// Pagination defaults
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
  PAGE_SIZES: [10, 20, 50, 100],
};

// Local storage keys
export const STORAGE_KEYS = {
  THEME: 'osint_theme',
  RECENT_SEARCHES: 'osint_recent_searches',
  FAVORITES: 'osint_favorites',
  FILTERS: 'osint_filters',
  AUTH_TOKEN: 'osint_auth_token',
};

// Feature flags
export const FEATURES = {
  ADVANCED_FILTERS: true,
  GRAPH_EXPORT: true,
  BATCH_OPERATIONS: true,
  SCHEDULED_SCANS: false,
  MACHINE_LEARNING: false,
  COLLABORATION: false,
};

export default {
  PLATFORMS,
  PLATFORM_LIST,
  COUNTRIES,
  COUNTRY_LIST,
  ACCOUNT_TYPES,
  ACCOUNT_TYPE_LIST,
  VERIFICATION_STATUS,
  SCAN_TYPES,
  RISK_SCORES,
  INVESTIGATION_STATUS,
  ENTITY_TYPES,
  API_CONFIG,
  THEME_CONFIG,
  NOTIFICATION_TYPES,
  CASE_TABS,
  EXPORT_FORMATS,
  REPORT_FORMATS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  PAGINATION,
  STORAGE_KEYS,
  FEATURES,
};
