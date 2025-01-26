from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from functools import wraps
import random
from werkzeug.security import generate_password_hash, check_password_hash
from captcha.image import ImageCaptcha
import base64
from io import BytesIO
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bottles_or_cans.db')
app.config['SQLALCHEMY_TRACK_CHANGES'] = False
app.config['SECRET_KEY'] = '0ef430d376ef2a44e9f946682eb16ac1'
db = SQLAlchemy(app)

# Add these constants at the top of the file
SEED_VOTES_MIN = 10  # Minimum number of seed votes per category
SEED_VOTES_MAX = 20  # Maximum number of seed votes per category

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    votes_headphones = db.Column(db.Integer, default=0)
    votes_wine = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class PendingReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 addresses can be up to 45 chars

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # Check if user has seen the landing page
    if not session.get('seen_landing'):
        return render_template('landing.html')
    return redirect(url_for('play_game'))

@app.route('/play')
def play_game():
    review = Review.query.order_by(db.func.random()).first()
    if review:
        total_votes = review.votes_headphones + review.votes_wine
        if total_votes > 0:
            headphones_percentage = int((review.votes_headphones / total_votes) * 100)
            wine_percentage = int((review.votes_wine / total_votes) * 100)
        else:
            headphones_percentage = 0
            wine_percentage = 0
    else:
        headphones_percentage = 0
        wine_percentage = 0
    
    # Remove the session-based vote tracking
    return render_template('index.html', 
                         review=review, 
                         headphones_percentage=headphones_percentage,
                         wine_percentage=wine_percentage,
                         has_voted=False)  # Always set has_voted to False

@app.route('/start')
def start_game():
    # Mark that the user has seen the landing page
    session['seen_landing'] = True
    return redirect(url_for('play_game'))

@app.route('/vote', methods=['POST'])
def vote():
    review_id = request.form.get('review_id')
    vote_type = request.form.get('vote_type')
    
    review = Review.query.get_or_404(review_id)
    
    if vote_type == 'headphones':
        review.votes_headphones += 1
    elif vote_type == 'wine':
        review.votes_wine += 1
    
    # Store voted review ID in session
    voted_reviews = session.get('voted_reviews', [])
    if review_id not in voted_reviews:
        voted_reviews.append(int(review_id))
        session['voted_reviews'] = voted_reviews
    
    db.session.commit()

    # Add virtual votes to smooth percentages
    virtual_votes = 10  # Baseline votes per category
    total_votes = (review.votes_headphones + review.votes_wine + (virtual_votes * 2))
    headphones_percentage = int(((review.votes_headphones + virtual_votes) / total_votes) * 100)
    wine_percentage = int(((review.votes_wine + virtual_votes) / total_votes) * 100)

    return jsonify({
        'headphones_percentage': headphones_percentage,
        'wine_percentage': wine_percentage
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.is_admin and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/manage-reviews')
@login_required
def admin_manage_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('manage_reviews.html', reviews=reviews)

@app.route('/admin/delete-review/<int:review_id>', methods=['POST'])
@login_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin_manage_reviews'))

@app.route('/admin/edit-review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if request.method == 'POST':
        review.text = request.form.get('review_text')
        db.session.commit()
        flash('Review updated successfully!', 'success')
        return redirect(url_for('admin_manage_reviews'))
    
    return render_template('edit_review.html', review=review)

@app.route('/admin')
def admin():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('admin_login'))

@app.route('/reset-votes', methods=['POST'])
@login_required
def reset_votes():
    try:
        # Reset all vote counts to zero
        Review.query.update({
            Review.votes_headphones: 0,
            Review.votes_wine: 0
        })
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/seed-reviews', methods=['POST'])
@login_required
def seed_reviews():
    try:
        reviews = Review.query.all()
        for review in reviews:
            review.votes_headphones = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
            review.votes_wine = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

def generate_image_captcha():
    # Create image with custom settings
    image = ImageCaptcha(
        width=280,          # Increase width for better readability
        height=90,          # Comfortable height
        fonts=[             # Use more readable fonts if available
            'Arial',
            'Courier',
            'Times New Roman'
        ],
        font_sizes=(46, 58, 68)  # Larger font sizes
    )

    # Generate simpler text - avoid confusing characters
    allowed_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Removed confusing chars like I,1,0,O
    captcha_text = ''.join(random.choices(allowed_chars, k=5))  # Reduced to 5 characters
    
    # Add custom settings for image generation
    captcha_image = image.generate(
        captcha_text,
        format='png'
    )
    
    # Convert to base64
    buffered = BytesIO()
    image.write(captcha_text, buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return captcha_text, img_str

# Update the rate limiting helper function to check for admin status
def check_rate_limit(ip_address, limit_minutes=30):
    # Skip rate limiting for admins
    if session.get('logged_in') and session.get('user_id'):
        user = User.query.get(session.get('user_id'))
        if user and user.is_admin:
            return True

    rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
    current_time = datetime.now(timezone.utc)
    
    if not rate_limit:
        # First attempt
        rate_limit = RateLimit(
            ip_address=ip_address,
            attempt_count=1,
            last_attempt=current_time
        )
        db.session.add(rate_limit)
        db.session.commit()
        return True
        
    # Check if blocked
    if rate_limit.is_blocked:
        return False
        
    # Ensure last_attempt is timezone-aware
    if rate_limit.last_attempt.tzinfo is None:
        rate_limit.last_attempt = rate_limit.last_attempt.replace(tzinfo=timezone.utc)
        
    # Check if outside time window
    time_diff = current_time - rate_limit.last_attempt
    if time_diff.total_seconds() >= (limit_minutes * 60):
        # Reset counter if outside time window
        rate_limit.attempt_count = 1
        rate_limit.last_attempt = current_time
        db.session.commit()
        return True
        
    # Increment attempt count
    rate_limit.attempt_count += 1
    rate_limit.last_attempt = current_time
    
    # Check if should be blocked
    if rate_limit.attempt_count >= 5:
        rate_limit.is_blocked = True
        db.session.commit()
        return False
        
    db.session.commit()
    return True

@app.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    is_admin = session.get('logged_in') and session.get('user_id') and \
               User.query.get(session.get('user_id')).is_admin

    if request.method == 'POST':
        ip_address = request.remote_addr
        review_text = request.form.get('review_text')
        
        # For non-admin users, check rate limit and captcha
        if not is_admin:
            if not check_rate_limit(ip_address):
                flash('You have submitted too many reviews. Please wait before trying again.', 'danger')
                captcha_text, captcha_image = generate_image_captcha()
                session['captcha_answer'] = captcha_text
                return render_template('submit_review.html', 
                                     captcha_image=captcha_image,
                                     is_admin=is_admin)

            user_answer = request.form.get('captcha_answer', '').upper()
            correct_answer = session.get('captcha_answer')
            
            if not user_answer or not correct_answer or user_answer != correct_answer:
                flash('Please enter the CAPTCHA text correctly.', 'danger')
                captcha_text, captcha_image = generate_image_captcha()
                session['captcha_answer'] = captcha_text
                return render_template('submit_review.html', 
                                     captcha_image=captcha_image,
                                     is_admin=is_admin)

            # Create pending review for non-admin users
            new_review = PendingReview(
                text=review_text,
                ip_address=ip_address
            )
        else:
            # Create direct review with seed votes for admin users
            seed_headphones = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
            seed_wine = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
            new_review = Review(
                text=review_text,
                votes_headphones=seed_headphones,
                votes_wine=seed_wine
            )
        
        db.session.add(new_review)
        db.session.commit()
        
        if is_admin:
            flash('Review added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        session['voted_reviews'] = []  # Reset voted reviews when submitting a new one
        return render_template('submit_thanks.html')
    
    # GET request
    captcha_image = None
    if not is_admin:
        captcha_text, captcha_image = generate_image_captcha()
        session['captcha_answer'] = captcha_text
    
    return render_template('submit_review.html', 
                         captcha_image=captcha_image,
                         is_admin=is_admin)

@app.route('/admin/pending-reviews', methods=['GET', 'POST'])
@login_required
def pending_reviews():
    if request.method == 'POST':
        review_id = request.form.get('review_id')
        action = request.form.get('action')
        
        if review_id and action == 'reject':
            review = PendingReview.query.get_or_404(review_id)
            review.status = 'rejected'
            db.session.commit()
            flash('Review rejected successfully.', 'success')
            return redirect(url_for('pending_reviews'))
    
    # GET request handling
    pending_reviews = PendingReview.query.filter_by(status='pending').order_by(PendingReview.created_at.desc()).all()
    return render_template('pending_reviews.html', pending_reviews=pending_reviews)

@app.route('/review-action/<int:review_id>/<action>', methods=['POST'])
@login_required
def review_action(review_id, action):
    pending_review = PendingReview.query.get_or_404(review_id)
    
    if action == 'approve':
        # Generate random seed votes
        seed_headphones = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        seed_wine = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        
        # Create new approved review
        new_review = Review(
            text=pending_review.text,
            votes_headphones=seed_headphones,
            votes_wine=seed_wine
        )
        db.session.add(new_review)
        pending_review.status = 'approved'
        flash('Review approved and added to the game!', 'success')
    
    elif action == 'reject':
        pending_review.status = 'rejected'
        flash('Review rejected.', 'warning')
    
    db.session.commit()
    return redirect(url_for('pending_reviews'))

@app.route('/admin/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/users/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    if not user_id:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    else:
        user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')
    
    return redirect(url_for('manage_users'))

# Add this new model class
class RateLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    last_attempt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    attempt_count = db.Column(db.Integer, default=1)
    is_blocked = db.Column(db.Boolean, default=False)

    def is_rate_limited(self):
        # Always ensure last_attempt is timezone-aware
        if self.last_attempt.tzinfo is None:
            self.last_attempt = self.last_attempt.replace(tzinfo=timezone.utc)
            
        time_diff = datetime.now(timezone.utc) - self.last_attempt
        
        # If more than 30 minutes have passed, not rate limited
        if time_diff.total_seconds() >= (30 * 60):
            return False
        
        # Rate limited if within time window and too many attempts
        return self.attempt_count >= 5

@app.route('/admin/rate-limits', methods=['GET', 'POST'])
@login_required
def manage_rate_limits():
    if request.method == 'POST':
        ip_address = request.form.get('ip_address')
        action = request.form.get('action')
        
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if rate_limit:
            if action == 'unblock':
                rate_limit.is_blocked = False
                rate_limit.attempt_count = 0
                flash('IP address unblocked successfully.', 'success')
            elif action == 'block':
                rate_limit.is_blocked = True
                flash('IP address blocked successfully.', 'success')
            elif action == 'delete':
                db.session.delete(rate_limit)
                flash('Rate limit record deleted successfully.', 'success')
            
            db.session.commit()
    
    rate_limits = RateLimit.query.order_by(RateLimit.last_attempt.desc()).all()
    return render_template('rate_limits.html', rate_limits=rate_limits)

@app.route('/refresh-captcha', methods=['POST'])
def refresh_captcha():
    captcha_text, captcha_image = generate_image_captcha()
    session['captcha_answer'] = captcha_text
    return jsonify({
        'captcha_image': captcha_image
    })

if __name__ == '__main__':
    app.run(debug=True) 