"""
database.py

SQLite database service for persistent case storage.
Manages all database operations for investigations.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent / "investigations.db"


class Database:
    """SQLite database service for case persistence"""
    
    def __init__(self, db_file: str = str(DB_PATH)):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create cases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    filters TEXT,
                    status TEXT DEFAULT 'created',
                    scan_type TEXT,
                    light_scan_result TEXT,
                    deep_scan_result TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_file}")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
        finally:
            conn.close()
    
    def create_case(self, case_id: str, username: str, email: Optional[str] = None, 
                   phone: Optional[str] = None, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new investigation case"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            filters_json = json.dumps(filters or {})
            
            cursor.execute("""
                INSERT INTO cases (case_id, username, email, phone, filters, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'created', ?, ?)
            """, (case_id, username, email, phone, filters_json, now, now))
            
            conn.commit()
            logger.info(f"Case created: {case_id} for {username}")
            
            return self.get_case(case_id)
        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get a case by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            
            if row:
                case = dict(row)
                # Parse JSON fields
                case['filters'] = json.loads(case['filters']) if case['filters'] else {}
                case['light_scan_result'] = json.loads(case['light_scan_result']) if case['light_scan_result'] else None
                case['deep_scan_result'] = json.loads(case['deep_scan_result']) if case['deep_scan_result'] else None
                return case
            return None
        except Exception as e:
            logger.error(f"Error getting case: {str(e)}")
            return None
        finally:
            conn.close()
    
    def list_cases(self) -> List[Dict[str, Any]]:
        """List all cases"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cases ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            cases = []
            for row in rows:
                case = dict(row)
                case['filters'] = json.loads(case['filters']) if case['filters'] else {}
                case['light_scan_result'] = json.loads(case['light_scan_result']) if case['light_scan_result'] else None
                case['deep_scan_result'] = json.loads(case['deep_scan_result']) if case['deep_scan_result'] else None
                cases.append(case)
            
            return cases
        except Exception as e:
            logger.error(f"Error listing cases: {str(e)}")
            return []
        finally:
            conn.close()
    
    def update_case_status(self, case_id: str, status: str) -> bool:
        """Update case status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute("""
                UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?
            """, (status, now, case_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating case status: {str(e)}")
            return False
        finally:
            conn.close()
    
    def set_light_scan_result(self, case_id: str, result: Dict[str, Any]) -> bool:
        """Store light scan result"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            result_json = json.dumps(result)
            
            cursor.execute("""
                UPDATE cases SET light_scan_result = ?, status = ?, updated_at = ? 
                WHERE case_id = ?
            """, (result_json, 'light_complete', now, case_id))
            
            conn.commit()
            logger.info(f"Light scan result stored for case {case_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error storing light scan result: {str(e)}")
            return False
        finally:
            conn.close()
    
    def set_deep_scan_result(self, case_id: str, result: Dict[str, Any]) -> bool:
        """Store deep scan result"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            result_json = json.dumps(result)
            
            cursor.execute("""
                UPDATE cases SET deep_scan_result = ?, status = ?, updated_at = ? 
                WHERE case_id = ?
            """, (result_json, 'deep_complete', now, case_id))
            
            conn.commit()
            logger.info(f"Deep scan result stored for case {case_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error storing deep scan result: {str(e)}")
            return False
        finally:
            conn.close()
    
    def delete_case(self, case_id: str) -> bool:
        """Delete a case"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
            conn.commit()
            logger.info(f"Case deleted: {case_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting case: {str(e)}")
            return False
        finally:
            conn.close()


# Initialize database singleton
db = Database()
