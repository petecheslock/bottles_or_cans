from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.services.user import UserService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    # Check if already logged in
    if 'logged_in' in session:
        flash('You are already logged in')
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Add debug logging
        current_app.logger.debug(f"Login attempt for username: {username}")
        
        # Validate required fields
        if not username:
            flash('Username is required', 'danger')
            return render_template('admin_login.html'), 400
        if not password:
            flash('Password is required', 'danger')
            return render_template('admin_login.html'), 400
            
        user = UserService.authenticate_admin(username, password)
        if user:
            current_app.logger.info(f"Successful login for user: {username}")
            session['logged_in'] = True
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        
        current_app.logger.warning(f"Failed login attempt for username: {username}")
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

@auth_bp.route('/admin')
@auth_bp.route('/admin/')
def admin_index():
    """Redirect /admin and /admin/ to appropriate page based on login status"""
    if session.get('logged_in'):
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login')) 