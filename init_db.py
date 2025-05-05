"""
Database initialization script for DonationConnect.
This script creates all necessary database tables.
"""
from app import app, db
from models import User, Donation

def init_db():
    """Initialize the database by creating all tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
