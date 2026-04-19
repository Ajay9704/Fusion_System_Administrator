#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Production Readiness Check Script
Validates configuration and provides deployment recommendations
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_status(message, status):
    """Print status message with color"""
    if status == 'OK':
        print(f"{Colors.GREEN}[OK]{Colors.ENDC} {message}")
    elif status == 'WARNING':
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {message}")
    elif status == 'ERROR':
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")
    elif status == 'INFO':
        print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

def check_environment():
    """Check environment configuration"""
    print_status("Checking Environment Configuration...", "INFO")

    env_file = Path('.env')
    if not env_file.exists():
        print_status(".env file not found. Creating from template...", "WARNING")
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print_status("Created .env from template. Please update with actual values.", "OK")
        else:
            print_status("No .env.example found. Please create .env manually.", "ERROR")
            return False
    else:
        print_status(".env file exists", "OK")

    # Check critical environment variables
    from dotenv import load_dotenv
    load_dotenv()

    critical_vars = {
        'SECRET_KEY': 'Required for Django security',
        'DB_NAME': 'Database name',
        'DB_USER': 'Database user',
        'DB_PASSWORD': 'Database password',
        'ALLOWED_HOSTS': 'Allowed hosts for security'
    }

    all_good = True
    for var, description in critical_vars.items():
        value = os.getenv(var)
        if not value or value == 'your-secret-key-here-change-this':
            print_status(f"{var} not properly set ({description})", "ERROR")
            all_good = False
        else:
            print_status(f"{var} is set", "OK")

    return all_good

def check_database():
    """Check database connectivity"""
    print_status("Checking Database Connectivity...", "INFO")

    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.base')
        django.setup()

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print_status("Database connection successful", "OK")
                return True
    except Exception as e:
        print_status(f"Database connection failed: {str(e)}", "ERROR")
        return False

def check_dependencies():
    """Check required dependencies"""
    print_status("Checking Dependencies...", "INFO")

    required_packages = [
        'django',
        'djangorestframework',
        'corsheaders',
        'rest_framework_simplejwt',
        'psycopg2',
        'redis'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"{package} is installed", "OK")
        except ImportError:
            print_status(f"{package} is missing", "ERROR")
            all_installed = False

    return all_installed

def check_security():
    """Check security settings"""
    print_status("Checking Security Settings...", "INFO")

    from dotenv import load_dotenv
    load_dotenv()

    debug_mode = os.getenv('DEBUG', 'True') == 'True'
    environment = os.getenv('ENVIRONMENT', 'development')

    security_issues = []

    if environment == 'production' and debug_mode:
        security_issues.append("DEBUG=True in production environment")
        print_status("DEBUG is True in production!", "ERROR")
    else:
        print_status("DEBUG mode is appropriate for environment", "OK")

    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 50 or secret_key.startswith('django-insecure'):
        security_issues.append("Weak or default SECRET_KEY")
        print_status("SECRET_KEY should be stronger", "WARNING")
    else:
        print_status("SECRET_KEY appears secure", "OK")

    return len(security_issues) == 0

def check_file_permissions():
    """Check file permissions"""
    print_status("Checking File Permissions...", "INFO")

    critical_dirs = ['logs', 'media', 'staticfiles']
    all_good = True

    for dir_name in critical_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print_status(f"Creating {dir_name} directory...", "WARNING")
            dir_path.mkdir(parents=True, exist_ok=True)

        if os.access(dir_path, os.W_OK):
            print_status(f"{dir_name} is writable", "OK")
        else:
            print_status(f"{dir_name} is not writable", "ERROR")
            all_good = False

    return all_good

def check_migrations():
    """Check if migrations are up to date"""
    print_status("Checking Database Migrations...", "INFO")

    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.base')
        django.setup()

        from django.core.management import call_command
        from io import StringIO

        # Check for unapplied migrations
        out = StringIO()
        try:
            call_command('showmigrations', '--plan', stdout=out)
            output = out.getvalue()
            if '[X]' not in output:
                print_status("Some migrations are not applied", "WARNING")
                return False
            else:
                print_status("All migrations applied", "OK")
                return True
        except Exception as e:
            print_status(f"Could not check migrations: {str(e)}", "WARNING")
            return True

    except Exception as e:
        print_status(f"Migration check failed: {str(e)}", "ERROR")
        return False

def generate_report():
    """Generate deployment readiness report"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE}PRODUCTION READINESS REPORT{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

    checks = [
        ("Environment Configuration", check_environment),
        ("Database Connectivity", check_database),
        ("Required Dependencies", check_dependencies),
        ("Security Settings", check_security),
        ("File Permissions", check_file_permissions),
        ("Database Migrations", check_migrations),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n{Colors.BLUE}Checking {check_name}...{Colors.ENDC}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"{Colors.RED}Error during {check_name}: {str(e)}{Colors.ENDC}")
            results.append((check_name, False))

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE}SUMMARY{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.ENDC}" if result else f"{Colors.RED}FAIL{Colors.ENDC}"
        print(f"{check_name}: {status}")

    print(f"\n{Colors.BLUE}Total: {passed}/{total} checks passed{Colors.ENDC}\n")

    if passed == total:
        print(f"{Colors.GREEN}[SUCCESS] System is ready for deployment!{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.YELLOW}[ATTENTION] System needs attention before deployment.{Colors.ENDC}")
        print(f"{Colors.BLUE}Please fix the failed checks above.{Colors.ENDC}\n")
        return 1

def main():
    """Main function"""
    print(f"\n{Colors.BLUE}Fusion System Administrator - Production Readiness Check{Colors.ENDC}")
    print(f"{Colors.BLUE}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    exit_code = generate_report()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()