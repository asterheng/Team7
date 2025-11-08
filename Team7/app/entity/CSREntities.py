# app/entity/CSREntities.py
from .. import db
from .Request import Request, PINRequestView
from datetime import datetime, timedelta

class CSRService(db.Model):
    __tablename__ = 'csr_shortlist'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    csr_company_id = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    request = db.relationship('Request', backref=db.backref('shortlisted_by', lazy=True))
    # -----------------------------
    # Completed services (history & search)
    # -----------------------------
    
    #Entity for: As CSR Representative, I want to view the history of completed volunteer services#
    @classmethod
    def get_completed_services_history(cls, csr_company_id):
        try:
            # Get requests that were completed by this CSR
            query = Request.query.join(CSRService).filter(
                CSRService.csr_company_id == csr_company_id,
                Request.status == 'completed'
            )
            
            return query.order_by(Request.updated_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"

    #Entity for: As CSR Representative, I want to search for completed volunteer services by type and date#
    @classmethod
    def search_completed_services(cls, csr_company_id, search_title=None, search_date=None):
        try:
            query = Request.query.join(CSRService).filter(
                CSRService.csr_company_id == csr_company_id,
                Request.status == 'completed'
            )
            
            if search_title:
                query = query.filter(Request.title.ilike(f"%{search_title}%"))
            
            if search_date:
                from datetime import timedelta
                query = query.filter(Request.updated_at >= search_date)
                query = query.filter(Request.updated_at < search_date + timedelta(days=1))
            
            return query.order_by(Request.updated_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"

    # -----------------------------
    # Browse available requests
    # ----------------------------
    
    #Entity for: As CSR, I want to search for available service requests#
    @classmethod
    def search_available_requests(cls, search_term=None, category=None, urgency=None):
        try:
            query = Request.query.filter(Request.status.in_(['pending', 'approved']))
            
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    db.or_(
                        Request.title.ilike(search_pattern),
                        Request.description.ilike(search_pattern),
                        Request.category.ilike(search_pattern)
                    )
                )
            
            if category:
                query = query.filter(Request.category == category)
            
            if urgency:
                query = query.filter(Request.urgency == urgency)
            
            return query.order_by(Request.created_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"


    # -----------------------------
    # Request details
    # -----------------------------
    
    #Entity for: As CSR, I want to view detailed information about a service request#
    @classmethod
    def get_request_details(cls, request_id):
        try:
            request = Request.query.get(request_id)
            if not request:
                return "not_found"
            return request
        except Exception as e:
            return f"error:{str(e)}"


    # -----------------------------
    # Shortlist (add/search/view/remove)
    # -----------------------------
    
    #Entity for: As CSR, I want to save interesting requests to a shortlist#
    @classmethod
    def add_to_shortlist(cls, request_id, csr_company_id):
        try:
            existing = CSRService.query.filter_by(
                request_id=request_id, 
                csr_company_id=csr_company_id
            ).first()
            
            if existing:
                return "already_shortlisted"
            
            # ✅ NEW: Get the request and increment shortlist_count
            request = Request.query.get(request_id)
            if not request:
                return "request_not_found"
            
            shortlist = CSRService(
                request_id=request_id,
                csr_company_id=csr_company_id,
                added_at=datetime.utcnow()
            )
            db.session.add(shortlist)
            
            # ✅ NEW: Increment the shortlist count
            request.shortlist_count += 1
            db.session.commit()
            return "success"
        except Exception as e:
            db.session.rollback()
            return f"error:{str(e)}"

    # User Story 4: Search shortlisted requests
    #Entity for: As CSR, I want to search through my shortlisted requests#
    @classmethod
    def search_shortlisted_requests(cls, csr_company_id, search_term=None):
        try:
            query = Request.query.join(CSRService).filter(
                CSRService.csr_company_id == csr_company_id
            )
            
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    db.or_(
                        Request.title.ilike(search_pattern),
                        Request.description.ilike(search_pattern)
                    )
                )
            
            return query.order_by(CSRService.added_at.desc()).all()
        except Exception as e:
            return f"error:{str(e)}"

    # User Story 5: View shortlisted request details
    #Entity for: As CSR, I want to view the details of my shortlisted requests#
    @classmethod
    def get_shortlisted_request_details(cls, request_id, csr_company_id):
        try:
            # Verify the request is in the user's shortlist
            shortlisted = CSRService.query.filter_by(
                request_id=request_id,
                csr_company_id=csr_company_id
            ).first()
            
            if not shortlisted:
                return "not_shortlisted"
            
            request = Request.query.get(request_id)
            if not request:
                return "not_found"
                
            return request
        except Exception as e:
            return f"error:{str(e)}"


    #Entity for removing from shortlist#
    @classmethod
    def remove_from_shortlist(cls, request_id, csr_company_id):
        try:
            shortlist = CSRService.query.filter_by(   
                request_id=request_id, 
                csr_company_id=csr_company_id
            ).first()
            
            if not shortlist:
                return "not_found"
            
  
            request = Request.query.get(request_id)
            if request and request.shortlist_count > 0:
                request.shortlist_count -= 1
            
            db.session.delete(shortlist)
            db.session.commit()
            return "success"
        except Exception as e:
            db.session.rollback()
            return f"error:{str(e)}"


