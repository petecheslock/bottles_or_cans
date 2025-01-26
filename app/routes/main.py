from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from app.services.review import ReviewService
from app.services.captcha import CaptchaService
from app.utils.decorators import login_required

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
    
    review = ReviewService.add_vote(review_id, vote_type)
    
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

@bp.route('/submit-review', methods=['GET', 'POST'])
def submit_review():
    """Handle submission of a new review"""
    # For GET requests, display the form
    if request.method == 'GET':
        # Generate captcha if user is not admin
        if not session.get('logged_in'):
            captcha_image, captcha_text = CaptchaService.generate_captcha()
            session['captcha_text'] = captcha_text
            return render_template('submit_review.html', 
                                 captcha_image=captcha_image,
                                 is_admin=False)
        return render_template('submit_review.html', is_admin=True)

    # For POST requests, handle the submission
    review_text = request.form.get('review_text')
    captcha_answer = request.form.get('captcha_answer')
    
    # If user is logged in as admin, bypass captcha
    if session.get('logged_in'):
        if review_text:
            ReviewService.create_review(review_text)
            flash('Review added successfully!', 'success')
            return redirect(url_for('admin.manage_reviews'))  # Admin stays in admin area
    else:
        # Handle non-admin submission
        if not review_text:
            flash('Review text is required', 'error')
            return redirect(url_for('main.submit_review'))
            
        if not captcha_answer:
            flash('Please complete the captcha', 'error')
            return redirect(url_for('main.submit_review'))
            
        # Verify captcha
        stored_captcha = session.get('captcha_text')
        if not stored_captcha or captcha_answer.lower() != stored_captcha.lower():
            flash('Invalid captcha answer', 'error')
            return redirect(url_for('main.submit_review'))
            
        # Clear used captcha
        session.pop('captcha_text', None)
        
        ReviewService.create_pending_review(review_text)
        return render_template('submit_thanks.html', is_admin=False)  # Only regular users see thank you page
    
    return redirect(url_for('main.submit_review'))

@bp.route('/refresh-captcha', methods=['POST'])
def refresh_captcha():
    """Generate a new captcha image"""
    if not session.get('logged_in'):  # Only for non-admin users
        captcha_image, captcha_text = CaptchaService.generate_captcha()
        session['captcha_text'] = captcha_text
        return jsonify({'captcha_image': captcha_image})
    return jsonify({'error': 'Unauthorized'}), 401 