# app/control/session_controller.py
from ..entity.SessionUser import SessionUser

class SessionController:
    def login(self, email: str, password: str):
        """Authenticate and start a session (single step)."""
        return SessionUser.login(email, password)
