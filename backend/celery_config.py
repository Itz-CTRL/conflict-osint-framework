"""Celery Configuration & Task Queue Setup
Provides background job processing with Redis.

Features:
- Persistent task queue
- Task scheduling
- Retry logic
- Task result tracking
- Distributed task processing
"""

import logging
from celery import Celery
from kombu import Exchange, Queue
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(__name__)

# Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# Configure Celery
celery_app.conf.update(
    # Broker settings
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    
    # Serialization
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,      # 30 min hard limit
    task_soft_time_limit=25 * 60,  # 25 min soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Beat Scheduler (for scheduled tasks)
    beat_scheduler='celery.beat:PersistentScheduler',
    
    # Queue settings
    default_queue='default',
    default_exchange='default',
    default_exchange_type='direct',
    default_routing_key='default',
    
    # Queues for different task types (if needed)
    task_queues=[
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('investigations', Exchange('investigations'), routing_key='investigation.*'),
        Queue('phone_lookups', Exchange('phone'), routing_key='phone.*'),
        Queue('reports', Exchange('reports'), routing_key='report.*'),
        Queue('emails', Exchange('emails'), routing_key='email.*'),
    ]
)

# Define periodic tasks (scheduled tasks)
celery_app.conf.beat_schedule = {
    'cleanup-old-investigations': {
        'task': 'tasks.cleanup_old_investigations',
        'schedule': timedelta(hours=24),  # Every 24 hours
        'args': (30,)  # Delete investigations older than 30 days
    },
    'health-check': {
        'task': 'tasks.health_check',
        'schedule': timedelta(minutes=5),  # Every 5 minutes
    }
}

# Task routes (optional: route tasks to specific workers)
# celery_app.conf.task_routes = {
#     'tasks.scan_investigation': {'queue': 'investigations'},
#     'tasks.lookup_phone': {'queue': 'phone_lookups'},
# }


# Define tasks
@celery_app.task(bind=True, max_retries=3)
def run_investigation_scan(self, case_id, username, scan_type='light'):
    """
    Run investigation scan in background
    
    Args:
        case_id: Investigation case ID
        username: Target username
        scan_type: 'light' or 'deep'
    
    Returns:
        dict with scan results
    """
    try:
        from database import db
        from models import Investigation
        from routes.investigation_routes import _light_scan, _deep_scan
        
        logger.info(f"[CELERY] Starting {scan_type} scan for case {case_id}")
        
        # Get investigation
        investigation = Investigation.query.get(case_id)
        if not investigation:
            logger.error(f"[CELERY] Investigation {case_id} not found")
            return {'error': 'Investigation not found'}
        
        # Update status
        investigation.status = 'running'
        investigation.started_at = datetime.utcnow()
        db.session.commit()
        
        # Run scan
        if scan_type == 'light':
            result = _light_scan(investigation)
        else:
            result = _deep_scan(investigation)
        
        # Update status
        investigation.status = 'completed'
        investigation.completed_at = datetime.utcnow()
        if result.get('data', {}).get('analysis'):
            investigation.risk_score = result['data']['analysis'].get('risk_score', 0)
        db.session.commit()
        
        logger.info(f"[CELERY] {scan_type} scan completed for case {case_id}")
        return result
        
    except Exception as e:
        logger.error(f"[CELERY] Scan error: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def harvest_emails_for_investigation(self, case_id, domain):
    """
    Harvest emails from domain in background
    
    Args:
        case_id: Investigation case ID
        domain: Domain to harvest from
    
    Returns:
        dict with harvested emails
    """
    try:
        from services.email_harvester import EmailHarvester
        
        logger.info(f"[CELERY] Harvesting emails from {domain}")
        
        harvester = EmailHarvester()
        result = harvester.harvest_from_domain(domain, intensive=True)
        
        logger.info(f"[CELERY] Harvested {result.get('count', 0)} emails from {domain}")
        return result
        
    except Exception as e:
        logger.error(f"[CELERY] Email harvesting error: {str(e)}")
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))


@celery_app.task
def phonequery_lookup(phone_number, country_code=None):
    """
    Perform phone lookup in background
    
    Args:
        phone_number: Phone number to lookup
        country_code: Optional country code
    
    Returns:
        dict with phone intelligence
    """
    try:
        from services.phone_intel import PhoneIntelligence
        
        logger.info(f"[CELERY] Phone lookup for {phone_number}")
        
        phone_service = PhoneIntelligence()
        result = phone_service.lookup(phone_number, country_code=country_code, scan_type='deep')
        
        return result
        
    except Exception as e:
        logger.error(f"[CELERY] Phone lookup error: {str(e)}")
        return {'error': str(e)}


@celery_app.task
def cleanup_old_investigations(days=30):
    """
    Clean up old investigations from database
    
    Args:
        days: Delete investigations older than N days
    
    Returns:
        dict with cleanup stats
    """
    try:
        from database import db
        from models import Investigation
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find and delete old investigations
        old_investigations = Investigation.query.filter(
            Investigation.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        logger.info(f"[CELERY] Deleted {old_investigations} old investigations")
        
        return {
            'deleted': old_investigations,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"[CELERY] Cleanup error: {str(e)}")
        return {'error': str(e)}


@celery_app.task
def health_check():
    """
    Periodic health check task
    
    Returns:
        dict with status
    """
    try:
        from database import db
        
        # Test database connection
        db.session.execute('SELECT 1')
        
        logger.debug("[CELERY] Health check passed")
        
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"[CELERY] Health check failed: {str(e)}")
        return {'status': 'unhealthy', 'error': str(e)}


def init_celery(app):
    """Initialize Celery with Flask app"""
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwds):
            with app.app_context():
                return self.run(*args, **kwds)
    
    celery_app.Task = ContextTask
    return celery_app
