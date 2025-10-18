from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

from .control.UserController import CreateUserController, ListUserController
from .control.SessionController import SessionController
from .entity.SessionUser import SessionUser
from .control.ProfileController import  CreateProfileController, ListProfileController
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
    return redirect(url_for('boundary.login'))

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
    ctrl = ListProfileController()
    profiles = ctrl.list_profiles_all()
    return render_template('list_profiles.html', profiles=profiles["data"])

# -----------------------------------------------------------------------------
# Users (CREATE + LIST) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/new', methods=['GET','POST'])
@login_required
def create_user():
    profiles = UserProfileRepository().all()
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
    return render_template('create_user.html', profiles=profiles)

@bp.route('/users')
@login_required
def list_users():
    ctrl = ListUserController()
    rows = ctrl.list_all_users()
    return render_template('list_users.html', rows=rows["data"])

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
