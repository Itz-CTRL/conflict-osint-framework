"""
Database module for the OSINT Investigation Platform
Initializes SQLAlchemy ORM and database connection
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()


def init_db(app):
    """
    Initialize database with Flask application
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise


def get_db_session():
    """Get current database session"""
    return db.session


def close_db_session():
    """Close database session"""
    db.session.remove()

if __name__ == '__main__':
    init_db()