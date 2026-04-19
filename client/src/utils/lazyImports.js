/**
 * Lazy Loading Configuration
 * Enterprise-grade code splitting and lazy loading for optimal performance
 */

import { lazy, Suspense } from 'react'
import { Center, Loader, Text, Container } from '@mantine/core'

/**
 * Loading fallback component
 */
export const LoadingFallback = () => (
  <Container style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
    <Center style={{ flexDirection: 'column', gap: '1rem' }}>
      <Loader size="lg" color="blue" />
      <Text size="sm" color="dimmed">
        Loading...
      </Text>
    </Center>
  </Container>
)

/**
 * Error boundary fallback component
 */
export const ErrorFallback = ({ error, resetError }) => (
  <Container style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
    <Center style={{ flexDirection: 'column', gap: '1rem', textAlign: 'center' }}>
      <Text size="xl" weight={700} color="red">
        Something went wrong
      </Text>
      <Text size="sm" color="dimmed">
        {error?.message || 'An unexpected error occurred'}
      </Text>
      <button
        onClick={resetError}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#228BE6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Try Again
      </button>
    </Center>
  </Container>
)

/**
 * Higher-order component for lazy loading with error handling
 */
const withLazyLoading = (importFunc, fallback = LoadingFallback) => {
  const LazyComponent = lazy(() =>
    importFunc().catch((error) => {
      console.error('Lazy loading failed:', error)
      // Return error component
      return {
        default: () => (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <h3>Failed to load component</h3>
            <button onClick={() => window.location.reload()}>Reload</button>
          </div>
        )
      }
    })
  )

  return (props) => (
    <Suspense fallback={<fallback />}>
      <LazyComponent {...props} />
    </Suspense>
  )
}

/**
 * Lazy loaded page components
 */
export const LazyPages = {
  // Authentication
  LoginPage: withLazyLoading(() => import('../pages/Login/LoginPage')),

  // User Management
  StudentCreationPage: withLazyLoading(() => import('../pages/UserManagementPages/StudentCreationPage')),
  FacultyCreationPage: withLazyLoading(() => import('../pages/UserManagementPages/FacultyCreationPage')),
  StaffCreationPage: withLazyLoading(() => import('../pages/UserManagementPages/StaffCreationPage')),
  DeleteUserPage: withLazyLoading(() => import('../pages/UserManagementPages/DeleteUserPage')),
  ResetUserPasswordPage: withLazyLoading(() => import('../pages/UserManagementPages/ResetUserPasswordPage')),
  AuditLogViewerPage: withLazyLoading(() => import('../pages/UserManagementPages/AuditLogViewerPage')),

  // Role Management
  CreateCustomRolePage: withLazyLoading(() => import('../pages/RoleManagementPages/CreateCustomRolePage')),
  EditUserRolePage: withLazyLoading(() => import('../pages/RoleManagementPages/EditUserRolePage')),
  ManageRoleAccessPage: withLazyLoading(() => import('../pages/RoleManagementPages/ManageRoleAccessPage')),

  // Department Management
  DepartmentManagementPage: withLazyLoading(() => import('../pages/DepartmentManagement/DepartmentManagementPage')),

  // Emergency Access
  EmergencyAccessPage: withLazyLoading(() => import('../pages/EmergencyAccess/EmergencyAccessPage')),

  // Archiving
  ArchiveStudentsPage: withLazyLoading(() => import('../pages/ArchivingPages/ArchiveStudentsPage')),
  ArchiveFacultyPage: withLazyLoading(() => import('../pages/ArchivingPages/ArchiveFacultyPage')),
  ArchiveUsersPage: withLazyLoading(() => import('../pages/ArchivingPages/ArchiveUsersPage')),
  ArchiveAnnouncementsPage: withLazyLoading(() => import('../pages/ArchivingPages/ArchiveAnnouncementsPage')),
  ArchiveNotificationsPage: withLazyLoading(() => import('../pages/ArchivingPages/ArchiveNotificationsPage')),

  // User Directory
  UserDirectory: withLazyLoading(() => import('../pages/UserDirectory/UserDirectory')),
}

/**
 * Lazy loaded feature components
 */
export const LazyComponents = {
  // Forms
  StudentForm: withLazyLoading(() => import('../components/forms/StudentForm')),
  FacultyForm: withLazyLoading(() => import('../components/forms/FacultyForm')),
  StaffForm: withLazyLoading(() => import('../components/forms/StaffForm')),

  // Modals
  BulkUploadModal: withLazyLoading(() => import('../components/BulkUploadModal/BulkUploadModal')),

  // Charts
  BarChart: withLazyLoading(() => import('../components/charts/BarChart')),
  PieChart: withLazyLoading(() => import('../components/charts/PieChart')),
  LineChart: withLazyLoading(() => import('../components/charts/LineChart')),

  // Features
  StatsGrid: withLazyLoading(() => import('../components/StatsGrid/StatsGrid')),
  FeaturesCards: withLazyLoading(() => import('../components/FeaturesCards/FeaturesCards')),
  RoleSwitcher: withLazyLoading(() => import('../components/RoleSwitcher/RoleSwitcher')),
}

/**
 * Prefetch component for improved perceived performance
 */
export const prefetchComponent = (importFunc) => {
  // Prefetch component when user is idle
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      importFunc()
    })
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      importFunc()
    }, 2000)
  }
}

/**
 * Prefetch multiple components
 */
export const prefetchComponents = (importFunctions) => {
  importFunctions.forEach((importFunc, index) => {
    // Stagger prefetching to avoid overwhelming the network
    setTimeout(() => {
      prefetchComponent(importFunc)
    }, index * 100)
  })
}

/**
 * Smart prefetching based on user behavior
 */
export const setupSmartPrefetching = () => {
  // Prefetch likely next pages based on current route
  const prefetchMap = {
    '/login': () => import('../pages/UserDirectory/UserDirectory'),
    '/user-directory': () => import('../pages/UserManagementPages/StudentCreationPage'),
    '/student-creation': () => import('../pages/UserManagementPages/FacultyCreationPage'),
  }

  // Prefetch on mouse hover (desktop)
  document.querySelectorAll('[data-prefetch]').forEach(element => {
    element.addEventListener('mouseenter', () => {
      const prefetchUrl = element.getAttribute('data-prefetch')
      if (prefetchMap[prefetchUrl]) {
        prefetchComponent(prefetchMap[prefetchUrl])
      }
    }, { once: true })
  })

  // Prefetch on visible (for mobile)
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const prefetchUrl = entry.target.getAttribute('data-prefetch')
          if (prefetchMap[prefetchUrl]) {
            prefetchComponent(prefetchMap[prefetchUrl])
          }
          observer.unobserve(entry.target)
        }
      })
    })

    document.querySelectorAll('[data-prefetch]').forEach(element => {
      observer.observe(element)
    })
  }
}

/**
 * Service Worker registration for offline capability
 */
export const registerServiceWorker = () => {
  if ('serviceWorker' in navigator && import.meta.env.PROD) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration)

          // Update service worker when new version is available
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New version available, show update notification
                if (window.confirm('New version available. Reload to update?')) {
                  window.location.reload()
                }
              }
            })
          })
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError)
        })
    })
  }
}

/**
 * Progressive Web App manifest
 */
export const getPWAManifest = () => {
  return {
    "name": "Fusion System Administrator",
    "short_name": "Fusion Admin",
    "description": "Enterprise system administration platform",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#228BE6",
    "icons": [
      {
        "src": "/icon-192.png",
        "sizes": "192x192",
        "type": "image/png"
      },
      {
        "src": "/icon-512.png",
        "sizes": "512x512",
        "type": "image/png"
      }
    ]
  }
}