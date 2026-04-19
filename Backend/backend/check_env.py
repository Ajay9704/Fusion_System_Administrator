import os
from dotenv import load_dotenv

load_dotenv()

print(f"DB Name: {os.getenv('DB_NAME', 'Not set')}")
print(f"DB Host: {os.getenv('DB_HOST', 'Not set')}")
print(f"USE_POSTGRES: {os.getenv('USE_POSTGRES', 'Not set')}")
print(f"DEBUG: {os.getenv('DEBUG', 'Not set')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'Not set')}")
