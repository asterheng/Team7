from werkzeug.security import check_password_hash

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

from .control.UserController import CreateUserController, ListUserController, UpdateUserController, UserSearchController
from .control.SessionController import SessionController
from .entity.SessionUser import SessionUser
from .control.ProfileController import  CreateProfileController, ListProfileController, UpdateProfileController, ProfileSearchController
from .repositories import UserProfileRepository, UserRepository

# -----------------------------------------------------------------------------
# Auth guard
# -----------------------------------------------------------------------------
def login_required(view_func):
    """Decorator to protect routes that require a logged-in user."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("You must log in to access this page.", "error")
            return redirect(url_for("boundary.login"))
        return view_func(*args, **kwargs)
    return wrapped_view

bp = Blueprint('boundary', __name__)

# -----------------------------------------------------------------------------
# Home → Login
# -----------------------------------------------------------------------------
@bp.route('/')
def home():
    return redirect(url_for('boundary.on_login'))

# -----------------------------------------------------------------------------
# Profiles (CREATE + LIST) - protected
# -----------------------------------------------------------------------------
@bp.route('/profiles/new', methods=['GET','POST'])
@login_required
def create_profile():
    if request.method == "POST":
        CreateProfileController().CreateUserProfile(
            request.form.get("name", ""),
            request.form.get("description", ""),
            1 if request.form.get("is_suspended") else 0
        )
        return redirect(url_for("boundary.create_profile"))  # flashes handled internally
    return render_template("create_profile.html")

@bp.route('/profiles')
@login_required
def list_profiles():
    q = (request.args.get('q') or '').strip()

    if q:
        res = ProfileSearchController().search(q)
    else:
        res = ListProfileController().list_profiles_all()

    if not res["ok"]:
        for e in res["errors"]:
            flash(e, "list_profiles:err")
        return render_template('list_profiles.html', profiles=[], q=q)

    return render_template('list_profiles.html', profiles=res["data"], q=q)

@bp.route("/profiles/<int:profile_id>/edit", methods=["GET", "POST"])
@login_required
def edit_profile(profile_id):
    ctrl = UpdateProfileController()
    profile = ctrl.get(profile_id)
    if not profile:
        flash("Profile not found.", "update_profile:err")
        return redirect(url_for("boundary.list_profiles"))

    if request.method == "POST":
        errors = []

        # --- inline validation here (as you prefer) ---
        name_n = (request.form.get("name", "") or "").strip()
        desc_n = request.form.get("description", "") or ""
        is_susp = 1 if request.form.get("is_suspended") else 0

        if not name_n:
            errors.append("Name is required.")

        if errors:
            for e in errors:
                flash(e, "update_profile:err")
            # Re-render with a 400 Bad Request status
            return render_template("update_profile.html", profile=profile["data"]), 400

        # call controller → entity handles duplicate-name check & commit
        res = ctrl.update(profile_id, name_n, desc_n, is_susp)

        if res["ok"]:
            flash("Profile updated successfully.", "list_profile:ok")
            return redirect(url_for("boundary.list_profiles"))
        else:
            for e in res["errors"]:
                flash(e, "update_profile:err")

    # GET or POST with errors
    return render_template("update_profile.html", profile=profile["data"])

# -----------------------------------------------------------------------------
# Users (CREATE + LIST) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/new', methods=['GET','POST'])
@login_required
def create_user():
    profiles = ListProfileController().list_profiles_all()
    if request.method == 'POST':
        ctrl = CreateUserController()
        ctrl.CreateUserAC(
            request.form.get('name', ''),
            request.form.get('email', '').strip().lower(),
            request.form.get('password', ''),
            request.form.get('profile_id', '0'),
            1 if request.form.get('is_suspended') else 0
        )
        return redirect(url_for('boundary.create_user'))  # refresh after post
    return render_template('create_user.html', profiles=profiles["data"])

@bp.route('/users')
@login_required
def list_users():
    q = (request.args.get('q') or '').strip()
    page = request.args.get('page', type=int)  # pass None to disable pagination
    per_page = 20

    if q:
        res = UserSearchController().search(q, page=page, per_page=per_page)
    else:
        res = ListUserController().list_all_users(page=page, per_page=per_page)

    if not res["ok"]:
        for e in res["errors"]:
            flash(e, "list_users:err")
        return render_template('list_users.html', rows=[], q=q, pagination=None)

    return render_template(
        'list_users.html',
        rows=res["data"],                  # list[(UserAccount, UserProfile)]
        q=q,
        pagination=res.get("pagination")   # dict or None
    )

@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    ctrl = UpdateUserController()
    user = ctrl.get(user_id)
    if not user:
        flash("User not found.", "update_user:err")
        return redirect(url_for("boundary.list_users"))

    profiles = ListProfileController().list_profiles_all()

    if request.method == "POST":
        errors = []

        # --- inline validation in routes.py ---
        name_n  = (request.form.get("name", "")  or "").strip()
        email_n = (request.form.get("email", "") or "").strip().lower()

        if not name_n:
            errors.append("Name is required.")
        if not email_n:
            errors.append("Email is required.")

        if errors:
            for e in errors:
                flash(e, "update_user:err")
            return render_template("update_user.html", user=user, profiles=profiles["data"]), 400

        # --- call controller with normalized values ---
        res = ctrl.update(
            user_id=user_id,
            name=name_n,
            email=email_n,
            password=request.form.get("password") or None,                 # blank -> keep current password
            profile_id=request.form.get("profile_id", "0"),
            is_suspended=1 if request.form.get("is_suspended") else 0
        )

        if res["ok"]:
            flash("User updated successfully.", "list_user:ok")
            return redirect(url_for("boundary.list_users"))
        else:
            for e in res["errors"]:
                flash(e, "update_user:err")

    # GET (or POST with errors) -> render form
    return render_template("update_user.html", user=user, profiles=profiles["data"])


# -----------------------------------------------------------------------------
# Session (LOGIN + LOGOUT)
# -----------------------------------------------------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def on_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
            
        # --- Step 1: Basic validation before hitting controller ---
        if not email or not password:
            if not email:
                flash("Email is required.", "error")
            if not password:
                flash("Password is required.", "error")
            # Re-render login form with entered email preserved
            return render_template('LoginForm.html', email=email), 400

        # --- Step 2: Business logic through controller ---
        ctrl = SessionController()
        res = ctrl.login(email, password)

        # --- Step 3: Handle errors ---
        if not res["ok"]:
            for e in res["errors"]:
                flash(e, "error")
            return render_template('LoginForm.html', email=email), res.get("status_code", 400)

        # --- Step 4: Redirect based on role ---
        flash("Signed in successfully.", "ok") # testing
        if SessionUser.is_admin():
            return redirect(url_for('boundary.list_users')) # testing
        else:
            return redirect(url_for('boundary.home'))  # redirect to user dashboard

    # --- Step 5: Initial GET request ---
    return render_template('LoginForm.html')

@bp.route("/logout", methods=["POST"])
@login_required
def click_logout():
    """Log the user out by clearing the session directly."""
    session.clear()
    flash("Signed out successfully.", "ok")
    return redirect(url_for("boundary.on_login"))
