# app/control/session_controller.py
from flask import flash, redirect, url_for
from werkzeug.security import check_password_hash
from ..repositories import UserRepository
from ..entity.SessionUser import SessionUser

class SessionController:
    def __init__(self, repo=None):
        # Default concrete repo if none provided (fixes the missing-arg error)
        self.repo = repo or UserRepository()

    def login(self, email: str, password: str):
        """
        Validate credentials. Returns:
        {
          "ok": bool,
          "errors": [str],
          "user": UserAccount | None,
          "profile_name": str | None,
          "status_code": int
        }
        (Does NOT redirect; caller decides where to go.)
        """
        res = {"ok": False, "errors": [], "user": None, "profile_name": None, "status_code": 200}

        email = (email or "").strip().lower()
        password = password or ""

        if not email:
            res["errors"].append("Email is required.")
        if not password:
            res["errors"].append("Password is required.")
        if res["errors"]:
            res["status_code"] = 400
            return res

        user = self.repo.find_by_email(email)
        if not user:
            res["errors"].append("No account found for that email.")
            res["status_code"] = 401
            return res

        if getattr(user, "is_suspended", False):
            res["errors"].append("Account is suspended.")
            res["status_code"] = 403
            return res

        if not check_password_hash(user.password_hash, password):
            res["errors"].append("Incorrect password.")
            res["status_code"] = 401
            return res

        # Success → set session via SessionUser
        SessionUser.login(user)

        res["ok"] = True
        res["user"] = user
        res["profile_name"] = (user.profile.name if getattr(user, "profile", None) else None)
        return res

    def logout(self):
        """Clear session and return a redirect response to login."""
        SessionUser.logout()
        flash("Signed out.", "ok")
        return redirect(url_for("boundary.login"))
