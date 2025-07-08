// Persistent authentication utilities for tenant authentication

export const TENANT_ID_KEY = 'audienceai_tenant_id';
export const AUTH_TIMESTAMP_KEY = 'audienceai_auth_timestamp';

// Authentication expires after 30 days (in milliseconds)
const AUTH_EXPIRATION_TIME = 30 * 24 * 60 * 60 * 1000; // 30 days

/**
 * Get tenant ID from localStorage with expiration check
 */
export const getTenantId = () => {
  if (typeof window === 'undefined') return null;
  
  try {
    const tenantId = localStorage.getItem(TENANT_ID_KEY);
    const authTimestamp = localStorage.getItem(AUTH_TIMESTAMP_KEY);
    
    if (!tenantId || !authTimestamp) return null;
    
    // Check if authentication has expired
    const now = Date.now();
    const authTime = parseInt(authTimestamp, 10);
    
    if (now - authTime > AUTH_EXPIRATION_TIME) {
      // Authentication expired, clear it
      clearTenantId();
      return null;
    }
    
    return tenantId;
  } catch (error) {
    console.error('Error getting tenant ID from localStorage:', error);
    return null;
  }
};

/**
 * Set tenant ID in localStorage with timestamp
 */
export const setTenantId = (tenantId) => {
  if (typeof window === 'undefined') return false;
  
  try {
    if (tenantId) {
      localStorage.setItem(TENANT_ID_KEY, tenantId);
      localStorage.setItem(AUTH_TIMESTAMP_KEY, Date.now().toString());
    } else {
      localStorage.removeItem(TENANT_ID_KEY);
      localStorage.removeItem(AUTH_TIMESTAMP_KEY);
    }
    return true;
  } catch (error) {
    console.error('Error setting tenant ID in localStorage:', error);
    return false;
  }
};

/**
 * Remove tenant ID from localStorage (sign out)
 */
export const clearTenantId = () => {
  if (typeof window === 'undefined') return false;
  
  try {
    localStorage.removeItem(TENANT_ID_KEY);
    localStorage.removeItem(AUTH_TIMESTAMP_KEY);
    return true;
  } catch (error) {
    console.error('Error clearing tenant ID from localStorage:', error);
    return false;
  }
};

/**
 * Validate if a string is a valid UUID format
 */
export const isValidUUID = (str) => {
  if (!str || typeof str !== 'string') return false;
  
  // UUID v4 regex pattern
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str.trim());
};

/**
 * Check if user is authenticated (has valid tenant ID)
 */
export const isAuthenticated = () => {
  const tenantId = getTenantId();
  return tenantId && tenantId.trim() !== '' && isValidUUID(tenantId);
};

/**
 * Refresh authentication timestamp to extend session
 */
export const refreshAuthTimestamp = () => {
  if (typeof window === 'undefined') return false;
  
  try {
    const tenantId = localStorage.getItem(TENANT_ID_KEY);
    if (tenantId) {
      localStorage.setItem(AUTH_TIMESTAMP_KEY, Date.now().toString());
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error refreshing auth timestamp:', error);
    return false;
  }
};
