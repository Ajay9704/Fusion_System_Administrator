/**
 * Performance Optimization Utilities
 * Enterprise-grade performance monitoring and optimization tools
 */

/**
 * Debounce function to limit execution rate
 */
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Throttle function to limit execution frequency
 */
export const throttle = (func, limit) => {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Lazy load component with error boundary
 */
export const lazyLoad = (importFunc) => {
  return React.lazy(() =>
    importFunc().catch((error) => {
      console.error('Component loading failed:', error)
      return {
        default: () => (
          <div className="error-boundary">
            <h3>Component failed to load</h3>
            <button onClick={() => window.location.reload()}>
              Reload Page
            </button>
          </div>
        )
      }
    })
  )
}

/**
 * Performance monitoring hook
 */
export const usePerformanceMonitor = (componentName) => {
  React.useEffect(() => {
    const startTime = performance.now()

    return () => {
      const endTime = performance.now()
      const renderTime = endTime - startTime

      if (renderTime > 100) { // Log slow renders
        console.warn(`${componentName} took ${renderTime.toFixed(2)}ms to render`)
      }

      // Send to analytics in production
      if (import.meta.env.PROD && window.gtag) {
        window.gtag('event', 'component_render_time', {
          component_name: componentName,
          render_time: renderTime
        })
      }
    }
  }, [componentName])
}

/**
 * Memoization hook for expensive computations
 */
export const useMemoizedCallback = (callback, deps) => {
  return React.useCallback(callback, deps)
}

/**
 * Image lazy loading with placeholder
 */
export const LazyImage = ({ src, alt, placeholder, className, ...props }) => {
  const [imageSrc, setImageSrc] = React.useState(placeholder)
  const [imageRef, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  })

  React.useEffect(() => {
    if (inView && src) {
      const img = new Image()
      img.src = src
      img.onload = () => setImageSrc(src)
    }
  }, [inView, src])

  return (
    <img
      ref={imageRef}
      src={imageSrc}
      alt={alt}
      className={className}
      loading="lazy"
      {...props}
    />
  )
}

/**
 * Virtual scroll hook for large lists
 */
export const useVirtualScroll = (items, itemHeight, containerHeight) => {
  const [scrollTop, setScrollTop] = React.useState(0)

  const visibleStart = Math.floor(scrollTop / itemHeight)
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  )

  const visibleItems = items.slice(visibleStart, visibleEnd)
  const offsetY = visibleStart * itemHeight
  const totalHeight = items.length * itemHeight

  return {
    visibleItems,
    offsetY,
    totalHeight,
    onScroll: (e) => setScrollTop(e.target.scrollTop)
  }
}

/**
 * Cache management utility
 */
class CacheManager {
  constructor(ttl = 300000) { // 5 minutes default
    this.cache = new Map()
    this.ttl = ttl
  }

  set(key, value, customTTL) {
    const expiry = Date.now() + (customTTL || this.ttl)
    this.cache.set(key, { value, expiry })
  }

  get(key) {
    const item = this.cache.get(key)
    if (!item) return null

    if (Date.now() > item.expiry) {
      this.cache.delete(key)
      return null
    }

    return item.value
  }

  clear() {
    this.cache.clear()
  }

  // Clean expired entries
  clean() {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key)
      }
    }
  }
}

export const cacheManager = new CacheManager()

/**
 * Request batching utility
 */
export const batchRequests = (requests, batchSize = 5) => {
  return new Promise((resolve, reject) => {
    const results = []
    let completed = 0
    let hasError = false

    const processBatch = async (start) => {
      const end = Math.min(start + batchSize, requests.length)
      const batch = requests.slice(start, end)

      try {
        const batchResults = await Promise.all(batch)
        results.push(...batchResults)
        completed = end

        if (end < requests.length && !hasError) {
          processBatch(end)
        } else if (completed === requests.length) {
          resolve(results)
        }
      } catch (error) {
        hasError = true
        reject(error)
      }
    }

    processBatch(0)
  })
}

/**
 * Performance metrics collector
 */
export const collectPerformanceMetrics = () => {
  if (!window.performance) return null

  const navigationTiming = performance.getEntriesByType('navigation')[0]
  const paintTiming = performance.getEntriesByType('paint')

  return {
    // Page load metrics
    pageLoadTime: navigationTiming?.loadEventEnd - navigationTiming?.navigationStart,
    domContentLoaded: navigationTiming?.domContentLoadedEventEnd - navigationTiming?.navigationStart,

    // Paint metrics
    firstPaint: paintTiming.find(entry => entry.name === 'first-paint')?.startTime,
    firstContentfulPaint: paintTiming.find(entry => entry.name === 'first-contentful-paint')?.startTime,

    // Resource metrics
    resourceCount: performance.getEntriesByType('resource').length,

    // Memory (if available)
    memory: performance.memory ? {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
    } : null
  }
}

/**
 * Report performance metrics to analytics
 */
export const reportPerformanceMetrics = () => {
  const metrics = collectPerformanceMetrics()
  if (!metrics) return

  // Send to Google Analytics if available
  if (window.gtag) {
    window.gtag('event', 'page_timing', {
      page_load_time: metrics.pageLoadTime,
      dom_content_loaded: metrics.domContentLoaded,
      first_paint: metrics.firstPaint,
      first_contentful_paint: metrics.firstContentfulPaint
    })
  }

  // Log in development
  if (import.meta.env.DEV) {
    console.log('Performance Metrics:', metrics)
  }

  return metrics
}

/**
 * Optimize images with WebP format fallback
 */
export const getOptimizedImageUrl = (imageUrl, width, height) => {
  if (!imageUrl) return ''

  // Check if image is from external source
  if (imageUrl.startsWith('http')) {
    // For external images, return as-is (or use CDN service)
    return imageUrl
  }

  // For local images, add optimization parameters
  const url = new URL(imageUrl, window.location.origin)
  url.searchParams.set('width', width)
  url.searchParams.set('height', height)
  url.searchParams.set('format', 'webp')

  return url.toString()
}