from .. import db
from datetime import datetime

class Request(db.Model):
    __tablename__ = 'requests'
    
    id = db.Column(db.Integer, primary_key=True)
    pin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    urgency = db.Column(db.String(50), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(50), default='pending')
    location = db.Column(db.String(200))
    preferred_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    shortlist_count = db.Column(db.Integer, default=0)
    
    # Relationship to UserAccount
    pin_user = db.relationship('UserAdmin', backref=db.backref('requests', lazy=True))
    
    def __init__(self, pin_id, title, description, category, urgency='medium', location=None, preferred_date=None):
        self.pin_id = pin_id
        self.title = title
        self.description = description
        self.category = category
        self.urgency = urgency
        self.location = location
        self.preferred_date = preferred_date
    
    def to_dict(self):
        return {
            'id': self.id,
            'pin_id': self.pin_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'urgency': self.urgency,
            'status': self.status,
            'location': self.location,
            'preferred_date': self.preferred_date.isoformat() if self.preferred_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'view_count': self.view_count,
            'shortlist_count': self.shortlist_count
        }
      
class PINRequestView(db.Model):
    __tablename__ = 'pin_request_views'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    csr_company_id = db.Column(db.Integer, nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    request = db.relationship('Request', backref=db.backref('pin_views', lazy=True))
