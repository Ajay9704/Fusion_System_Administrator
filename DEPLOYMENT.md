# 🚀 Fusion System Administrator - Deployment Guide

## 📋 Prerequisites

### Development Environment
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Git

### Production Environment
- All development requirements
- SSL certificate (Let's Encrypt or commercial)
- Domain name configured
- Production database (PostgreSQL on managed service)
- Redis instance (managed service recommended)
- SMTP server for emails

## 🔧 Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd Fusion_System_Administrator
```

### 2. Backend Setup
```bash
cd Backend/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 3. Frontend Setup
```bash
cd client

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start development server
npm run dev
```

## 🌐 Production Deployment

### Environment Selection
Set the `ENVIRONMENT` variable in `.env`:
- `development` - Local development
- `staging` - Pre-production testing
- `production` - Live production

### Backend Production Deployment

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql redis-server nginx

# Clone repository
git clone <repository-url> /var/www/fusion-system
cd /var/www/fusion-system/Backend/backend
```

#### 2. Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn whitenoise
```

#### 3. Environment Configuration
```bash
# Copy and edit production environment
cp .env.example .env
nano .env

# Set production values
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-secure-key>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

#### 4. Database Setup
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE fusion_prod;
CREATE USER fusion_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE fusion_prod TO fusion_user;
\q

# Run migrations
python manage.py migrate --settings=config.production
```

#### 5. Static Files
```bash
python manage.py collectstatic --settings=config.production --noinput
```

#### 6. Gunicorn Service
```bash
# Create systemd service
sudo nano /etc/systemd/system/fusion-backend.service
```

```ini
[Unit]
Description=Fusion Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/fusion-system/Backend/backend
Environment="PATH=/var/www/fusion-system/Backend/backend/venv/bin"
ExecStart=/var/www/fusion-system/Backend/backend/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/fusion-system/Backend/backend/gunicorn.sock \
          backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl start fusion-backend
sudo systemctl enable fusion-backend
```

### Frontend Production Deployment

#### 1. Build Frontend
```bash
cd client
npm run build
```

#### 2. Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/fusion-system
```

```nginx
# Upstream backend
upstream fusion_backend {
    server unix:/var/www/fusion-system/Backend/backend/gunicorn.sock;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        root /var/www/fusion-system/client/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://fusion_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/fusion-system/Backend/backend/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /var/www/fusion-system/Backend/backend/media/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fusion-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔐 Security Hardening

### 1. SSL Certificate
```bash
# Install Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. Firewall
```bash
# Configure UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 3. Database Security
```bash
# Create .pgpass file for secure database access
echo "localhost:5432:fusion_prod:fusion_user:password" > ~/.pgpass
chmod 600 ~/.pgpass
```

## 📊 Monitoring & Maintenance

### 1. Application Monitoring
```bash
# Check logs
tail -f /var/www/fusion-system/Backend/backend/logs/django.log

# System resources
htop
```

### 2. Database Maintenance
```bash
# Backup database
pg_dump fusion_prod | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore database
gunzip < backup_20250101.sql.gz | psql fusion_prod
```

### 3. Redis Maintenance
```bash
# Monitor Redis
redis-cli INFO

# Clear cache if needed
redis-cli FLUSHDB
```

## 🔄 Updates & Deployments

### 1. Update Application
```bash
cd /var/www/fusion-system
git pull origin main

# Backend updates
cd Backend/backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=config.production
python manage.py collectstatic --settings=config.production --noinput
sudo systemctl restart fusion-backend

# Frontend updates
cd ../../client
npm run build
sudo systemctl reload nginx
```

### 2. Rollback
```bash
# Git rollback
git checkout <previous-commit>

# Database rollback (if needed)
psql fusion_prod < backup_20250101.sql
```

## 🧪 Testing

### 1. Pre-deployment Checklist
- [ ] All tests pass
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] Database backups working
- [ ] Monitoring configured
- [ ] Error tracking (Sentry) configured

### 2. Smoke Tests
```bash
# Backend health check
curl https://your-domain.com/api/health/

# Frontend accessible
curl https://your-domain.com/

# API endpoints
curl -X POST https://your-domain.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

## 📱 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 2. Nginx 502 Errors
```bash
# Check backend service
sudo systemctl status fusion-backend

# Check Gunicorn logs
tail -f /var/www/fusion-system/Backend/backend/logs/gunicorn.log
```

#### 3. High Memory Usage
```bash
# Check process memory
ps aux --sort=-%mem | head

# Restart services if needed
sudo systemctl restart fusion-backend
sudo systemctl restart redis
```

## 📞 Support

For issues and questions:
- GitHub Issues: `<repository-url>/issues`
- Email: support@fusion.edu
- Documentation: `<repository-url>/wiki`

---

**Last Updated:** 2025-01-19
**Version:** 1.0.0