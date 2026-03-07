/**
 * Form validation utilities for OSINT investigations
 * Handles validation for usernames, emails, phones, and form state
 */

// Validation regex patterns
export const PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^[\d\s\-\+\(\)]{7,20}$/, // Flexible phone format
  USERNAME: /^[a-zA-Z0-9._\-]{2,30}$/, // 2-30 chars, alphanumeric + . _ -
  URL: /^https?:\/\/.+/,
  SPECIAL_CHARS: /[!@#$%^&*(),.?":{}|<>]/g,
};

/**
 * Validate email address
 */
export function validateEmail(email) {
  if (!email) return { valid: true, error: null }; // Optional field

  const trimmed = email.trim();

  if (trimmed.length < 5 || trimmed.length > 254) {
    return { valid: false, error: 'Email must be between 5 and 254 characters' };
  }

  if (!PATTERNS.EMAIL.test(trimmed)) {
    return { valid: false, error: 'Invalid email format' };
  }

  return { valid: true, error: null };
}

/**
 * Validate phone number
 */
export function validatePhone(phone, countryCode = '+1') {
  if (!phone) return { valid: true, error: null }; // Optional field

  const trimmed = phone.trim();

  if (trimmed.length < 7 || trimmed.length > 20) {
    return { valid: false, error: 'Phone must be between 7 and 20 characters' };
  }

  if (!PATTERNS.PHONE.test(trimmed)) {
    return { valid: false, error: 'Invalid phone format' };
  }

  // Check for minimum digits (at least 7)
  const digitCount = (trimmed.match(/\d/g) || []).length;
  if (digitCount < 7) {
    return { valid: false, error: 'Phone must contain at least 7 digits' };
  }

  return { valid: true, error: null };
}

/**
 * Validate username
 */
export function validateUsername(username) {
  if (!username) {
    return { valid: false, error: 'Username is required' };
  }

  const trimmed = username.trim();

  if (trimmed.length < 2) {
    return { valid: false, error: 'Username must be at least 2 characters' };
  }

  if (trimmed.length > 30) {
    return { valid: false, error: 'Username must be at most 30 characters' };
  }

  if (!PATTERNS.USERNAME.test(trimmed)) {
    return {
      valid: false,
      error: 'Username can only contain letters, numbers, dots, hyphens, and underscores',
    };
  }

  return { valid: true, error: null };
}

/**
 * Validate entire investigation form
 */
export function validateInvestigationForm(formData) {
  const errors = {};

  // Validate username (required)
  const usernameValidation = validateUsername(formData.username);
  if (!usernameValidation.valid) {
    errors.username = usernameValidation.error;
  }

  // Validate email (optional)
  if (formData.email) {
    const emailValidation = validateEmail(formData.email);
    if (!emailValidation.valid) {
      errors.email = emailValidation.error;
    }
  }

  // Validate phone (optional)
  if (formData.phone) {
    const phoneValidation = validatePhone(formData.phone, formData.dialCode);
    if (!phoneValidation.valid) {
      errors.phone = phoneValidation.error;
    }
  }

  // At least one search parameter must be provided
  if (!formData.username && !formData.email && !formData.phone) {
    errors.general = 'Please provide at least a username';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Sanitize input to prevent injection attacks
 */
export function sanitizeInput(input) {
  if (typeof input !== 'string') return input;

  return input
    .trim()
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .substring(0, 1024); // Limit length
}

/**
 * Normalize phone number for API calls
 */
export function normalizePhone(phone, countryCode = '+1') {
  if (!phone) return null;

  // Remove all non-digit characters
  const digitsOnly = phone.replace(/\D/g, '');

  // Format with country code
  if (!digitsOnly.startsWith('1') && countryCode === '+1') {
    return `+1${digitsOnly}`;
  }

  return `${countryCode}${digitsOnly}`;
}

/**
 * Check if email looks like a test/fake email
 */
export function isTestEmail(email) {
  if (!email) return false;

  const testPatterns = [
    'test@',
    'demo@',
    'example@',
    'temp@',
    'fake@',
    'noreply@',
    '@test.com',
    '@example.com',
    '@temp.com',
  ];

  const lowerEmail = email.toLowerCase();
  return testPatterns.some(pattern => lowerEmail.includes(pattern));
}

/**
 * Estimate investigation difficulty based on inputs
 */
export function estimateSearchDifficulty(formData) {
  let score = 0;

  // Username length (shorter = more common = harder)
  if (formData.username) {
    const len = formData.username.length;
    if (len < 5) score += 3; // Very common
    else if (len < 8) score += 2; // Common
    else score += 1; // Less common
  }

  // Email provided = easier (faster narrowing)
  if (formData.email) score += 2;

  // Phone provided = easier (faster narrowing)
  if (formData.phone) score += 2;

  // With platform filters = easier
  if (formData.filters.platforms && formData.filters.platforms.length > 0) {
    score += 1;
  }

  // With location filters = easier
  if (formData.filters.location) score += 1;

  // Scale to 1-10
  return Math.min(Math.ceil(score), 10);
}

/**
 * Estimate scan time based on inputs
 */
export function estimateScanTime(scanType, difficulty) {
  const baseTime = scanType === 'light' ? 15 : 60; // seconds
  const difficultyMultiplier = 1 + (difficulty / 10); // 1x to 2x

  return Math.round(baseTime * difficultyMultiplier);
}

/**
 * Get search tips based on inputs
 */
export function getSearchTips(formData) {
  const tips = [];

  const username = formData.username?.trim();
  if (username && username.length < 4) {
    tips.push('⚠️ Short usernames are very common. Consider adding email or phone for better results.');
  }

  if (username && /^\d+$/.test(username)) {
    tips.push('ℹ️ Numeric usernames are common. Adding platform filters may help narrow results.');
  }

  if (!formData.email && !formData.phone) {
    tips.push('✓ Adding email or phone will significantly speed up the search.');
  }

  if (formData.filters.platforms?.length === 0) {
    tips.push('✓ Selecting specific platforms will narrow results and reduce scan time.');
  }

  if (formData.filters.location) {
    tips.push('✓ Location filter applied - this will help find location-specific matches.');
  }

  if (formData.email && isTestEmail(formData.email)) {
    tips.push('⚠️ This appears to be a test email. Results may be limited.');
  }

  return tips;
}

/**
 * Format validation error for display
 */
export function formatValidationError(field, error) {
  const fieldLabels = {
    username: 'Username',
    email: 'Email',
    phone: 'Phone',
    general: 'Form',
  };

  const label = fieldLabels[field] || field;
  return `${label}: ${error}`;
}

/**
 * Check if form has unsaved changes
 */
export function hasFormChanges(currentData, originalData) {
  if (!originalData) return true; // New form = has changes

  return (
    currentData.username !== originalData.username ||
    currentData.email !== originalData.email ||
    currentData.phone !== originalData.phone ||
    currentData.dialCode !== originalData.dialCode ||
    currentData.scanType !== originalData.scanType ||
    JSON.stringify(currentData.filters) !== JSON.stringify(originalData.filters)
  );
}

/**
 * Extract identifiable information from form
 */
export function extractIdentifiers(formData) {
  const identifiers = [];

  if (formData.username) {
    identifiers.push({ type: 'username', value: formData.username });
  }

  if (formData.email) {
    identifiers.push({ type: 'email', value: formData.email });
  }

  if (formData.phone) {
    identifiers.push({ type: 'phone', value: formData.phone });
  }

  return identifiers;
}

/**
 * Generate summary of search parameters
 */
export function generateSearchSummary(formData) {
  const parts = [];

  if (formData.username) parts.push(`username: ${formData.username}`);
  if (formData.email) parts.push(`email: ${formData.email}`);
  if (formData.phone) parts.push(`phone: ${formData.dialCode}${formData.phone}`);

  if (formData.filters.platforms?.length > 0) {
    parts.push(`platforms: ${formData.filters.platforms.join(', ')}`);
  }

  if (formData.filters.location) {
    parts.push(`location: ${formData.filters.location}`);
  }

  if (formData.filters.accountType && formData.filters.accountType !== 'all') {
    parts.push(`type: ${formData.filters.accountType}`);
  }

  if (formData.filters.verified && formData.filters.verified !== 'all') {
    parts.push(`verified: ${formData.filters.verified}`);
  }

  return parts.join(' | ');
}

export default {
  PATTERNS,
  validateEmail,
  validatePhone,
  validateUsername,
  validateInvestigationForm,
  sanitizeInput,
  normalizePhone,
  isTestEmail,
  estimateSearchDifficulty,
  estimateScanTime,
  getSearchTips,
  formatValidationError,
  hasFormChanges,
  extractIdentifiers,
  generateSearchSummary,
};
