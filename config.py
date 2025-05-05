import os

# Secret key for Flask session
SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_key')

# Database URI - handle both SQLite and PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Heroku uses 'postgres://' but SQLAlchemy requires 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# For Render deployment, use the mounted disk for SQLite
if os.path.exists('/data'):
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:////data/donations.db'
else:
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///donations.db'

# File upload settings
if os.path.exists('/data'):
    UPLOAD_FOLDER = '/data/uploads'
else:
    UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

# Flask configuration
DEBUG = True
