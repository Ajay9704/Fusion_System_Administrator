/**
 * Date formatting utilities for consistent date handling across the application
 * Ensures dates are always sent in YYYY-MM-DD format (Django DateField standard)
 */

/**
 * Format a JavaScript Date object to YYYY-MM-DD string
 * Uses local date components to avoid timezone offset issues from toISOString()
 *
 * @param {Date|null|undefined} date - The date to format
 * @returns {string|null} - Formatted date string in YYYY-MM-DD format, or null if no date
 */
export const formatDateForAPI = (date) => {
  if (!date) return null;

  // Check if it's already a string in correct format
  if (typeof date === 'string') {
    // If already in YYYY-MM-DD format, return as is
    if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return date;
    }
    // Try to parse the string
    date = new Date(date);
    // If invalid date, return null
    if (isNaN(date.getTime())) {
      return null;
    }
  }

  // Format using local date components (not UTC) to avoid timezone issues
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
};

/**
 * Parse a date string from API and return a Date object
 *
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @returns {Date|null} - Date object or null if invalid
 */
export const parseDateFromAPI = (dateString) => {
  if (!dateString) return null;

  const date = new Date(dateString);
  return isNaN(date.getTime()) ? null : date;
};

/**
 * Format a date for display in a user-friendly format
 *
 * @param {Date|string} date - Date to format
 * @param {string} format - Format type: 'short', 'long', 'time'
 * @returns {string} - Formatted date string
 */
export const formatDateForDisplay = (date, format = 'short') => {
  if (!date) return '';

  const dateObj = typeof date === 'string' ? new Date(date) : date;

  if (isNaN(dateObj.getTime())) return '';

  const options = {
    short: { year: 'numeric', month: 'short', day: 'numeric' },
    long: { year: 'numeric', month: 'long', day: 'numeric' },
    time: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
  };

  return dateObj.toLocaleDateString('en-US', options[format] || options.short);
};

/**
 * Validate if a date string is in correct YYYY-MM-DD format
 *
 * @param {string} dateString - Date string to validate
 * @returns {boolean} - True if valid format
 */
export const isValidDateFormat = (dateString) => {
  if (!dateString || typeof dateString !== 'string') return false;

  // Check format
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return false;

  // Check if it's a valid date
  const date = new Date(dateString);
  return !isNaN(date.getTime());
};

/**
 * Get today's date in YYYY-MM-DD format
 *
 * @returns {string} - Today's date in YYYY-MM-DD format
 */
export const getTodayDate = () => {
  return formatDateForAPI(new Date());
};

/**
 * Calculate age from date of birth
 *
 * @param {Date|string} dateOfBirth - Date of birth
 * @returns {number|null} - Age in years, or null if invalid
 */
export const calculateAge = (dateOfBirth) => {
  if (!dateOfBirth) return null;

  const dob = typeof dateOfBirth === 'string' ? new Date(dateOfBirth) : dateOfBirth;
  if (isNaN(dob.getTime())) return null;

  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }

  return age;
};
