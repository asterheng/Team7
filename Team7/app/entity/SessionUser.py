# app/entity/SessionUser.py
from .. import db 
from ..entity.UserAccount import UserAccount  # ✅ correct import

class SessionUser:
    
    @staticmethod
    def authenticate_user(email: str, password: str):
        """Returns user data or None (if non existent)"""
        user = UserAccount.query.filter_by(email=email).first()
        
        if not user or user.is_suspended or user.password != password:
            return None  
            
        return user  
