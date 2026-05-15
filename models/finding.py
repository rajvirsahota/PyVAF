from models.database import db

class Finding(db.Model):
    __tablename__ = 'findings'

    id          = db.Column(db.Integer, primary_key=True)
    scan_id     = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    severity    = db.Column(db.String(20), default='Info')
    # Critical / High / Medium / Low / Info
    port        = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    remediation = db.Column(db.Text, nullable=True)
    cvss_score  = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id':          self.id,
            'scan_id':     self.scan_id,
            'title':       self.title,
            'severity':    self.severity,
            'port':        self.port,
            'description': self.description,
            'remediation': self.remediation,
            'cvss_score':  self.cvss_score,
        }