from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///osint.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Investigation(Base):
    __tablename__ = 'investigations'
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Finding(Base):
    __tablename__ = 'findings'
    id = Column(Integer, primary_key=True)
    investigation_id = Column(Integer)
    platform = Column(String(50))
    username = Column(String(100))
    profile_url = Column(String(300))
    data = Column(Text)
    found = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'platform': self.platform,
            'username': self.username,
            'profile_url': self.profile_url,
            'data': self.data,
            'found': bool(self.found),
            'scraped_at': self.scraped_at.strftime('%Y-%m-%d %H:%M:%S')
        }

def init_db():
    Base.metadata.create_all(engine)
    print("Database ready.")

if __name__ == '__main__':
    init_db()