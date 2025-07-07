// Session management utilities for tenant authentication

export const TENANT_ID_KEY = 'audienceai_tenant_id';

/**
 * Get tenant ID from session storage
 */
export const getTenantId = () => {
  if (typeof window === 'undefined') return null;
  
  try {
    return sessionStorage.getItem(TENANT_ID_KEY);
  } catch (error) {
    console.error('Error getting tenant ID from session:', error);
    return null;
  }
};

/**
 * Set tenant ID in session storage
 */
export const setTenantId = (tenantId) => {
  if (typeof window === 'undefined') return false;
  
  try {
    if (tenantId) {
      sessionStorage.setItem(TENANT_ID_KEY, tenantId);
    } else {
      sessionStorage.removeItem(TENANT_ID_KEY);
    }
    return true;
  } catch (error) {
    console.error('Error setting tenant ID in session:', error);
    return false;
  }
};

/**
 * Remove tenant ID from session storage (sign out)
 */
export const clearTenantId = () => {
  if (typeof window === 'undefined') return false;
  
  try {
    sessionStorage.removeItem(TENANT_ID_KEY);
    return true;
  } catch (error) {
    console.error('Error clearing tenant ID from session:', error);
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