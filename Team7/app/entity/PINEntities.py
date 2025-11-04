from .. import db
from .UserAccount import UserAccount
from .Request import Request, PINRequestView
from datetime import datetime

class PINRequestService:
    """Entity for: As PIN, I want to see how many times my request has been viewed"""
    
    # -----------------------------
    # Views
    # -----------------------------
    @classmethod
    def track_view(cls, request_id, csr_company_id):
        """Track when a CSR views a request"""
        try:
            # Check if this CSR has already viewed this request
            existing_view = PINRequestView.query.filter_by(
                request_id=request_id,
                csr_company_id=csr_company_id
            ).first()
            
            if not existing_view:
                # Create new view record
                view = PINRequestView(
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

            
    # -----------------------------
    # Shortlists
    # -----------------------------
    """Entity for: As PIN, I want to see how many times my request has been shortlisted"""
    @classmethod
    def get_shortlist_count(cls, request_id, pin_id):
        try:
            request = Request.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            return request.shortlist_count
        except Exception as e:
            return f"error:{str(e)}"

    # -----------------------------
    # Completed matches
    # -----------------------------
    """Entity for: As PIN, I want to search my completed matches by service type and date"""
    @classmethod
    def search_completed_matches(cls, pin_id, search_category=None, search_date=None):
        try:
            query = Request.query.filter_by(
                pin_id=pin_id, 
                status='completed'
            )
            
            if search_category:
                query = query.filter(Request.category.ilike(f"%{search_category}%"))
            
            if search_date:
                query = query.filter(Request.preferred_date == search_date)
            
            return query.order_by(Request.created_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"
            

    """Entity for: As PIN, I want to view the history of my completed matches"""
    @classmethod
    def get_completed_matches_history(cls, pin_id):
        try:
            return Request.query.filter_by(
                pin_id=pin_id, 
                status='completed'
            ).order_by(Request.created_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"
            
            
    # -----------------------------
    # Create & Update
    # -----------------------------
    #Entity: As PIN, i want to create requests
    @classmethod
    def create_pin_request(cls, pin_id, title, description, category, urgency, location, preferred_date):
        try:
            request = Request(
                pin_id=pin_id, title=title, description=description,
                category=category, urgency=urgency, location=location,
                preferred_date=preferred_date
            )
            db.session.add(request)
            db.session.commit()
            return "success"  
        except Exception as e:
            return f"error:{str(e)}"

    #Entity for: As PIN, I want to view my active requests#
    @classmethod
    def get_active_requests(cls, pin_id):
        try:
            requests = Request.query.filter_by(pin_id=pin_id).filter(
                Request.status.notin_(['completed', 'suspended'])
            ).all()
            return requests  # Return list of requests
        except Exception as e:
            return f"error:{str(e)}"  # Return error string

	
    #Entity for: As PIN, I want to suspend my requests#
    @classmethod
    def suspend_pin_request(cls, request_id, pin_id):
        try:
            request = Request.query.filter_by(id=request_id, pin_id=pin_id).first()
            request.status = 'suspended'
            db.session.commit()
            return "success"  
        except Exception as e:
            return f"error:{str(e)}"

    @classmethod
    def update_pin_request(cls, request_id, pin_id, **update_data):
        #Entity: Update active request
        try:
            request = Request.query.filter_by(id=request_id, pin_id=pin_id).first()
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
    #Entity for: As PIN, I want to view my request history#
    
    @classmethod
    def get_pin_request_history(cls, pin_id):
        try:
            requests = Request.query.filter_by(pin_id=pin_id).filter(
                Request.status.in_(['completed', 'suspended'])
            ).order_by(Request.created_at.desc()).all()
            return requests  # Return request objects 
        except Exception as e:
            return f"error:{str(e)}"  # Return error string

    #Entity for: As PIN, I want to search my requests#
    @classmethod
    def search_pin_requests(cls, pin_id, search_term):
        """search requests by title """
        try:
            search_pattern = f"%{search_term}%"
            requests = Request.query.filter_by(pin_id=pin_id).filter(
                Request.title.ilike(search_pattern)  
            ).order_by(Request.created_at.desc()).all()
            return requests  # Return request objects 
        except Exception as e:
            return f"error:{str(e)}"  # Return error string



    # Entity for: As PIN, I want to update my ACTIVE requests
    @classmethod
    def get_request_for_display(cls, request_id, pin_id):
       #Get request data for display
        try:
            request = Request.query.filter_by(id=request_id, pin_id=pin_id).first()
            if not request:
                return "not_found"
            
            # Only allow viewing ACTIVE requests for editing
            if request.status not in ['pending', 'approved', 'in_progress']:
                return "can_only_edit_active"
                
            return request
        except Exception as e:
            return f"error:{str(e)}"