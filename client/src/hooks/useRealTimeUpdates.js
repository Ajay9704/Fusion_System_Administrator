/**
 * Enterprise-Grade Real-Time Update Hook
 * Provides automatic data refresh across all pages
 * Configurable intervals and smart caching
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const useRealTimeUpdates = (fetchFunction, options = {}) => {
  const {
    interval = 30000, // 30 seconds default (enterprise standard)
    immediate = true,
    enabled = true,
    onSuccess = null,
    onError = null
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);
  const isMountedRef = useRef(true);

  const fetchData = useCallback(async (showLoading = true) => {
    if (!enabled || !isMountedRef.current) return;

    if (showLoading) setLoading(true);
    setError(null);

    try {
      const result = await fetchFunction();

      if (isMountedRef.current) {
        setData(result);
        setLastUpdated(new Date());
        if (onSuccess) onSuccess(result);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
        if (onError) onError(err);
      }
    } finally {
      if (isMountedRef.current && showLoading) {
        setLoading(false);
      }
    }
  }, [fetchFunction, enabled, onSuccess, onError]);

  // Manual refresh function
  const refresh = useCallback(() => {
    return fetchData(true);
  }, [fetchData]);

  // Silent refresh (no loading state)
  const silentRefresh = useCallback(() => {
    return fetchData(false);
  }, [fetchData]);

  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch
    if (immediate && enabled) {
      fetchData(true);
    }

    // Set up interval for auto-refresh
    if (enabled && interval > 0) {
      intervalRef.current = setInterval(() => {
        silentRefresh();
      }, interval);
    }

    // Cleanup
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, immediate, enabled, interval, silentRefresh]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refresh,
    silentRefresh
  };
};

export default useRealTimeUpdates;
