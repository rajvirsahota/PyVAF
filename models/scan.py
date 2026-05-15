from datetime import datetime
from models.database import db

class Scan(db.Model):
    __tablename__ = 'scans'

    id          = db.Column(db.Integer, primary_key=True)
    target      = db.Column(db.String(255), nullable=False)
    status      = db.Column(db.String(50), default='pending')
    # pending → running → complete → failed
    started_at  = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    modules     = db.Column(db.String(255), default='')

    findings    = db.relationship('Finding', backref='scan',
                                  lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'target':      self.target,
            'status':      self.status,
            'started_at':  str(self.started_at),
            'finished_at': str(self.finished_at) if self.finished_at else None,
            'modules':     self.modules.split(',') if self.modules else [],
        }