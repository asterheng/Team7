# app/entity/SessionUser.py
from flask import session
from ..entity.UserAccount import UserAccount  # ✅ correct import

class SessionUser:
    """Encapsulates session and authentication logic."""

    @staticmethod
    def login(email: str, password: str):
        """Authenticate credentials and, if valid, start a session."""
        res = {"ok": False, "errors": [], "user": None}

        email = (email or "").strip().lower()
        password = (password or "").strip()

        # Find user
        user = UserAccount.query.filter_by(email=email).first()
        if not user:
            res["errors"].append("No account found for that email.")
            return res

        if getattr(user, "is_suspended", False):
            res["errors"].append("Account is suspended.")
            return res

        if user.password != password:
            res["errors"].append("Incorrect password.")
            return res

        # ✅ Success — store session immediately
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        session["profile_name"] = getattr(user.profile, "name", None)

        res["ok"] = True
        res["user"] = user
        return res

    @staticmethod
    def is_logged_in():
        return bool(session.get("user_id"))

    @staticmethod
    def is_admin():
        return session.get("profile_name", "").lower() == "admin"
