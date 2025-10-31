# app/control/session_controller.py
from ..entity.SessionUser import SessionUser

class SessionController:
    def login(self, email: str, password: str):
        """Controller: Pure data passing"""
        user = SessionUser.authenticate_user(email, password)
        return {"ok": bool(user), "user": user}