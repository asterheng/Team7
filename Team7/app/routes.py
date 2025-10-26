from werkzeug.security import check_password_hash

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime  

from .control.UserController import (
    CreateUserController, 
    ListUserController, 
    UpdateUserController, 
    UserSearchController, 
    SuspendedUserController, 
    LoginUserController
)
from .control.UserProfileController import  (
    CreateUserProfileController, 
    ListUserProfileController, 
    UpdateUserProfileController, 
    UserProfileSearchController, 
    SuspendedUserProfileController
)
from .control.ServiceCategoryController import (
    CreateServiceCategoryController,
    ListServiceCategoryController,
    UpdateServiceCategoryController,
    SearchServiceCategoryController,
    SuspendedServiceCategoryController
)   

from .control.PINControllers import (
    PINCreateRequestController, 
    PINViewRequestsController, PINSuspendRequestController,
    PINViewHistoryController, PINSearchRequestsController
)

# -----------------------------------------------------------------------------
# Auth guard
# -----------------------------------------------------------------------------
def login_required(view_func):
    """Decorator to protect routes that require a logged-in user."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("You must log in to access this page.", "error")
            return redirect(url_for("boundary.on_login"))
        return view_func(*args, **kwargs)
    return wrapped_view

bp = Blueprint('boundary', __name__)

# -----------------------------------------------------------------------------
# Session (LOGIN)
# -----------------------------------------------------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def on_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not email or not password:
            if not email:
                flash("Email is required.", "error")
            if not password:
                flash("Password is required.", "error")
            return render_template('LoginForm.html', email=email), 400

        ctrl = LoginUserController()
        res = ctrl.login(email, password)

        if not res["ok"]:
            for err in res["errors"]:
                flash(err, "error")
            return render_template('LoginForm.html', email=email), 400

        user = res["data"]
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        session["profile_name"] = user.profile.name

        profile_name = user.profile.name.lower()
        if profile_name == "admin":
            return redirect(url_for('boundary.list_users'))
        elif profile_name == "platform management":
            return redirect(url_for('boundary.list_service_categories'))
        elif profile_name == "pin":
            return redirect(url_for('boundary.pin_dashboard'))
        else:
            return redirect(url_for('boundary.home'))

    return render_template('LoginForm.html')


# -----------------------------------------------------------------------------
# Session (LOGOUT)
# -----------------------------------------------------------------------------
@bp.route("/logout", methods=["POST"])
@login_required
def click_logout():
    """Log the user out by clearing the session directly."""
    session.clear()
    flash("Signed out successfully.", "ok")
    return redirect(url_for("boundary.on_login"))


# -----------------------------------------------------------------------------
# Home → Login
# -----------------------------------------------------------------------------
@bp.route('/')
def home():
    return redirect(url_for('boundary.on_login'))
    
# -----------------------------------------------------------------------------
# Users (CREATE) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    profiles = ListUserProfileController().ListUserProfile()
    if request.method == "POST":
        ctrl = CreateUserController()
        status  = ctrl.CreateUserAC(
            request.form.get('name', '').strip(),
            request.form.get('email', '').strip().lower(),
            request.form.get('password', ''),
            request.form.get('profile_id', '0'),
            1 if request.form.get('is_suspended') else 0
        )

        if status == "success":
            flash("User created successfully.", "create_user:ok")
            return redirect(url_for('boundary.create_user'))  # refresh after post
        elif status == "duplicate":
            flash("A user with this email already exists.", "create_user:err")
        else:
            flash("An unexpected error occurred. Please try again later.", "create_user:err")
            
    return render_template("create_user.html", profiles=profiles["data"])

# -----------------------------------------------------------------------------
# Users (LIST + SEARCH) - protected
# -----------------------------------------------------------------------------
@bp.route('/users')
@login_required
def list_users():
    q = (request.args.get('q') or '').strip()
    page = request.args.get('page', default=1, type=int)  # pass None to disable pagination
    per_page = 20

    if q:
        res = UserSearchController().SearchUser(q, page=page, per_page=per_page)
    else:
        res = ListUserController().ListUsers(page=page, per_page=per_page)

    if not res["ok"]:
        for e in res["errors"]:
            flash(e, "list_users:err")
        return render_template('list_users.html', rows=[], q=q, pagination=None)

    return render_template(
        'list_users.html',
        rows=res["data"],                  # list[(UserAccount, UserProfile)]
        q=q,                               # Search list[(UserAccount, UserProfile)]
        pagination=res.get("pagination")   # dict or None
    )
    
# -----------------------------------------------------------------------------
# Users (UPDATE) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    ctrl = UpdateUserController()
    profiles = ListUserProfileController().ListUserProfile()
    user = ctrl.get(user_id)
    
    if not user:
        flash("User not found.", "update_user:err")
        return redirect(url_for("boundary.list_users"))
    
    if request.method == "POST":
        errors = []

        # Inline validation
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

        status = ctrl.UpdateUser(
            user_id=user_id,
            name=name_n,
            email=email_n,
            password=request.form.get("password") or None,
            profile_id=request.form.get("profile_id", "0"),
            is_suspended=int(request.form.get("is_suspended") or 0),
        )

        if status == "success":
            flash("User updated successfully.", "list_user:ok")
            return redirect(url_for("boundary.list_users"))
        elif status == "duplicate":
            flash("A user with this email already exists.", "update_user:err")
        elif status == "not_found":
            flash("User not found.", "update_user:err")
            return redirect(url_for("boundary.list_users"))
        else:
            flash("An unexpected error occurred while updating user.", "update_user:err")

    return render_template("update_user.html", user=user, profiles=profiles["data"])

# -----------------------------------------------------------------------------
# Users (SUSPEND) - protected
# -----------------------------------------------------------------------------
@bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
def suspend_user(user_id):
    is_suspended = int(request.form.get('is_suspended') or 0)
    status = SuspendedUserController().SuspendedUser(user_id, is_suspended)

    if status in ("success", "noop"):
        msg = "User suspended." if is_suspended else "User unsuspended."
        flash(msg, "list_user:ok")
    elif status == "not_found":
        flash("User not found.", "list_user:err")
    else:
        flash("Unexpected error while updating suspension.", "list_user:err")

    return redirect(url_for('boundary.list_users'))

# -----------------------------------------------------------------------------
# Profiles (CREATE) - protected
# -----------------------------------------------------------------------------
@bp.route('/profiles/new', methods=['GET','POST'])
@login_required
def create_profile():
    if request.method == "POST":
        status = CreateUserProfileController().CreateUserProfile(
            request.form.get("name", "").strip(),
            request.form.get("description", "").strip(),
            1 if request.form.get("is_suspended") else 0
        )
        
        if status == "success":
            flash("Profile created successfully.", "create_profile:ok")
        elif status == "duplicate":
            flash("A profile with this name already exists.", "create_profile:err")
        elif status == "invalid":
            flash("Profile name is required.", "create_profile:err")
        else:
            flash("An unexpected error occurred while creating the profile.", "create_profile:err")

        return redirect(url_for("boundary.create_profile"))

    return render_template("create_profile.html")

# -----------------------------------------------------------------------------
# Profiles (LIST + SEARCH) - protected
# -----------------------------------------------------------------------------
@bp.route('/profiles')
@login_required
def list_profiles():
    q = (request.args.get('q') or '').strip()

    if q:
        res = UserProfileSearchController().SearchUserProfile(q)
    else:
        res = ListUserProfileController().ListUserProfile()

    if not res["ok"]:
        for e in res["errors"]:
            flash(e, "list_profiles:err")
        return render_template('list_profiles.html', profiles=[], q=q)

    return render_template('list_profiles.html', profiles=res["data"], q=q)

# -----------------------------------------------------------------------------
# Profiles (UPDATE) - protected
# -----------------------------------------------------------------------------
@bp.route("/profiles/<int:profile_id>/edit", methods=["GET", "POST"])
@login_required
def edit_profile(profile_id):
    ctrl = UpdateUserProfileController()
    profile = ctrl.get(profile_id)
    
    if not profile:
        flash("Profile not found.", "update_profile:err")
        return redirect(url_for("boundary.list_profiles"))

    if request.method == "POST":
        errors = []

        # --- inline validation here (as you prefer) ---
        name_n = (request.form.get("name", "") or "").strip()
        desc_n = request.form.get("description", "") or ""
        is_susp = int(request.form.get('is_suspended') or 0)

        if not name_n:
            errors.append("Name is required.")

        if errors:
            for e in errors:
                flash(e, "update_profile:err")
            return render_template("update_profile.html", profile=profile["data"]), 400

        status = ctrl.UpdateUserProfile(profile_id, name_n, desc_n, is_susp)

        if status == "success":
            flash("Profile updated successfully.", "list_profile:ok")
            return redirect(url_for("boundary.list_profiles"))
        elif status == "duplicate":
            flash("A profile with this name already exists.", "update_profile:err")
        elif status == "not_found":
            flash("Profile not found.", "update_profile:err")
            return redirect(url_for("boundary.list_profiles"))
        elif status == "invalid":
            flash("Profile name cannot be empty.", "update_profile:err")
        else:
            flash("An unexpected database error occurred.", "update_profile:err")

    # GET or POST with errors
    return render_template("update_profile.html", profile=profile["data"])
 
# -----------------------------------------------------------------------------
# Users Profile (SUSPEND) - protected
# ----------------------------------------------------------------------------- 
@bp.route('/profiles/<int:profile_id>/suspend', methods=['POST'])
@login_required
def suspend_profile(profile_id):
    is_suspended = int(request.form.get('is_suspended') or 0)
    status = SuspendedUserProfileController().SuspendedUserProfile(profile_id, is_suspended)

    if status in ("success", "noop"):
        flash(("Profile suspended." if is_suspended else "Profile unsuspended."), "list_profile:ok")
    elif status == "not_found":
        flash("Profile not found.", "list_profile:err")
    else:
        flash("Unexpected error while updating profile.", "list_profile:err")

    return redirect(url_for('boundary.list_profiles'))
    
# -----------------------------------------------------------------------------
# Service Category (CREATE) - protected
# -----------------------------------------------------------------------------
@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_service_category():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        description = request.form.get('description').strip()
        is_suspended = int(request.form.get('is_suspended') or 0)

        status = CreateServiceCategoryController().CreateServiceCategory(name, description, is_suspended)

        if status == "success":
            flash('Category created successfully.', 'create_service:ok')
            return redirect(url_for('boundary.create_service_category'))
        elif status == "duplicate":
            flash('A category with this name already exists.', 'create_service:err')
        elif status == "invalid":
            flash('Category name is required.', 'create_service:err')
        else:
            flash('An unexpected database error occurred.', 'create_service:err')

    return render_template('create_service_category.html')

# -----------------------------------------------------------------------------
# Service Category (LIST + SEARCH) - protected
# -----------------------------------------------------------------------------
@bp.route('/categories', methods=['GET'])
@login_required
def list_service_categories():
    q = (request.args.get('q') or '').strip()

    if q:
        res = SearchServiceCategoryController().SearchServiceCategory(q)
    else:
        res = ListServiceCategoryController().ListServiceCategory()

    if not res["ok"]:
        for e in res.get("errors", []):
            flash(e, "list_service_categories:err")
        return render_template('list_service_categories.html', categories=[], q=q)

    return render_template('list_service_categories.html', categories=res.get("data", []), q=q)

# -----------------------------------------------------------------------------
# Service Category (UPDATE) - protected
# -----------------------------------------------------------------------------
@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def update_service_category(category_id):
    ctrl = UpdateServiceCategoryController()
    row = ctrl.get(category_id)
    
    if not row['ok']:
        flash('Category not found.', 'list_service:err')
        return redirect(url_for('boundary.list_service_categories'))

    if request.method == 'POST':
        name = (request.form.get('name', '') or '').strip()
        description = (request.form.get('description', '') or '').strip()
        is_suspended = int(request.form.get('is_suspended') or 0)
        
        status = ctrl.UpdateServiceCategory(category_id, name, description, is_suspended)

        if status == "success":
            flash("Category updated successfully.", "list_service:ok")
            return redirect(url_for("boundary.list_service_categories"))
        elif status == "duplicate":
            flash("Another category with this name already exists.", "update_service:err")
        elif status == "not_found":
            flash("Category not found.", "list_service:err")
            return redirect(url_for("boundary.list_service_categories"))
        elif status == "invalid":
            flash("Category name cannot be empty.", "update_service:err")
        else:
            flash("Unexpected database error while updating category.", "update_service:err")

    return render_template("update_service_category.html", category=row["data"])
    
# -----------------------------------------------------------------------------
# Service Category (SUSPEND) - protected
# ----------------------------------------------------------------------------- 
@bp.route('/categories/<int:category_id>/suspend', methods=['POST'])
@login_required
def suspend_service_category(category_id):
    is_suspended = int(request.form.get('is_suspended') or 0)
    status = SuspendedServiceCategoryController().SuspendedServiceCategory(category_id, is_suspended)

    if status in ("success", "noop"):
        flash(("Category suspended." if is_suspended else "Category unsuspended."), "list_service:ok")
    elif status == "not_found":
        flash("Category not found.", "list_service:err")
    else:
        flash("Unexpected error while updating category.", "list_service:err")

    return redirect(url_for('boundary.list_service_categories'))

#PIN ROUTES 
# -----------------------------------------------------------------------------

#landing page for PIN#
@bp.route('/pin/dashboard')
@login_required
def pin_dashboard():
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    return render_template('pin_dashboard.html')

@bp.route('/pin/requests/new', methods=['GET', 'POST'])
@login_required
def create_request():
    #BOUNDARY for: As PIN, I want to create requests#
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    if request.method == 'POST':
        # BOUNDARY: Handle ALL user input validation
        title = (request.form.get('title', '') or '').strip()
        description = (request.form.get('description', '') or '').strip()
        category = (request.form.get('category', '') or '').strip()
        
        errors = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if not category:
            errors.append("Category is required.")
        if len(title) < 5:
            errors.append("Title must be at least 5 characters.")
        if len(description) < 10:
            errors.append("Description must be at least 10 characters.")
        
        # BOUNDARY: Handle date validation
        preferred_date = None
        date_str = request.form.get('preferred_date', '')
        if date_str:
            try:
                preferred_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if preferred_date < datetime.now().date():
                    errors.append("Preferred date cannot be in the past.")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD.")
        
        if errors:
            for e in errors:
                flash(e, "create_request:err")
            return render_template('create_request.html'), 400
        
        # Prepare clean data for controller
        request_data = {
            'pin_id': session.get('user_id'),
            'title': title,
            'description': description,
            'category': category,
            'urgency': request.form.get('urgency', 'medium'),
            'location': (request.form.get('location', '') or '').strip(),
            'preferred_date': preferred_date
        }
        
        # CONTROL: Pure data passing to story-specific controller
        ctrl = PINCreateRequestController()
        result = ctrl.create_request(request_data)
        
        # BOUNDARY: Handle display to user
        if result['success']:
            flash("Request created successfully.", "create_request:ok")
            return redirect(url_for('boundary.pin_requests'))
        else:
            for e in result['errors']:
                flash(e, "create_request:err")
    
    return render_template('create_request.html')

@bp.route('/pin/requests')
@login_required
def pin_requests():
    #BOUNDARY for: As PIN, I want to view my active requests#
    if session.get("profile_name", "").lower() != "pin": 
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    # BOUNDARY: Call controller
    ctrl = PINViewRequestsController()
    result = ctrl.get_active_requests(session.get('user_id'))
    
    # BOUNDARY: Handle display
    if result['success']:
        requests = result['data']
    else:
        requests = []
        for e in result['errors']:
            flash(e, "error")
    
    return render_template('pin_requests.html', requests=requests, current_page='active')


@bp.route('/pin/requests/history')
@login_required
def request_history():
    #BOUNDARY for: As PIN, I want to view my request history#
    if session.get("profile_name", "").lower() != "pin": 
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    # BOUNDARY: Call controller
    ctrl = PINViewHistoryController()
    result = ctrl.get_request_history(session.get('user_id'))
    
    # BOUNDARY: Handle display
    if result['success']:
        requests = result['data']
    else:
        requests = []
        for e in result['errors']:
            flash(e, "error")
    
    return render_template('pin_requests.html', requests=requests, title="Request History", current_page='history')



@bp.route('/pin/requests/<int:request_id>/suspend', methods=['POST'])
@login_required
def suspend_request(request_id):
    #BOUNDARY for: As PIN, I want to suspend my requests#
    if session.get("profile_name", "").lower() != "pin": 
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    # CONTROL: Pure data passing to story-specific controller
    ctrl = PINSuspendRequestController()
    result = ctrl.suspend_request(request_id, session.get('user_id'))
    
    # BOUNDARY: Handle display to user
    if result['success']:
        flash("Request suspended successfully.", "suspend_request:ok")
    else:
        for e in result['errors']:
            flash(e, "suspend_request:err")
    
    return redirect(url_for('boundary.pin_requests'))



@bp.route('/pin/requests/search', methods=['GET'])
@login_required
def search_requests():
    #BOUNDARY for: As PIN, I want to search my requests#
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    # BOUNDARY: Get user input
    search_term = request.args.get('q', '').strip()
    pin_id = session.get('user_id')
    current_page = request.args.get('page', 'active')  # Get the page context
    
    # BOUNDARY: Handle empty search - stay on current page
    if not search_term:
        flash("Please enter a search term", "error")
        if current_page == 'history':
            return redirect(url_for('boundary.request_history'))
        else:
            return redirect(url_for('boundary.pin_requests'))
    
    # BOUNDARY: Call controller
    ctrl = PINSearchRequestsController()
    result = ctrl.search_requests(pin_id, search_term)
    
    # BOUNDARY: Handle user display
    if result['success']:
        requests = result['data']
        if not requests:
            flash(f"No requests found for '{search_term}'", "info")
        
        # Stay on the same page type (history vs active)
        template_data = {
            'requests': requests, 
            'search_term': search_term,
            'current_page': current_page
        }
        
        # Set appropriate title based on page context
        if current_page == 'history':
            template_data['title'] = f"Search Results for '{search_term}' - History"
        else:
            template_data['title'] = f"Search Results for '{search_term}'"
        
        return render_template('pin_requests.html', **template_data)
    else:
        for error in result['errors']:
            flash(error, "error")
        # Redirect back to appropriate page
        if current_page == 'history':
            return redirect(url_for('boundary.request_history'))
        else:
            return redirect(url_for('boundary.pin_requests'))
