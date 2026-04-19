#!/usr/bin/env node
/**
 * Production Build Script
 * Automated build optimization and deployment preparation
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

console.log('🚀 Fusion System Administrator - Production Build')
console.log('='.repeat(60))

/**
 * Step 1: Environment validation
 */
function validateEnvironment() {
  console.log('\n📋 Step 1: Validating environment...')

  const requiredEnvVars = [
    'VITE_API_URL',
    'VITE_APP_NAME',
  ]

  const missingVars = requiredEnvVars.filter(varName => !process.env[varName])

  if (missingVars.length > 0) {
    console.warn('⚠️  Missing environment variables:', missingVars.join(', '))
    console.log('   Using default values for development...')
  } else {
    console.log('✅ Environment variables validated')
  }
}

/**
 * Step 2: Clean previous builds
 */
function cleanBuild() {
  console.log('\n🧹 Step 2: Cleaning previous builds...')

  const dirsToRemove = ['dist', 'node_modules/.vite']

  dirsToRemove.forEach(dir => {
    const fullPath = path.join(process.cwd(), dir)
    if (fs.existsSync(fullPath)) {
      fs.rmSync(fullPath, { recursive: true, force: true })
      console.log(`   Removed ${dir}`)
    }
  })

  console.log('✅ Build directories cleaned')
}

/**
 * Step 3: Install dependencies
 */
function installDependencies() {
  console.log('\n📦 Step 3: Installing dependencies...')

  try {
    execSync('npm ci', { stdio: 'inherit' })
    console.log('✅ Dependencies installed')
  } catch (error) {
    console.error('❌ Failed to install dependencies')
    process.exit(1)
  }
}

/**
 * Step 4: Run linter
 */
function runLinter() {
  console.log('\n🔍 Step 4: Running linter...')

  try {
    execSync('npm run lint', { stdio: 'inherit' })
    console.log('✅ Linting passed')
  } catch (error) {
    console.warn('⚠️  Linting issues found. Continuing anyway...')
  }
}

/**
 * Step 5: Build application
 */
function buildApplication() {
  console.log('\n🏗️  Step 5: Building application...')

  try {
    execSync('npm run build', { stdio: 'inherit' })
    console.log('✅ Application built successfully')
  } catch (error) {
    console.error('❌ Build failed')
    process.exit(1)
  }
}

/**
 * Step 6: Optimize build output
 */
function optimizeBuild() {
  console.log('\n⚡ Step 6: Optimizing build output...')

  const distPath = path.join(process.cwd(), 'dist')

  // Check build size
  const getDirectorySize = (dirPath) => {
    let size = 0
    const files = fs.readdirSync(dirPath)

    files.forEach(file => {
      const filePath = path.join(dirPath, file)
      const stats = fs.statSync(filePath)

      if (stats.isDirectory()) {
        size += getDirectorySize(filePath)
      } else {
        size += stats.size
      }
    })

    return size
  }

  const totalSize = getDirectorySize(distPath)
  const sizeInMB = (totalSize / (1024 * 1024)).toFixed(2)

  console.log(`   Total build size: ${sizeInMB} MB`)

  // Check individual bundle sizes
  const jsPath = path.join(distPath, 'assets', 'js')
  if (fs.existsSync(jsPath)) {
    const jsFiles = fs.readdirSync(jsPath)

    jsFiles.forEach(file => {
      const filePath = path.join(jsPath, file)
      const stats = fs.statSync(filePath)
      const fileSize = (stats.size / 1024).toFixed(2)

      if (stats.size > 200 * 1024) { // Warn if file > 200KB
        console.warn(`   ⚠️  Large file: ${file} (${fileSize} KB)`)
      }
    })
  }

  console.log('✅ Build optimization complete')
}

/**
 * Step 7: Generate build report
 */
function generateBuildReport() {
  console.log('\n📊 Step 7: Generating build report...')

  const reportPath = path.join(process.cwd(), 'dist', 'build-report.json')

  const report = {
    buildDate: new Date().toISOString(),
    buildVersion: process.env.npm_package_version || '1.0.0',
    buildEnvironment: process.env.NODE_ENV || 'production',
    buildSize: getBuildSize(),
    buildFiles: getBuildFiles(),
  }

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))
  console.log(`✅ Build report generated: ${reportPath}`)

  function getBuildSize() {
    const distPath = path.join(process.cwd(), 'dist')
    let totalSize = 0
    const fileCount = { js: 0, css: 0, other: 0 }

    function walkDir(dirPath) {
      const files = fs.readdirSync(dirPath)

      files.forEach(file => {
        const filePath = path.join(dirPath, file)
        const stats = fs.statSync(filePath)

        if (stats.isDirectory()) {
          walkDir(filePath)
        } else {
          totalSize += stats.size

          if (file.endsWith('.js')) fileCount.js++
          else if (file.endsWith('.css')) fileCount.css++
          else fileCount.other++
        }
      })
    }

    walkDir(distPath)

    return {
      totalBytes: totalSize,
      totalMB: (totalSize / (1024 * 1024)).toFixed(2),
      fileCount: fileCount
    }
  }

  function getBuildFiles() {
    const distPath = path.join(process.cwd(), 'dist')
    const files = []

    function walkDir(dirPath, relativePath = '') {
      const items = fs.readdirSync(dirPath)

      items.forEach(item => {
        const itemPath = path.join(dirPath, item)
        const stats = fs.statSync(itemPath)

        if (stats.isDirectory()) {
          walkDir(itemPath, path.join(relativePath, item))
        } else {
          files.push({
            path: path.join(relativePath, item).replace(/\\/g, '/'),
            size: stats.size,
            sizeKB: (stats.size / 1024).toFixed(2)
          })
        }
      })
    }

    walkDir(distPath)
    return files.sort((a, b) => b.size - a.size).slice(0, 10) // Top 10 largest files
  }
}

/**
 * Step 8: Generate sitemap
 */
function generateSitemap() {
  console.log('\n🗺️  Step 8: Generating sitemap...')

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${process.env.VITE_APP_URL || 'https://fusion.edu'}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`

  const sitemapPath = path.join(process.cwd(), 'dist', 'sitemap.xml')
  fs.writeFileSync(sitemapPath, sitemap)
  console.log('✅ Sitemap generated')
}

/**
 * Step 9: Generate robots.txt
 */
function generateRobotsTxt() {
  console.log('\n🤖 Step 9: Generating robots.txt...')

  const robotsTxt = `# Allow all crawlers
User-agent: *
Allow: /

# Disallow admin areas
Disallow: /admin/
Disallow: /api/

# Sitemap
Sitemap: ${process.env.VITE_APP_URL || 'https://fusion.edu'}/sitemap.xml
`

  const robotsPath = path.join(process.cwd(), 'dist', 'robots.txt')
  fs.writeFileSync(robotsPath, robotsTxt)
  console.log('✅ Robots.txt generated')
}

/**
 * Main build process
 */
function main() {
  try {
    validateEnvironment()
    cleanBuild()
    installDependencies()
    runLinter()
    buildApplication()
    optimizeBuild()
    generateBuildReport()
    generateSitemap()
    generateRobotsTxt()

    console.log('\n' + '='.repeat(60))
    console.log('✅ Production build completed successfully!')
    console.log('='.repeat(60))
    console.log('\n📦 Build artifacts are ready in the "dist" directory')
    console.log('🚀 Ready for deployment!')
    console.log('\nNext steps:')
    console.log('  1. Test the build: npm run preview')
    console.log('  2. Deploy to server: See DEPLOYMENT.md')
    console.log('')

  } catch (error) {
    console.error('\n❌ Build process failed:', error.message)
    process.exit(1)
  }
}

// Run the build process
main()