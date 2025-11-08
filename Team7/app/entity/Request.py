from .. import db
from datetime import datetime, timedelta
from .UserAccount import UserAccount

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
            
    # -----------------------------
    # Shortlists
    # -----------------------------
    @classmethod
    def get_shortlist_count(cls, request_id, pin_id):
        """Entity for: As PIN, I want to see how many times my request has been shortlisted"""
        try:
            request = cls.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            return request.shortlist_count
        except Exception as e:
            return f"error:{str(e)}"

    # -----------------------------
    # Completed matches
    # -----------------------------
    @classmethod
    def search_completed_matches(cls, pin_id, search_title=None, search_date=None):
        """Entity for: As PIN, I want to search my completed matches by title and date"""
        try:
            query = cls.query.filter_by(
                pin_id=pin_id, 
                status='completed'
            )
        
            if search_title:
                print(search_title)
                search_pattern = f"%{search_title}%"
                query = query.filter(cls.title.ilike(search_pattern))
        
            if search_date:
                from datetime import timedelta
                query = query.filter(cls.updated_at >= search_date)
                query = query.filter(cls.updated_at < search_date + timedelta(days=1))
        
            results = query.order_by(cls.created_at.desc()).all()
            return results
        
        except Exception as e:
            return f"error:{str(e)}"
            

    @classmethod
    def get_completed_matches_history(cls, pin_id):
        """Entity for: As PIN, I want to view the history of my completed matches"""
        try:
            return cls.query.filter_by(
                pin_id=pin_id, 
                status='completed'
            ).order_by(cls.created_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"
            
            
    # -----------------------------
    # Create & Update
    # -----------------------------
    @classmethod
    def create_pin_request(cls, pin_id, title, description, category, urgency, location, preferred_date):
        """Entity: As PIN, i want to create requests"""
        try:
            request = cls(
                pin_id=pin_id, title=title, description=description,
                category=category, urgency=urgency, location=location,
                preferred_date=preferred_date
            )
            db.session.add(request)
            db.session.commit()
            return "success"  
        except Exception as e:
            return f"error:{str(e)}"

    @classmethod
    def get_active_requests(cls, pin_id):
        """Entity for: As PIN, I want to view my active requests"""
        try:
            requests = cls.query.filter_by(pin_id=pin_id).filter(
                cls.status.notin_(['completed', 'suspended'])
            ).all()
            return requests  # Return list of requests
        except Exception as e:
            return f"error:{str(e)}"  # Return error string

	
    @classmethod
    def suspend_pin_request(cls, request_id, pin_id):
        """Entity for: As PIN, I want to suspend my requests"""
        try:
            request = cls.query.filter_by(id=request_id, pin_id=pin_id).first()
            request.status = 'suspended'
            db.session.commit()
            return "success"  
        except Exception as e:
            return f"error:{str(e)}"

    @classmethod
    def update_pin_request(cls, request_id, pin_id, **update_data):
        """Entity: Update active request"""
        try:
            request = cls.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            # Only allow updates to ACTIVE requests
            if request.status not in ['pending', 'approved', 'in_progress']:
                return "can_only_update_active"
            
            allowed_fields = ['title', 'description', 'category', 'urgency', 'location', 'preferred_date']
            
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    setattr(request, field, value)
            
            request.updated_at = datetime.utcnow()
            db.session.commit()
            return "success"
            
        except Exception as e:
            db.session.rollback()
            return f"error:{str(e)}"

    # -----------------------------
    # Read (active / history / search)
    # -----------------------------
    @classmethod
    def get_pin_request_history(cls, pin_id):
        """Entity for: As PIN, I want to view my request history"""
        try:
            requests = cls.query.filter_by(pin_id=pin_id).filter(
                cls.status.in_(['completed', 'suspended'])
            ).order_by(cls.created_at.desc()).all()
            return requests  # Return request objects 
        except Exception as e:
            return f"error:{str(e)}"  # Return error string

    @classmethod
    def search_pin_requests(cls, pin_id, search_term):
        """Entity for: As PIN, I want to search my requests by title"""
        try:
            search_pattern = f"%{search_term}%"
            requests = cls.query.filter_by(pin_id=pin_id).filter(
                cls.title.ilike(search_pattern)  
            ).order_by(cls.created_at.desc()).all()
            return requests  # Return request objects 
        except Exception as e:
            return f"error:{str(e)}"  # Return error string

    @classmethod
    def get_request_for_display(cls, request_id, pin_id):
        """Entity for: As PIN, I want to update my ACTIVE requests - Get request data for display"""
        try:
            request = cls.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            # Only allow viewing ACTIVE requests for editing
            if request.status not in ['pending', 'approved', 'in_progress']:
                return "can_only_edit_active"
                
            return request
        except Exception as e:
            return f"error:{str(e)}"

      
class PINRequestView(db.Model):
    __tablename__ = 'pin_request_views'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    csr_company_id = db.Column(db.Integer, nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    request = db.relationship('Request', backref=db.backref('pin_views', lazy=True))

    @classmethod
    def track_view(cls, request_id, csr_company_id):
        """Track when a CSR views a request"""
        try:
            # Check if this CSR has already viewed this request
            existing_view = cls.query.filter_by(
                request_id=request_id,
                csr_company_id=csr_company_id
            ).first()
            
            if not existing_view:
                # Create new view record
                view = cls(
                    request_id=request_id,
                    csr_company_id=csr_company_id,
                    viewed_at=datetime.utcnow()
                )
                db.session.add(view)
                
                # Increment view count on request
                request = Request.query.get(request_id)
                if request:
                    request.view_count += 1
                
                db.session.commit()
                return "success"
            return "already_viewed"
        except Exception as e:
            db.session.rollback()
            return f"error:{str(e)}"

    @classmethod
    def get_view_count(cls, request_id, pin_id):
        """Get the view count for a specific request"""
        try:
            request = Request.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            return request.view_count
        except Exception as e:
            return f"error:{str(e)}"
