from werkzeug.security import check_password_hash

# === Boundary Layer (Flask views / forms) ===
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

from .control.AuthController import AuthController
from .control.ProfileController import ProfileController
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
    ok = None
    errors = []
    if request.method == 'POST':
        ctrl = ProfileController()
        # NOTE: Using your existing controller API name (CreateUserAC) as in your codebase.
        result = ctrl.CreateUserProfile(
            request.form.get('name',''),
            request.form.get('description',''),
            1 if request.form.get('is_suspended') else 0
        )
        if result['ok']:
            ok = f"Profile created with ID {result['profile_id']}"
            flash(ok, "ok")
            return redirect(url_for('boundary.create_profile'))
        else:
            errors = result['errors']
            for e in errors:
                flash(e, "err")
    return render_template('create_profile.html', ok=ok, errors=errors)

@bp.route('/profiles')
@login_required
def list_profiles():
    profiles = UserProfileRepository().all()
    return render_template('list_profiles.html', profiles=profiles)

# -----------------------------------------------------------------------------
# Users (CREATE + LIST) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/new', methods=['GET','POST'])
@login_required
def create_user():
    profiles = UserProfileRepository().all()
    ok = None
    errors = []
    if request.method == 'POST':
        ctrl = AuthController()
        result = ctrl.CreateUserAC(
            request.form.get('name',''),
            request.form.get('email','').strip().lower(),
            request.form.get('password',''),
            request.form.get('profile_id','0'),
            1 if request.form.get('is_suspended') else 0
        )
        if result['ok']:
            ok = f"User created successfully (ID {result['user_id']})."
            flash(ok, "ok")
            return redirect(url_for('boundary.create_user'))  # clears form
        else:
            errors = result['errors']
            for e in errors:
                flash(e, "err")
    return render_template('create_user.html', ok=ok, errors=errors, profiles=profiles)

@bp.route('/users')
@login_required
def list_users():
    rows = UserRepository().all_with_profiles()  # ensure ASC in repository if desired
    return render_template('list_users.html', rows=rows)

# -----------------------------------------------------------------------------
# Auth (LOGIN + LOGOUT)
# -----------------------------------------------------------------------------
@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','')
        password = request.form.get('password','')

        ctrl = AuthController()
        res = ctrl.login(email, password)

        if not res["ok"]:
            for e in res["errors"]:
                flash(e, "error")
            return render_template('login.html', email=email), res.get("status_code", 400)

        user = res["user"]
        profile_name = (res["profile_name"] or "").lower()

        # Success → set session
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['profile_name'] = res["profile_name"]

        flash('Signed in successfully.', 'ok')

        # Redirect based on role
        if profile_name == "admin":
            return redirect(url_for('boundary.list_users'))
        else:
            return redirect(url_for('boundary.home'))  # or a user dashboard

    # GET
    return render_template('login.html')

@bp.route('/logout', methods=['POST'])
def logout():
    ctrl = AuthController()
    return ctrl.logout()
