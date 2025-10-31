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
    PINViewHistoryController, PINSearchRequestsController,
    PINUpdateRequestController, PINRequestViewCountController,
    PINRequestShortlistCountController, 
    PINCompletedMatchesSearchController,
    PINCompletedMatchesHistoryController,
)

from .control.CSRControllers import (
    CSRSearchAvailableRequestsController,
    CSRViewRequestDetailsController,
    CSRSaveToShortlistController,
    CSRSearchShortlistedRequestsController,
    CSRViewShortlistedRequestController,
    CSRRemoveFromShortlistController,
    CSRViewCompletedServicesController,
    CSRSearchCompletedServicesController
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
        print(profile_name)
        if profile_name == "admin":
            return redirect(url_for('boundary.admin_dashboard'))
        elif profile_name == "platform management":
            return redirect(url_for('boundary.list_service_categories'))
        elif profile_name == "pin":
            return redirect(url_for('boundary.pin_dashboard'))
        elif profile_name == "csr rep": 
            return redirect(url_for('boundary.csr_dashboard'))
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
# User Admin dashboard
# -----------------------------------------------------------------------------
@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    role = (session.get("profile_name") or "").lower()
    if role != "admin":
        flash("You do not have permission to access the admin dashboard.", "error")
        return redirect(url_for('boundary.home'))
    return render_template("AdminDashboard.html")

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
     
    # 🔹 Load all active categories
    # 🔹 Get active categories (list[ServiceCategory])
    res = ListServiceCategoryController().ListServiceCategory(page=None)  # returns {"ok":..., "data":[...]}
    categories = [c for c in res.get("data", []) if not getattr(c, "is_suspended", False)]
    
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
                flash(e, "err")
            return render_template('create_request.html', categories=categories), 400
        
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
        if result == "success":
            flash("Request created successfully.", "ok")
            return redirect(url_for('boundary.pin_requests'))
        else:
            flash(result, "err")  
    
    return render_template('create_request.html', categories=categories)


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
    if type(result) == str:
    	flash(result, "err")
    	requests = []
    else:  
    	requests = result  #success with request list

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
    if type(result) == str:
    	flash(result, "err")
    	requests = []
    else:  
    	requests = result  #success with request list
    
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
    if result == "success":
        flash("Request suspended.", "suspend_request:ok")
    else:
        flash(result, "suspend_request:err")  # Show database error
    
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
    if isinstance(result, str):  #  String = error
        flash(f"No requests found for '{search_term}'", "info")
        requests = []
    else:  # storing request object
        requests = result
       
    
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





@bp.route('/pin/requests/<int:request_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    # BOUNDARY: User interaction ONLY
    if session.get("profile_name", "").lower() != "pin": 
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    pin_id = session.get('user_id')
    ctrl = PINUpdateRequestController()
    
    # GET: Get request data through controller for display
    if request.method == 'GET':
        result = ctrl.get_request_for_display(request_id, pin_id)
        
        if isinstance(result, str):
            if result == "not_found":
                flash("Request not found or access denied.", "error")
            elif result == "can_only_edit_active":
                flash("Can only edit active requests (pending, approved, or in progress).", "error")
            else:
                flash("Error loading request.", "error")
            return redirect(url_for('boundary.pin_requests'))
        
        # BOUNDARY: Render template with actual request data
        return render_template('edit_request.html', request=result)
    
    # POST: Handle form submission
    if request.method == 'POST':
        title = (request.form.get('title', '') or '').strip()
        description = (request.form.get('description', '') or '').strip()
        category = (request.form.get('category', '') or '').strip()
        
        errors = []
        if not title: errors.append("Title is required.")
        if not description: errors.append("Description is required.")
        if not category: errors.append("Category is required.")
        if len(title) < 5: errors.append("Title must be at least 5 characters.")
        if len(description) < 10: errors.append("Description must be at least 10 characters.")
        
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
                flash(e, "err")
            # Get current data through controller for re-rendering
            current_result = ctrl.get_request_for_display(request_id, pin_id)
            if isinstance(current_result, str):
                return redirect(url_for('boundary.pin_requests'))
            return render_template('edit_request.html', request=current_result), 400
        
        # BOUNDARY: Prepare data for controller
        update_data = {
            'title': title,
            'description': description,
            'category': category,
            'urgency': request.form.get('urgency', 'medium'),
            'location': (request.form.get('location', '') or '').strip(),
            'preferred_date': preferred_date
        }
        
        # BOUNDARY: Call controller
        result = ctrl.update_request(request_id, pin_id, update_data)
        
        # BOUNDARY: Handle user feedback
        if result == "success":
            flash("Request updated successfully!", "ok")
            return redirect(url_for('boundary.pin_requests'))
        elif result == "can_only_update_active":
            flash("Can only update active requests.", "error")
        else:
            flash("Error updating request.", "error")
            
        return redirect(url_for('boundary.pin_requests'))
        
@bp.route('/pin/requests/<int:request_id>/analytics')
@login_required
def pin_request_analytics(request_id):
    #BOUNDARY for: As PIN, I want to see how many times my request has been viewed and shortlisted#
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    pin_id = session.get('user_id')
    
    # BOUNDARY: Get request details for context
    request_ctrl = PINUpdateRequestController()
    request = request_ctrl.get_request_for_display(request_id, pin_id)
    
    if isinstance(request, str):
        if request == "not_found":
            flash("Request not found or access denied.", "error")
        elif request == "can_only_edit_active":
            flash("Cannot view analytics for this request.", "error")
        else:
            flash("Error loading request details.", "error")
        return redirect(url_for('boundary.pin_requests'))
    
    # BOUNDARY: Call specific controllers for view and shortlist counts
    view_ctrl = PINRequestViewCountController()
    shortlist_ctrl = PINRequestShortlistCountController()
    
    view_count = view_ctrl.get_view_count(request_id, pin_id)
    shortlist_count = shortlist_ctrl.get_shortlist_count(request_id, pin_id)
    
    # BOUNDARY: Handle errors
    if isinstance(view_count, str) or isinstance(shortlist_count, str):
        flash("Error loading analytics data.", "error")
        return redirect(url_for('boundary.pin_requests'))
    
    return render_template('pin_request_analytics.html', 
                         request=request, 
                         view_count=view_count,
                         shortlist_count=shortlist_count)

# 🆕 NEW: PIN Completed Matches History (User Story 4)
@bp.route('/pin/matches/completed/history')
@login_required
def pin_completed_matches_history():
    #BOUNDARY for: As PIN, I want to view the history of my completed matches#
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    pin_id = session.get('user_id')
    
    # BOUNDARY: Call specific controller
    ctrl = PINCompletedMatchesHistoryController()
    result = ctrl.get_completed_matches_history(pin_id)
    
    # BOUNDARY: Handle display
    if isinstance(result, str):
        flash("Error loading completed matches history.", "error")
        matches = []
    else:
        matches = result
    
    return render_template('pin_completed_matches.html', 
                         matches=matches,
                         search_category=None,
                         search_date=None)

# 🆕 NEW: PIN Search Completed Matches (User Story 3)
@bp.route('/pin/matches/completed/search')
@login_required
def pin_search_completed_matches():
    #BOUNDARY for: As PIN, I want to search my completed matches by service type and date#
    if session.get("profile_name", "").lower() != "pin":  
        flash("Access denied. PIN profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    
    pin_id = session.get('user_id')
    
    # BOUNDARY: Get search parameters
    search_category = request.args.get('category', '').strip()
    search_date = request.args.get('date', '').strip()
    
    # BOUNDARY: Validate date format
    parsed_date = None
    if search_date:
        try:
            parsed_date = datetime.strptime(search_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            search_date = ""
    
    # BOUNDARY: Call specific controller
    ctrl = PINCompletedMatchesSearchController()
    result = ctrl.search_completed_matches(pin_id, search_category, parsed_date)
    
    # BOUNDARY: Handle display
    if isinstance(result, str):
        flash("Error searching completed matches.", "error")
        matches = []
    else:
        matches = result
    
    return render_template('pin_completed_matches.html', 
                         matches=matches,
                         search_category=search_category,
                         search_date=search_date)
        
        
        
        
        
#CSR ROUTES 
# -----------------------------------------------------------------------------
@bp.route('/csr/dashboard')
@login_required
def csr_dashboard():
    #BOUNDARY for: As CSR, I want to access my dashboard#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied. CSR Representative profile required.", "error")
        return redirect(url_for("boundary.on_login"))
    return render_template('csr_dashboard.html')
    
    
# User Story 1 Boundary
@bp.route('/csr/requests/search')
@login_required
def csr_search_available_requests():
    #BOUNDARY for: As CSR, I want to search for available service requests#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    search_term = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    urgency = request.args.get('urgency', '').strip()
    
    ctrl = CSRSearchAvailableRequestsController()
    result = ctrl.search_available_requests(search_term, category, urgency)
    
    if isinstance(result, str):
        flash("Error searching requests.", "error")
        requests = []
    else:
        requests = result
    
    return render_template('csr_search_requests.html', 
                         requests=requests, 
                         search_term=search_term,
                         category=category,
                         urgency=urgency)


@bp.route('/csr/requests/<int:request_id>')
@login_required
def csr_view_request_details(request_id):
    #BOUNDARY for: As CSR, I want to view detailed information about a service request#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    
    ctrl = CSRViewRequestDetailsController()
    result = ctrl.get_request_details(request_id, csr_company_id)
    
    if isinstance(result, str):
        flash("Request not found.", "error")
        return redirect(url_for('boundary.csr_search_available_requests'))
    
    return render_template('csr_request_details.html', request=result)


@bp.route('/csr/shortlist/add/<int:request_id>', methods=['POST'])
@login_required
def csr_save_to_shortlist(request_id):
    #BOUNDARY for: As CSR, I want to save interesting requests to a shortlist#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    ctrl = CSRSaveToShortlistController()
    result = ctrl.add_to_shortlist(request_id, csr_company_id)
    
    if result == "success":
        flash("Request added to shortlist!", "ok")
    elif result == "already_shortlisted":
        flash("Request is already in your shortlist.", "info")
    else:
        flash("Error adding to shortlist.", "error")
    
    return redirect(url_for('boundary.csr_search_available_requests'))



@bp.route('/csr/shortlist/search')
@login_required
def csr_search_shortlisted_requests():
    #BOUNDARY for: As CSR, I want to search through my shortlisted requests#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    search_term = request.args.get('q', '').strip()
    csr_company_id = session.get('user_id')
    
    ctrl = CSRSearchShortlistedRequestsController()
    result = ctrl.search_shortlisted_requests(csr_company_id, search_term)
    
    if isinstance(result, str):
        flash("Error loading shortlist.", "error")
        requests = []
    else:
        requests = result
    
    return render_template('csr_shortlist.html', 
                         requests=requests, 
                         search_term=search_term)


@bp.route('/csr/shortlist/<int:request_id>')
@login_required
def csr_view_shortlisted_request(request_id):
    #BOUNDARY for: As CSR, I want to view the details of my shortlisted requests#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    ctrl = CSRViewShortlistedRequestController()
    result = ctrl.get_shortlisted_request_details(request_id, csr_company_id)
    
    if isinstance(result, str):
        flash("Request not found in your shortlist.", "error")
        return redirect(url_for('boundary.csr_search_shortlisted_requests'))
    
    return render_template('csr_shortlisted_request_details.html', request=result)


@bp.route('/csr/shortlist/remove/<int:request_id>', methods=['POST'])
@login_required
def csr_remove_from_shortlist(request_id):
    #BOUNDARY for removing from shortlist#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    ctrl = CSRRemoveFromShortlistController()
    result = ctrl.remove_from_shortlist(request_id, csr_company_id)
    
    if result == "success":
        flash("Request removed from shortlist.", "ok")
    else:
        flash("Error removing from shortlist.", "error")
    
    return redirect(url_for('boundary.csr_search_shortlisted_requests'))
    
    
@bp.route('/csr/services/completed/history')
@login_required
def csr_completed_services_history():
    #BOUNDARY for: As CSR Representative, I want to view the history of completed volunteer services#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    
    ctrl = CSRViewCompletedServicesController()
    result = ctrl.get_completed_services_history(csr_company_id)
    
    if isinstance(result, str):
        flash("Error loading completed services history.", "error")
        services = []
    else:
        services = result
    
    return render_template('csr_completed_services.html', 
                         services=services,
                         search_category=None,
                         search_date=None,
                         current_page='history')


@bp.route('/csr/services/completed/search')
@login_required
def csr_search_completed_services():
    #BOUNDARY for: As CSR Representative, I want to search for completed volunteer services by type and date#
    if session.get("profile_name", "").lower() != "csr rep": 
        flash("Access denied.", "error")
        return redirect(url_for("boundary.on_login"))
    
    csr_company_id = session.get('user_id')
    
    # BOUNDARY: Get search parameters
    search_category = request.args.get('category', '').strip()
    search_date = request.args.get('date', '').strip()
    
    # BOUNDARY: Validate date format
    parsed_date = None
    if search_date:
        try:
            parsed_date = datetime.strptime(search_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            search_date = ""
    
    ctrl = CSRSearchCompletedServicesController()
    result = ctrl.search_completed_services(csr_company_id, search_category, parsed_date)
    
    if isinstance(result, str):
        flash("Error searching completed services.", "error")
        services = []
    else:
        services = result
    
    return render_template('csr_completed_services.html', 
                         services=services,
                         search_category=search_category,
                         search_date=search_date,
                         current_page='search')
