import os
from app import create_app

# Use the FLASK_ENV environment variable if available, otherwise default to production.
app = create_app(os.getenv('FLASK_ENV', 'production'))
