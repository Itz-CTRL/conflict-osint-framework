"""
Task Manager for Background Job Processing
Handles Celery tasks and threaded job execution
"""

import logging
import threading
import queue
from datetime import datetime
from database import db
from models import Investigation, TaskLog
from services import AnalyserService, RiskEngine, GraphEngine
from utils import generate_entity_id

logger = logging.getLogger(__name__)


class TaskManager:
    """Background task manager using threading"""
    
    def __init__(self, max_workers=4):
        """
        Initialize task manager
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.active_tasks = {}
        self.workers = []
        self.running = False
    
    def start(self):
        """Start worker threads"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.max_workers} background workers")
    
    def stop(self):
        """Stop worker threads"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        logger.info("Background workers stopped")
    
    def submit_investigation(self, investigation_id, username, scan_depth='light'):
        """
        Submit investigation task to background queue
        
        Args:
            investigation_id: Investigation case ID
            username: Username to investigate
            scan_depth: 'light' or 'deep'
        """
        task = {
            'type': 'investigation',
            'investigation_id': investigation_id,
            'username': username,
            'scan_depth': scan_depth,
            'created_at': datetime.utcnow()
        }
        self.task_queue.put(task)
        logger.info(f"Submitted investigation task for {investigation_id}")
        return task
    
    def submit_phone_lookup(self, investigation_id, phone_number):
        """Submit phone lookup task"""
        task = {
            'type': 'phone_lookup',
            'investigation_id': investigation_id,
            'phone_number': phone_number,
            'created_at': datetime.utcnow()
        }
        self.task_queue.put(task)
        logger.info(f"Submitted phone lookup task for {investigation_id}")
        return task
    
    def submit_risk_scoring(self, investigation_id):
        """Submit risk scoring task"""
        task = {
            'type': 'risk_score',
            'investigation_id': investigation_id,
            'created_at': datetime.utcnow()
        }
        self.task_queue.put(task)
        logger.info(f"Submitted risk scoring task for {investigation_id}")
        return task
    
    def submit_graph_building(self, investigation_id):
        """Submit graph building task"""
        task = {
            'type': 'build_graph',
            'investigation_id': investigation_id,
            'created_at': datetime.utcnow()
        }
        self.task_queue.put(task)
        logger.info(f"Submitted graph building task for {investigation_id}")
        return task
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                self._execute_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
    
    def _execute_task(self, task):
        """Execute a task"""
        try:
            task_type = task.get('type')
            task_id = f"{task_type}_{task.get('investigation_id')}"
            
            self.active_tasks[task_id] = task
            
            if task_type == 'investigation':
                self._handle_investigation(task)
            elif task_type == 'phone_lookup':
                self._handle_phone_lookup(task)
            elif task_type == 'risk_score':
                self._handle_risk_score(task)
            elif task_type == 'build_graph':
                self._handle_graph_building(task)
            else:
                logger.warning(f"Unknown task type: {task_type}")
            
            del self.active_tasks[task_id]
        
        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            if 'investigation_id' in task:
                self._log_task_error(task['investigation_id'], task.get('type'), str(e))
    
    def _handle_investigation(self, task):
        """Handle investigation task"""
        investigation_id = task['investigation_id']
        username = task['username']
        scan_depth = task['scan_depth']
        
        logger.info(f"Executing investigation task for {investigation_id}")
        
        investigation = Investigation.query.get(investigation_id)
        if not investigation:
            logger.error(f"Investigation {investigation_id} not found")
            return
        
        try:
            # Log task start
            self._log_task(investigation_id, f"investigation_{scan_depth}", 'running', 
                          f"Starting {scan_depth} scan for {username}")
            
            # Run analysis
            analyser = AnalyserService(investigation_id)
            
            if scan_depth == 'light':
                results = analyser.light_scan(username)
            else:
                results = analyser.deep_scan(username)
            
            # Run risk scoring
            risk_engine = RiskEngine(investigation_id)
            risk_score = risk_engine.calculate_risk_score()
            
            # Build graph
            graph_engine = GraphEngine(investigation_id)
            graph_engine.add_central_node('username', username)
            
            # Update investigation
            investigation.findings_data = results
            investigation.risk_score = risk_score
            investigation.status = 'completed'
            investigation.completed_at = datetime.utcnow()
            db.session.commit()
            
            self._log_task(investigation_id, f"investigation_{scan_depth}", 'completed',
                          f"Scan completed. Risk Score: {risk_score}")
            
            logger.info(f"Investigation task for {investigation_id} completed successfully")
        
        except Exception as e:
            investigation.status = 'failed'
            db.session.commit()
            self._log_task(investigation_id, f"investigation_{scan_depth}", 'failed', str(e))
            logger.error(f"Investigation task failed: {str(e)}")
    
    def _handle_phone_lookup(self, task):
        """Handle phone lookup task"""
        investigation_id = task['investigation_id']
        phone_number = task['phone_number']
        
        logger.info(f"Executing phone lookup for {investigation_id}")
        
        try:
            from services import PhoneIntelService
            
            self._log_task(investigation_id, 'phone_lookup', 'running',
                          f"Looking up {phone_number}")
            
            phone_service = PhoneIntelService()
            result = phone_service.lookup_phone(phone_number)
            
            investigation = Investigation.query.get(investigation_id)
            investigation.findings_data = result
            investigation.status = 'completed'
            db.session.commit()
            
            self._log_task(investigation_id, 'phone_lookup', 'completed',
                          f"Phone lookup completed for {phone_number}")
            
            logger.info(f"Phone lookup for {investigation_id} completed")
        
        except Exception as e:
            self._log_task(investigation_id, 'phone_lookup', 'failed', str(e))
            logger.error(f"Phone lookup failed: {str(e)}")
    
    def _handle_risk_score(self, task):
        """Handle risk scoring task"""
        investigation_id = task['investigation_id']
        
        logger.info(f"Executing risk scoring for {investigation_id}")
        
        try:
            self._log_task(investigation_id, 'risk_score', 'running',
                          "Calculating risk score")
            
            risk_engine = RiskEngine(investigation_id)
            risk_score = risk_engine.calculate_risk_score()
            
            investigation = Investigation.query.get(investigation_id)
            investigation.risk_score = risk_score
            db.session.commit()
            
            self._log_task(investigation_id, 'risk_score', 'completed',
                          f"Risk score calculated: {risk_score}")
            
            logger.info(f"Risk scoring for {investigation_id} completed: {risk_score}")
        
        except Exception as e:
            self._log_task(investigation_id, 'risk_score', 'failed', str(e))
            logger.error(f"Risk scoring failed: {str(e)}")
    
    def _handle_graph_building(self, task):
        """Handle graph building task"""
        investigation_id = task['investigation_id']
        
        logger.info(f"Executing graph building for {investigation_id}")
        
        try:
            self._log_task(investigation_id, 'build_graph', 'running',
                          "Building network graph")
            
            graph_engine = GraphEngine(investigation_id)
            graph = graph_engine.build_graph_json()
            
            investigation = Investigation.query.get(investigation_id)
            investigation.graph_data = graph
            db.session.commit()
            
            self._log_task(investigation_id, 'build_graph', 'completed',
                          f"Graph built with {len(graph['nodes'])} nodes")
            
            logger.info(f"Graph building for {investigation_id} completed")
        
        except Exception as e:
            self._log_task(investigation_id, 'build_graph', 'failed', str(e))
            logger.error(f"Graph building failed: {str(e)}")
    
    def _log_task(self, investigation_id, task_name, status, message):
        """Log task execution"""
        try:
            task_log = TaskLog(
                id=generate_entity_id(),
                investigation_id=investigation_id,
                task_name=task_name,
                status=status,
                message=message,
                started_at=datetime.utcnow() if status == 'running' else None,
                completed_at=datetime.utcnow() if status in ['completed', 'failed'] else None
            )
            db.session.add(task_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging task: {str(e)}")
    
    def _log_task_error(self, investigation_id, task_type, error_msg):
        """Log task error"""
        try:
            investigation = Investigation.query.get(investigation_id)
            if investigation:
                investigation.status = 'failed'
                db.session.commit()
            
            self._log_task(investigation_id, task_type, 'failed', error_msg)
        except Exception as e:
            logger.error(f"Error logging task error: {str(e)}")
    
    def get_task_status(self, investigation_id):
        """Get status of investigation task"""
        investigation = Investigation.query.get(investigation_id)
        if not investigation:
            return None
        
        return {
            'investigation_id': investigation_id,
            'status': investigation.status,
            'risk_score': investigation.risk_score,
            'findings_count': len(investigation.findings) if investigation.findings else 0,
            'created_at': investigation.created_at,
            'started_at': investigation.started_at,
            'completed_at': investigation.completed_at
        }


# Global task manager instance
_task_manager = None


def get_task_manager():
    """Get or create task manager"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_workers=4)
        _task_manager.start()
    return _task_manager
