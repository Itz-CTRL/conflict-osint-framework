/**
 * Theme management utilities for light/dark mode switching
 */

export const THEMES = {
  light: {
    name: 'light',
    colors: {
      // Primary
      primary: '#3b82f6',
      primaryLight: '#60a5fa',
      primaryDark: '#1e40af',
      
      // Accent
      accent: '#f59e0b',
      accentLight: '#fbbf24',
      accentDark: '#d97706',
      
      // Status colors
      success: '#10b981',
      warning: '#f97316',
      danger: '#ef4444',
      info: '#3b82f6',
      
      // Backgrounds
      background: '#ffffff',
      backgroundAlt: '#f9fafb',
      backgroundMuted: '#f3f4f6',
      
      // Surfaces
      surface: '#ffffff',
      surfaceAlt: '#f9fafb',
      surfaceHover: '#f3f4f6',
      
      // Borders
      border: '#e5e7eb',
      borderLight: '#f3f4f6',
      borderDark: '#d1d5db',
      
      // Text
      text: '#111827',
      textAlt: '#374151',
      textMuted: '#6b7280',
      textSubtle: '#9ca3af',
      textInverse: '#ffffff',
      
      // Type colors (for graph visualization)
      typeProfile: '#ef4444',
      typePlatform: '#06b6d4',
      typeEmail: '#f59e0b',
      typePhone: '#a855f7',
      typeKeyword: '#10b981',
      typeMention: '#3b82f6',
      typeLocation: '#f97316',
      typeOrg: '#ec4899',
      
      // Risk colors
      riskCritical: '#dc2626',
      riskHigh: '#f97316',
      riskMed: '#f59e0b',
      riskLow: '#84cc16',
      riskMinimal: '#22c55e',
      
      // Shadows
      shadow: 'rgba(0, 0, 0, 0.1)',
      shadowDark: 'rgba(0, 0, 0, 0.2)',
    },
  },
  dark: {
    name: 'dark',
    colors: {
      // Primary
      primary: '#3b82f6',
      primaryLight: '#60a5fa',
      primaryDark: '#1e40af',
      
      // Accent
      accent: '#f59e0b',
      accentLight: '#fbbf24',
      accentDark: '#d97706',
      
      // Status colors
      success: '#10b981',
      warning: '#f97316',
      danger: '#ef4444',
      info: '#3b82f6',
      
      // Backgrounds
      background: '#0f172a',
      backgroundAlt: '#1e293b',
      backgroundMuted: '#334155',
      
      // Surfaces
      surface: '#1f2937',
      surfaceAlt: '#111827',
      surfaceHover: '#2d3748',
      
      // Borders
      border: '#374151',
      borderLight: '#4b5563',
      borderDark: '#1f2937',
      
      // Text
      text: '#f3f4f6',
      textAlt: '#e5e7eb',
      textMuted: '#9ca3af',
      textSubtle: '#6b7280',
      textInverse: '#111827',
      
      // Type colors (for graph visualization)
      typeProfile: '#ef4444',
      typePlatform: '#06b6d4',
      typeEmail: '#f59e0b',
      typePhone: '#a855f7',
      typeKeyword: '#10b981',
      typeMention: '#3b82f6',
      typeLocation: '#f97316',
      typeOrg: '#ec4899',
      
      // Risk colors
      riskCritical: '#dc2626',
      riskHigh: '#f97316',
      riskMed: '#f59e0b',
      riskLow: '#84cc16',
      riskMinimal: '#22c55e',
      
      // Shadows
      shadow: 'rgba(0, 0, 0, 0.3)',
      shadowDark: 'rgba(0, 0, 0, 0.5)',
    },
  },
};

/**
 * Get the current theme
 */
export function getCurrentTheme() {
  const stored = localStorage.getItem('theme');
  if (stored) return stored;

  // Check if system prefers dark mode
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
}

/**
 * Save theme preference
 */
export function saveTheme(themeName) {
  localStorage.setItem('theme', themeName);
  applyTheme(themeName);
}

/**
 * Apply theme to document
 */
export function applyTheme(themeName) {
  const theme = THEMES[themeName] || THEMES.light;
  const root = document.documentElement;

  // Set CSS variables
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value);
  });

  // Update document class
  document.documentElement.classList.remove('light', 'dark');
  document.documentElement.classList.add(themeName);

  // Update meta theme color for mobile
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.setAttribute(
      'content',
      theme.colors.primary
    );
  }
}

/**
 * Toggle between light and dark themes
 */
export function toggleTheme() {
  const currentTheme = getCurrentTheme();
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  saveTheme(newTheme);
  return newTheme;
}

/**
 * Get color value for current theme
 */
export function getThemeColor(colorKey, themeName = null) {
  const theme = themeName ? THEMES[themeName] : THEMES[getCurrentTheme()];
  return theme?.colors?.[colorKey] || '#000000';
}

/**
 * Create CSS module from theme
 */
export function createThemeStyles() {
  const themeName = getCurrentTheme();
  const theme = THEMES[themeName];

  const rootVars = {};
  Object.entries(theme.colors).forEach(([key, value]) => {
    rootVars[`--color-${key}`] = value;
  });

  return rootVars;
}

/**
 * Initialize theme on app load
 */
export function initializeTheme() {
  const themeName = getCurrentTheme();
  applyTheme(themeName);

  // Listen for system theme changes
  if (window.matchMedia) {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

/**
 * Get contrast color for background
 */
export function getContrastColor(backgroundColor, themeName = null) {
  const theme = THEMES[themeName || getCurrentTheme()];
  
  // Simple luminance calculation
  const hex = backgroundColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  return luminance > 0.5 ? theme.colors.text : theme.colors.textInverse;
}

/**
 * Convert hex to rgba
 */
export function hexToRgba(hex, alpha = 1) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Create gradient from two colors
 */
export function createGradient(color1, color2, angle = 90) {
  return `linear-gradient(${angle}deg, ${color1}, ${color2})`;
}

/**
 * Get color palette for data visualization
 */
export function getVisualizationPalette(themeName = null) {
  const theme = THEMES[themeName || getCurrentTheme()];
  
  return [
    theme.colors.primary,
    theme.colors.accent,
    theme.colors.success,
    theme.colors.warning,
    theme.colors.danger,
    theme.colors.info,
    theme.colors.typeProfile,
    theme.colors.typePlatform,
    theme.colors.typeEmail,
    theme.colors.typePhone,
  ];
}

/**
 * Map risk score to color
 */
export function getRiskColor(score, themeName = null) {
  const theme = THEMES[themeName || getCurrentTheme()];
  
  if (score >= 85) return theme.colors.riskCritical;
  if (score >= 60) return theme.colors.riskHigh;
  if (score >= 40) return theme.colors.riskMed;
  if (score >= 20) return theme.colors.riskLow;
  return theme.colors.riskMinimal;
}

/**
 * Format theme-aware box shadow
 */
export function getBoxShadow(intensity = 'md', themeName = null) {
  const theme = THEMES[themeName || getCurrentTheme()];
  const isDark = (themeName || getCurrentTheme()) === 'dark';
  
  const shadows = {
    sm: `0 1px 2px 0 ${theme.colors.shadow}`,
    md: `0 4px 6px -1px ${theme.colors.shadow}`,
    lg: `0 10px 15px -3px ${theme.colors.shadow}`,
    xl: `0 20px 25px -5px ${theme.colors.shadowDark}`,
  };
  
  return shadows[intensity] || shadows.md;
}

export default {
  THEMES,
  getCurrentTheme,
  saveTheme,
  applyTheme,
  toggleTheme,
  getThemeColor,
  createThemeStyles,
  initializeTheme,
  getContrastColor,
  hexToRgba,
  createGradient,
  getVisualizationPalette,
  getRiskColor,
  getBoxShadow,
};
