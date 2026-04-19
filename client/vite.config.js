import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Production-optimized Vite configuration
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [react()],

    // Path aliases for cleaner imports
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@pages': path.resolve(__dirname, './src/pages'),
        '@services': path.resolve(__dirname, './src/services'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@api': path.resolve(__dirname, './src/api'),
      }
    },

    // Development server configuration
    server: {
      port: 5173,
      host: true,
      open: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    },

    // Build optimizations for production
    build: {
      // Output directory
      outDir: 'dist',
      emptyOutDir: true,

      // Generate source maps for debugging (disable in production for better performance)
      sourcemap: !isProduction,

      // Code splitting optimizations
      rollupOptions: {
        output: {
          // Manual chunks for better caching
          manualChunks: {
            // Vendor chunk for React and major libraries
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],

            // UI library chunk
            'ui-vendor': ['@mantine/core', '@mantine/hooks', '@tabler/icons-react'],

            // API and services chunk
            'api-vendor': ['./src/services/base/ApiService', './src/services/api'],

            // Utility libraries
            'utils': ['axios'],
          },

          // Asset naming for cache busting
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
        }
      },

      // Chunk size warning limit (increase to avoid warnings)
      chunkSizeWarningLimit: 1000,

      // Minify settings
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: isProduction, // Remove console.logs in production
          drop_debugger: isProduction,
        },
      },

      // CSS code splitting
      cssCodeSplit: true,

      // Target modern browsers
      target: 'es2015',
    },

    // Dependencies optimization
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@mantine/core',
        '@mantine/hooks',
        'axios'
      ],
    },

    // Global constants
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
    },

    // Preview server for production builds
    preview: {
      port: 4173,
      host: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    }
  }
})
