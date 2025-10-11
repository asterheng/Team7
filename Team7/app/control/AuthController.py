from ..repositories import UserRepository
from ..entity.UserAccount import UserAccount

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
