from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import random
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PendingReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 addresses can be up to 45 chars

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    
    # Get whether user has voted on this review from session
    voted_reviews = session.get('voted_reviews', [])
    has_voted = review.id in voted_reviews if review else False
    
    return render_template('index.html', 
                         review=review, 
                         has_voted=has_voted,
                         headphones_percentage=headphones_percentage,
                         wine_percentage=wine_percentage)

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
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/add-review', methods=['GET', 'POST'])
@login_required
def add_review():
    print("Accessing add-review route")
    total_reviews = Review.query.count()
    
    if request.method == 'POST':
        # Generate random seed votes
        seed_headphones = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        seed_wine = random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        
        new_review = Review(
            text=request.form.get('review_text'),
            votes_headphones=seed_headphones,  # Add seed votes
            votes_wine=seed_wine              # Add seed votes
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        flash('Review added successfully! Add another?', 'success')
        return redirect(url_for('add_review'))
    
    return render_template('add_review.html', total_reviews=total_reviews)

@app.route('/manage-reviews')
@login_required
def manage_reviews():
    # Get all reviews ordered by creation date (newest first)
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('manage_reviews.html', reviews=reviews)

@app.route('/delete-review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('manage_reviews'))

@app.route('/edit-review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if request.method == 'POST':
        review.text = request.form.get('review_text')
        db.session.commit()
        flash('Review updated successfully!', 'success')
        return redirect(url_for('manage_reviews'))
    
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
        flash('All vote counts have been reset successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error resetting votes. Please try again.', 'danger')
    
    return redirect(url_for('manage_reviews'))

@app.route('/seed-reviews', methods=['POST'])
@login_required
def seed_reviews():
    try:
        reviews = Review.query.all()
        
        for review in reviews:
            if review.votes_headphones + review.votes_wine < 5:  # Only seed reviews with few votes
                review.votes_headphones += random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
                review.votes_wine += random.randint(SEED_VOTES_MIN, SEED_VOTES_MAX)
        
        db.session.commit()
        flash('Reviews seeded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error seeding reviews. Please try again.', 'danger')
    
    return redirect(url_for('manage_reviews'))

def generate_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-'])
    if operator == '+':
        answer = num1 + num2
    else:
        # Ensure subtraction always gives positive result
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2
    question = f"{num1} {operator} {num2} = ?"
    return question, str(answer)

# Add a rate limiting helper function
def check_rate_limit(ip_address, limit_minutes=10):
    # Check how many submissions this IP has made in the last hour
    cutoff_time = datetime.utcnow() - timedelta(minutes=limit_minutes)
    recent_submissions = PendingReview.query.filter(
        PendingReview.ip_address == ip_address,
        PendingReview.created_at >= cutoff_time
    ).count()
    
    # Limit to 5 submissions per 10 minutes
    return recent_submissions < 5

@app.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        ip_address = request.remote_addr
        
        # Check rate limit
        if not check_rate_limit(ip_address):
            flash('You have submitted too many reviews. Please wait before trying again.', 'danger')
            captcha_question, captcha_answer = generate_captcha()
            session['captcha_answer'] = captcha_answer
            return render_template('submit_review.html', captcha_question=captcha_question)

        user_answer = request.form.get('captcha_answer')
        correct_answer = session.get('captcha_answer')
        
        if not user_answer or not correct_answer or user_answer != correct_answer:
            flash('Please solve the math problem correctly.', 'danger')
            captcha_question, captcha_answer = generate_captcha()
            session['captcha_answer'] = captcha_answer
            return render_template('submit_review.html', captcha_question=captcha_question)

        new_pending_review = PendingReview(
            text=request.form.get('review_text'),
            ip_address=ip_address
        )
        db.session.add(new_pending_review)
        db.session.commit()
        return render_template('thank_you.html')
    
    # Generate new CAPTCHA for GET request
    captcha_question, captcha_answer = generate_captcha()
    session['captcha_answer'] = captcha_answer
    return render_template('submit_review.html', captcha_question=captcha_question)

@app.route('/pending-reviews')
@login_required
def pending_reviews():
    pending = PendingReview.query.filter_by(status='pending').order_by(PendingReview.created_at.desc()).all()
    return render_template('pending_reviews.html', pending_reviews=pending)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 