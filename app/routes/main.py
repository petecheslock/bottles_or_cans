from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from app.services.review import ReviewService
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

@bp.route('/submit-review', methods=['POST'])
def submit_review():
    """Handle submission of a new review"""
    review_text = request.form.get('review_text')
    captcha_answer = request.form.get('captcha_answer')
    
    # If user is logged in as admin, bypass captcha and rate limiting
    if session.get('logged_in'):
        if review_text:
            ReviewService.create_review(review_text)
            flash('Review added successfully!', 'success')
            return redirect(url_for('admin.manage_reviews'))
    else:
        # Handle non-admin submission with captcha and rate limiting
        if review_text and captcha_answer:
            ReviewService.create_pending_review(review_text)
            flash('Review submitted successfully!', 'success')
    return redirect(url_for('main.play_game')) 