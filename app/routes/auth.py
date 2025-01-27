from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.user import UserService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
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
    
    result = UserService.change_admin_password(
        user_id, 
        current_password, 
        new_password, 
        confirm_password
    )
    
    if result:
        flash('Password updated successfully!', 'success')
    else:
        flash('Failed to update password. Please check your input.', 'danger')
    
    return redirect(url_for('admin.manage_users')) 