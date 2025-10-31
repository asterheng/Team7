# app/control/CSRControllers.py
from ..entity.CSREntities import (CSRService)

from ..control.PINControllers import PINRequestViewCountController

class CSRViewCompletedServicesController:
    #Controller for: As CSR Representative, I want to view the history of completed volunteer services#    
    def get_completed_services_history(self, csr_company_id):
        return CSRService.get_completed_services_history(csr_company_id)


class CSRSearchCompletedServicesController:
   #Controller for: As CSR Representative, I want to search for completed volunteer services by type and date#    
    def search_completed_services(self, csr_company_id, search_category=None, search_date=None):
        return CSRService.search_completed_services(csr_company_id, search_category, search_date)


class CSRSearchAvailableRequestsController:
    #Controller for: As CSR, I want to search for available service requests#    
    def search_available_requests(self, search_term=None, category=None, urgency=None):
        return CSRService.search_available_requests(search_term, category, urgency)


class CSRViewRequestDetailsController:
    #Controller for: As CSR, I want to view detailed information about a service request#
    def get_request_details(self, request_id, csr_company_id=None):
        # First get the request details
        result = CSRService.get_request_details(request_id)
        

        if csr_company_id and not isinstance(result, str):
            tracking_ctrl = PINRequestViewCountController()
            tracking_ctrl.track_view(request_id, csr_company_id)
        
        return result

class CSRSaveToShortlistController:
    #Controller for: As CSR, I want to save interesting requests to a shortlist#
    
    def add_to_shortlist(self, request_id, csr_company_id):
        return CSRService.add_to_shortlist(request_id, csr_company_id)


class CSRSearchShortlistedRequestsController:
    #Controller for: As CSR, I want to search through my shortlisted requests#
    
    def search_shortlisted_requests(self, csr_company_id, search_term=None):
        return CSRService.search_shortlisted_requests(csr_company_id, search_term)


class CSRViewShortlistedRequestController:
   #Controller for: As CSR, I want to view the details of my shortlisted requests#
    
    def get_shortlisted_request_details(self, request_id, csr_company_id):
        return CSRService.get_shortlisted_request_details(request_id, csr_company_id)


class CSRRemoveFromShortlistController:
   #Controller for removing from shortlist#
    
    def remove_from_shortlist(self, request_id, csr_company_id):
        return CSRService.remove_from_shortlist(request_id, csr_company_id)
