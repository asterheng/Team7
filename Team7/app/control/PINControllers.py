from ..entity.Request import Request, PINRequestView 


class PINCreateRequestController:
    #Controller for: As PIN, I want to create assistance requests#
    
    def create_pin_request(self, request_data):
            request = Request.create_pin_request(**request_data)  
            return request
            
class PINViewRequestsController:
    #Controller for: As PIN, I want to view my active requests#
     def get_active_requests(self, pin_id):
        return Request.get_active_requests(pin_id)  

class PINSuspendRequestController:
    #Controller for: As PIN, I want to suspend my requests#
     def suspend_pin_request(self, request_id, pin_id):
        return Request.suspend_pin_request(request_id, pin_id)  

class PINViewHistoryController:
    #Controller for: As PIN, I want to view my request history#
    def get_request_history(self, pin_id):
       return Request.get_pin_request_history(pin_id) 

class PINSearchRequestsController:
    #Controller for: As PIN, I want to search my requests#
    def search_pin_requests(self, pin_id, search_term):
       return Request.search_pin_requests(pin_id, search_term)  

class PINUpdateRequestController:
    # Controller: As PIN, i want to update existing requests
    def get_request_for_display(self, request_id, pin_id):
        return Request.get_request_for_display(request_id, pin_id) 
    
    def update_request(self, request_id, pin_id, update_data):
        return Request.update_pin_request(request_id, pin_id, **update_data)  


class PINRequestViewCountController:
    #Controller for: As PIN, I want to see how many times my request has been viewed#
    
    def track_view(self, request_id, csr_company_id):
        return PINRequestView.track_view(request_id, csr_company_id) 
    
    def get_view_count(self, request_id, pin_id):
        return PINRequestView.get_view_count(request_id, pin_id)  


class PINRequestShortlistCountController:
    #Controller for: As PIN, I want to see how many times my request has been shortlisted#
    
    def get_shortlist_count(self, request_id, pin_id):
        return Request.get_shortlist_count(request_id, pin_id)  


class PINCompletedMatchesSearchController:
    """Controller for: As PIN, I want to search my completed matches by service type and date"""
    
    def search_completed_matches(self, pin_id, search_title=None, search_date=None):
        return Request.search_completed_matches(pin_id, search_title, search_date)  


class PINCompletedMatchesHistoryController:
    """Controller for: As PIN, I want to view the history of my completed matches"""
    
    def get_completed_matches_history(self, pin_id):
        return Request.get_completed_matches_history(pin_id)  # Changed to Request
