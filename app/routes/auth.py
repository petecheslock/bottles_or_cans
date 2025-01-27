from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.user import UserService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/setup', methods=['GET', 'POST'])
def setup():
    # Check if admin already exists
    if UserService.get_admin_user():
        flash('Setup has already been completed')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('auth/setup.html')
            
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/setup.html')
            
        # Create admin user
        UserService.create_admin_user(username, password)
        
        # Handle JSON file upload if provided
        json_file = request.files.get('json_file')
        print(f"Files in request: {list(request.files.keys())}")  # Debug print
        print(f"JSON file present: {json_file is not None}")  # Debug print
        
        if json_file:
            try:
                print(f"Received file: {json_file.filename}")
                print(f"File content type: {json_file.content_type}")  # Debug print
                print(f"File content length: {json_file.content_length}")  # Debug print
                data = json.load(json_file)
                print(f"Parsed JSON data: {data}")
                UserService.import_initial_data(data)
                flash('Database initialized with provided data')
            except Exception as e:
                print(f"Error processing file: {str(e)}")
                flash(f'Error importing data: {str(e)}')
        
        flash('Setup completed successfully')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/setup.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    # Check for first-time setup
    if not UserService.get_admin_user():
        return redirect(url_for('auth.setup'))
    # Check if already logged in
    if 'logged_in' in session:
        flash('You are already logged in')
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate required fields
        if not username:
            flash('Username is required', 'danger')
            return render_template('admin_login.html'), 400
        if not password:
            flash('Password is required', 'danger')
            return render_template('admin_login.html'), 400
            
        user = UserService.authenticate_admin(username, password)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid credentials.', 'danger')
    
    return render_template('admin_login.html')

@auth_bp.route('/admin/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/users/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    if not user_id:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    success, message = UserService.change_admin_password(
        user_id, 
        current_password, 
        new_password, 
        confirm_password
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.manage_users')) 