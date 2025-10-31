# 📦 File: app/control/ServiceCategoryController.py
from ..entity.ServiceCategory import ServiceCategory


class CreateServiceCategoryController:
    def CreateServiceCategory(self, name: str, description: str, is_suspended: int | bool):
        return ServiceCategory.CreateServiceCategory(name, description, is_suspended)

class ListServiceCategoryController:
    def ListServiceCategory(self, page=1, per_page=20):
        return ServiceCategory.ListServiceCategory(page=page, per_page=per_page)
           
class SearchServiceCategoryController:
    def SearchServiceCategory(self, term: str, page=1, per_page=20):
        return ServiceCategory.SearchServiceCategory(term, page=page, per_page=per_page)

class UpdateServiceCategoryController:
    def UpdateServiceCategory(self, category_id: int, name: str, description: str, is_suspended: int | bool):
        return ServiceCategory.UpdateServiceCategory(category_id, name, description, is_suspended)
        
    def get(self, category_id: int):
        return ServiceCategory.get_by_id(category_id)

class SuspendedServiceCategoryController:
    def SuspendedServiceCategory(self, category_id: int, is_suspended: int | bool) -> str:
        return ServiceCategory.SuspendedServiceCategory(category_id, is_suspended)