from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from app.services.review import ReviewService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required
from app.services.rate_limit import RateLimitService

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if not session.get('seen_landing'):
        return render_template('landing.html')
    return redirect(url_for('main.play_game'))

@bp.route('/play')
def play_game():
    review = ReviewService.get_random_review()
    if review:
        headphones_percentage, wine_percentage = ReviewService.calculate_vote_percentages(review)
    else:
        headphones_percentage, wine_percentage = 0, 0
    
    return render_template('index.html', 
                         review=review, 
                         headphones_percentage=headphones_percentage,
                         wine_percentage=wine_percentage,
                         has_voted=False)

@bp.route('/start')
def start_game():
    session['seen_landing'] = True
    return redirect(url_for('main.play_game'))

@bp.route('/vote', methods=['POST'])
def vote():
    review_id = request.form.get('review_id')
    vote_type = request.form.get('vote_type')
    
    # Validate vote_type
    if vote_type not in ['headphones', 'wine']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    # Add vote and get updated review
    review = ReviewService.add_vote(review_id, vote_type)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    
    # Track voted reviews in session
    voted_reviews = session.get('voted_reviews', [])
    if review_id not in voted_reviews:
        voted_reviews.append(int(review_id))
        session['voted_reviews'] = voted_reviews
    
    headphones_percentage, wine_percentage = ReviewService.calculate_vote_percentages(review)
    
    return jsonify({
        'headphones_percentage': headphones_percentage,
        'wine_percentage': wine_percentage
    })

def get_client_ip():
    """Get client IP accounting for proxy headers"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@bp.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    """Submit a new review."""
    is_admin = session.get('logged_in', False)

    if request.method == 'POST':
        text = request.form.get('review_text', '').strip()
        
        # Validate review text
        if not text:
            flash('Review text is required', 'error')
            return render_template('submit_review.html', 
                                is_admin=is_admin), 400
        
        if len(text) > 500:  # Match the model's max length
            flash('Review text too long', 'error')
            return render_template('submit_review.html', 
                                is_admin=is_admin), 400

        # Check rate limit first
        if not is_admin and not RateLimitService.check_rate_limit(request.remote_addr):
            flash('Too many submissions. Please try again later.', 'error')
            # Generate new captcha for the form
            captcha_image, answer = CaptchaService.generate_captcha()
            session['captcha_answer'] = answer
            return render_template('submit_review.html', 
                                is_admin=is_admin,
                                captcha_image=captcha_image), 429
        
        if is_admin:
            # Admin submissions bypass captcha and go straight to approved reviews
            ReviewService.create_review(text)
            flash('Review added successfully!', 'success')
            return redirect(url_for('admin.manage_reviews'))
        else:
            # Regular user submissions need captcha and go to pending
            captcha_answer = request.form.get('captcha_answer')
            stored_answer = session.get('captcha_answer')
            
            if not CaptchaService.verify_captcha(captcha_answer, stored_answer):
                flash('Invalid captcha. Please try again.', 'error')
                return redirect(url_for('main.submit_review'))
            
            ReviewService.create_pending_review(text, request.remote_addr)
            return render_template('submit_thanks.html', is_admin=False)
    
    # GET request - show the form
    if not is_admin:
        captcha_image, answer = CaptchaService.generate_captcha()
        session['captcha_answer'] = answer
    else:
        captcha_image = None
    
    return render_template('submit_review.html', 
                         is_admin=is_admin,
                         captcha_image=captcha_image)

@bp.route('/refresh-captcha', methods=['POST'])
def refresh_captcha():
    """Generate a new captcha image"""
    if not session.get('logged_in'):  # Only for non-admin users
        captcha_image, captcha_text = CaptchaService.generate_captcha()
        session['captcha_text'] = captcha_text
        return jsonify({'captcha_image': captcha_image})
    return jsonify({'error': 'Unauthorized'}), 401 