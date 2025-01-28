from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from app.services.review import ReviewService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required
from app.services.rate_limit import RateLimitService
from app.services.user import UserService
from flask import current_app

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page."""
    # If user hasn't seen landing page and is not logged in, show it first
    if not session.get('seen_landing') and not session.get('logged_in'):
        return render_template('landing.html')
        
    # Otherwise show the game
    review = ReviewService.get_random_review()
    if review:
        headphones_percentage, wine_percentage = ReviewService.calculate_vote_percentages(review)
    else:
        headphones_percentage = wine_percentage = 0
        
    return render_template('index.html', 
                         review=review,
                         headphones_percentage=headphones_percentage,
                         wine_percentage=wine_percentage,
                         has_voted=False)

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
    """Mark the landing page as seen and start the game"""
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
        
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Validate review text
        if not text:
            if is_ajax:
                return jsonify({'success': False, 'error': 'Review text is required'}), 400
            flash('Review text is required', 'error')
            return render_template('submit_review.html', is_admin=is_admin), 400
        
        if len(text) > current_app.config['MAX_REVIEW_LENGTH']:
            if is_ajax:
                return jsonify({'success': False, 'error': 'Review text too long'}), 400
            flash('Review text too long', 'error')
            return render_template('submit_review.html', is_admin=is_admin), 400

        # Check rate limit using client IP from X-Forwarded-For
        client_ip = get_client_ip()
        if not is_admin and not RateLimitService.check_rate_limit(client_ip):
            if is_ajax:
                return jsonify({'success': False, 'error': 'Too many submissions. Please try again later.'}), 429
            flash('Too many submissions. Please try again later.', 'error')
            return render_template('submit_review.html', is_admin=is_admin), 429
        
        if is_admin:
            # Admin submissions bypass captcha
            ReviewService.create_review(text)
            if is_ajax:
                return jsonify({
                    'success': True,
                    'redirect_url': url_for('admin.manage_reviews')
                })
            flash('Review added successfully!', 'success')
            return redirect(url_for('admin.manage_reviews'))
        else:
            # Regular user submissions need captcha
            captcha_answer = request.form.get('captcha_answer')
            stored_answer = session.get('captcha_answer')
            
            if not CaptchaService.verify_captcha(captcha_answer, stored_answer):
                if is_ajax:
                    return jsonify({'success': False, 'error': 'Invalid captcha. Please try again.'})
                flash('Invalid captcha. Please try again.', 'error')
                return redirect(url_for('main.submit_review'))
            
            # Use client IP from X-Forwarded-For for pending review
            ReviewService.create_pending_review(text, client_ip)
            if is_ajax:
                return jsonify({
                    'success': True,
                    'redirect_url': url_for('main.thank_you')
                })
            return redirect(url_for('main.thank_you'))

    # GET request - show the form
    if not is_admin:
        captcha_service = CaptchaService()
        captcha_image, answer = captcha_service.generate_captcha()
        session['captcha_answer'] = answer
    else:
        captcha_image = None
    
    return render_template('submit_review.html', 
                         is_admin=is_admin,
                         captcha_image=captcha_image)

@bp.route('/thank-you')
def thank_you():
    """Thank you page after submitting a review."""
    return render_template('submit_thanks.html', is_admin=False)

@bp.route('/refresh-captcha', methods=['POST'])
def refresh_captcha():
    """Generate a new captcha image"""
    if not session.get('logged_in'):
        captcha_service = CaptchaService()
        captcha_image, captcha_text = captcha_service.generate_captcha()
        session['captcha_answer'] = captcha_text
        return jsonify({'captcha_image': captcha_image})
    return jsonify({'error': 'Unauthorized'}), 401

@bp.route('/captcha')
def get_captcha():
    captcha_service = CaptchaService()
    image_data, answer = captcha_service.generate_captcha()
    session['captcha_answer'] = answer
    return jsonify({'image': image_data, 'answer': answer}) 