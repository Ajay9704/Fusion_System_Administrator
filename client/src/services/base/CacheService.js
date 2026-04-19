/**
 * Enterprise Cache Service
 * Provides client-side caching with TTL support for API responses
 */

class CacheService {
  constructor() {
    this.cache = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes default TTL
  }

  set(key, value, ttl = this.defaultTTL) {
    const expiry = Date.now() + ttl;
    this.cache.set(key, { value, expiry });
    return true;
  }

  get(key) {
    const item = this.cache.get(key);

    if (!item) {
      return null;
    }

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  has(key) {
    const item = this.cache.get(key);

    if (!item) {
      return false;
    }

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    if (key.includes('*')) {
      const escapedPattern = key
        .split('*')
        .map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('.*');
      const matcher = new RegExp(`^${escapedPattern}$`);
      let deleted = false;

      for (const cacheKey of this.cache.keys()) {
        if (matcher.test(cacheKey)) {
          this.cache.delete(cacheKey);
          deleted = true;
        }
      }

      return deleted;
    }

    return this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }

  // Cache key generator for consistent key generation
  static generateKey(prefix, params = {}) {
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&');

    return `${prefix}:${sortedParams}`;
  }

  // Get cache statistics
  getStats() {
    let expired = 0;
    let active = 0;

    for (const [key, item] of this.cache.entries()) {
      if (Date.now() > item.expiry) {
        expired++;
      } else {
        active++;
      }
    }

    return {
      total: this.cache.size,
      active,
      expired,
      size: JSON.stringify([...this.cache.entries()]).length,
    };
  }

  // Clean expired entries
  clean() {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key);
      }
    }
  }
}

// Export singleton instance
const cacheService = new CacheService();
// Clean cache every 10 minutes
setInterval(() => cacheService.clean(), 10 * 60 * 1000);

export default cacheService;
