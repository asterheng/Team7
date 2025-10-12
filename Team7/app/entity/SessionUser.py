from flask import session

class SessionUser:
    """Encapsulates session-related logic for the logged-in user."""

    @staticmethod
    def login(user):
        """Store user info into Flask session."""
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['profile_name'] = (
            user.profile.name if getattr(user, "profile", None) else None
        )

    @staticmethod
    def endSession():
        """Clear all session data."""
        session.clear()

    @staticmethod
    def is_logged_in():
        """Check if a user is logged in."""
        return bool(session.get('user_id'))

    @staticmethod
    def is_admin():
        """Check if the current user is an admin profile."""
        return session.get('profile_name', '').lower() == 'admin'

    @staticmethod
    def current_user_info():
        """Return current session data as dict."""
        return {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "profile": session.get("profile_name"),
        }
