"""
Database models for the OSINT Investigation Platform
Defines all SQLAlchemy ORM models for investigations, findings, and entities
"""

from database import db
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class Investigation(db.Model):
    """Investigation case model"""
    __tablename__ = 'investigations'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    case_type = db.Column(db.String(50), nullable=False)  # 'username', 'email', 'phone'
    primary_entity = db.Column(db.String(255), nullable=False)
    scan_depth = db.Column(db.String(10), nullable=False)  # 'light' or 'deep'
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    
    risk_score = db.Column(db.Float, default=0.0)  # 0-100
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # JSON fields for storing structured data
    findings_data = db.Column(db.JSON, default={})
    graph_data = db.Column(db.JSON, default={})
    logs = db.Column(db.JSON, default=[])
    
    # Relationships
    entities = db.relationship('Entity', backref='investigation', cascade='all, delete-orphan')
    edges = db.relationship('NetworkEdge', backref='investigation', cascade='all, delete-orphan')
    findings = db.relationship('Finding', backref='investigation', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert investigation to dictionary"""
        return {
            'case_id': self.id,
            'case_type': self.case_type,
            'primary_entity': self.primary_entity,
            'scan_depth': self.scan_depth,
            'status': self.status,
            'risk_score': self.risk_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Entity(db.Model):
    """Entity model (username, email, phone, mention, keyword, etc.)"""
    __tablename__ = 'entities'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False)
    
    entity_type = db.Column(db.String(50), nullable=False)  # 'username', 'email', 'phone', 'mention', 'keyword', 'report'
    entity_value = db.Column(db.String(500), nullable=False)
    is_central = db.Column(db.Boolean, default=False)  # Is this the central node?
    
    platform = db.Column(db.String(100))  # For username entities
    profile_url = db.Column(db.String(500))
    verified = db.Column(db.Boolean, default=False)
    
    # Risk indicators
    spam_reported = db.Column(db.Boolean, default=False)
    dangerous = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)  # 0-1
    
    # Additional metadata
    entity_metadata = db.Column(db.JSON, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, include_metadata=True):
        """Convert entity to dictionary"""
        data = {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_value': self.entity_value,
            'is_central': self.is_central,
            'platform': self.platform,
            'profile_url': self.profile_url,
            'verified': self.verified,
            'spam_reported': self.spam_reported,
            'dangerous': self.dangerous,
            'confidence_score': self.confidence_score,
        }
        if include_metadata:
            data['metadata'] = self.entity_metadata
        return data


class NetworkEdge(db.Model):
    """Network graph edge model"""
    __tablename__ = 'network_edges'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False)
    
    source_entity_id = db.Column(db.String(36), db.ForeignKey('entities.id'), nullable=False)
    target_entity_id = db.Column(db.String(36), db.ForeignKey('entities.id'), nullable=False)
    
    edge_type = db.Column(db.String(50), nullable=False)  # MENTIONS, CONNECTED_TO, USES_EMAIL, USES_PHONE, POSTED_KEYWORD, REPORTED_AS, SIMILAR_USERNAME
    confidence_score = db.Column(db.Float, default=0.0)  # 0-1
    
    evidence = db.Column(db.Text)  # Description of how connection was discovered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    source_entity = db.relationship('Entity', foreign_keys=[source_entity_id])
    target_entity = db.relationship('Entity', foreign_keys=[target_entity_id])
    
    def to_dict(self):
        """Convert edge to dictionary"""
        return {
            'id': self.id,
            'source': self.source_entity_id,
            'target': self.target_entity_id,
            'type': self.edge_type,
            'confidence': self.confidence_score,
            'evidence': self.evidence,
        }


class Finding(db.Model):
    """Detailed finding model"""
    __tablename__ = 'findings'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False)
    
    finding_type = db.Column(db.String(50), nullable=False)  # 'platform', 'email', 'phone', 'mention', 'report'
    platform = db.Column(db.String(100))
    
    found = db.Column(db.Boolean, default=False)
    data = db.Column(db.JSON, default={})
    
    source = db.Column(db.String(255))  # Where was this found
    confidence = db.Column(db.Float, default=0.0)  # 0-1
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert finding to dictionary"""
        return {
            'id': self.id,
            'finding_type': self.finding_type,
            'platform': self.platform,
            'found': self.found,
            'data': self.data,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PhoneIntelligence(db.Model):
    """Phone number intelligence cache"""
    __tablename__ = 'phone_intelligence'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    
    country = db.Column(db.String(100))
    country_code = db.Column(db.String(5))
    region = db.Column(db.String(100))
    carrier = db.Column(db.String(100))
    timezone = db.Column(db.String(100))
    number_type = db.Column(db.String(50))  # MOBILE, FIXED_LINE, etc.
    
    valid = db.Column(db.Boolean, default=False)
    is_possible = db.Column(db.Boolean, default=False)
    
    social_presence = db.Column(db.JSON, default={})  # Platforms where this phone was found
    emails_found = db.Column(db.JSON, default=[])
    
    risk_score = db.Column(db.Float, default=0.0)  # 0-100
    confidence = db.Column(db.Float, default=0.0)  # 0-1
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'country': self.country,
            'country_code': self.country_code,
            'region': self.region,
            'carrier': self.carrier,
            'timezone': self.timezone,
            'number_type': self.number_type,
            'valid': self.valid,
            'is_possible': self.is_possible,
            'social_presence': self.social_presence,
            'emails_found': self.emails_found,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
        }


class Report(db.Model):
    """Generated reports"""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False)
    
    report_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'json', 'html'
    file_path = db.Column(db.String(500))
    file_url = db.Column(db.String(500))
    
    title = db.Column(db.String(255))
    summary = db.Column(db.Text)
    
    chain_of_custody = db.Column(db.JSON, default=[])  # Audit trail
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'report_type': self.report_type,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'title': self.title,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TaskLog(db.Model):
    """Background task execution logs"""
    __tablename__ = 'task_logs'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'))
    
    task_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    
    message = db.Column(db.Text)
    error = db.Column(db.Text)
    
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'task_name': self.task_name,
            'status': self.status,
            'message': self.message,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
