from ..repositories import UserRepository
from ..entity.UserAccount import UserAccount
from werkzeug.security import check_password_hash
from flask import session, flash, redirect, url_for

class AuthController:
    def __init__(self):
        self.repo = UserRepository()

    def CreateUserAC(self, name: str, email: str, password: str, profile_id: int, is_suspended: int):
        result = {"ok": False, "errors": [], "user_id": None}

        # normalize
        email = (email or "").strip().lower()
        name = (name or "").strip()

        # validation
        if not name:
            result["errors"].append("Name is required.")
        if not email:
            result["errors"].append("Email is required.")
        if not password:
            result["errors"].append("Password is required.")
        if result["errors"]:
            return result

        # prevent duplicate before insert
        if self.repo.find_by_email(email):
            result["errors"].append("A user with this email already exists.")
            return result

        # create entity and insert
        user = UserAccount.CreateUserAC(name, email, password, profile_id, is_suspended)
        try:
            result["user_id"] = self.repo.create(user)
            result["ok"] = True
        except Exception as e:
            # IntegrityError (race) or other DB errors land here; message nicely
            msg = str(e)
            if "UNIQUE" in msg and "users.email" in msg:
                result["errors"].append("A user with this email already exists.")
            else:
                result["errors"].append("Database error: " + msg)
        return result
        
    def login(self, email: str, password: str):
        """
        Validate credentials. Returns:
        {
          "ok": bool,
          "errors": [str, ...],
          "user": UserAccount | None,
          "profile_name": str | None,
          "status_code": int   # helpful for the route
        }
        """
        result = {"ok": False, "errors": [], "user": None, "profile_name": None, "status_code": 200}

        email = (email or "").strip().lower()
        password = password or ""

        if not email:
            result["errors"].append("Email is required.")
        if not password:
            result["errors"].append("Password is required.")
        if result["errors"]:
            result["status_code"] = 400
            return result

        user = self.repo.find_by_email(email)
        if not user:
            result["errors"].append("No account found for that email.")
            result["status_code"] = 401
            return result

        if user.is_suspended:
            result["errors"].append("Account is suspended.")
            result["status_code"] = 403
            return result

        if not check_password_hash(user.password_hash, password):
            result["errors"].append("Incorrect password.")
            result["status_code"] = 401
            return result

        # success
        result["ok"] = True
        result["user"] = user
        # thanks to relationship, user.profile is available
        result["profile_name"] = (user.profile.name if getattr(user, "profile", None) else None)
        return result
        
    def logout(self):
        """Logs out the current user by clearing session data."""
        session.clear()
        flash('Signed out.', 'ok')
        return redirect(url_for('boundary.login'))
