from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from app.models.review import Review, PendingReview
from app.models.user import User
from app.models.rate_limit import RateLimit
from app.utils.decorators import login_required
from app.extensions import db
import random
from app.services.review import ReviewService
from app.services.rate_limit import RateLimitService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

SEED_VOTES_MIN = 10
SEED_VOTES_MAX = 20

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/manage-reviews')
@login_required
def manage_reviews():
    reviews = ReviewService.get_all_reviews()
    return render_template('manage_reviews.html', reviews=reviews)

@admin_bp.route('/delete-review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    if ReviewService.delete_review(review_id):
        flash('Review deleted successfully!', 'success')
        return redirect(url_for('admin.manage_reviews'))
    else:
        abort(404)  # Return 404 when review doesn't exist

@admin_bp.route('/edit-review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    if request.method == 'POST':
        text = request.form.get('review_text')
        ReviewService.update_review(review_id, text)
        flash('Review updated successfully!', 'success')
        return redirect(url_for('admin.manage_reviews'))
    
    review = ReviewService.get_review(review_id)
    return render_template('edit_review.html', review=review)

@admin_bp.route('/pending-reviews')
@login_required
def pending_reviews():
    pending = ReviewService.get_pending_reviews()
    return render_template('pending_reviews.html', pending_reviews=pending)

@admin_bp.route('/approve-pending/<int:review_id>', methods=['POST'])
@login_required
def approve_pending(review_id):
    """Approve a pending review"""
    ReviewService.approve_pending_review(review_id)
    flash('Review approved successfully!', 'success')
    return redirect(url_for('admin.pending_reviews'))

@admin_bp.route('/reject-pending/<int:review_id>', methods=['POST'])
@login_required
def reject_pending(review_id):
    """Reject a pending review"""
    ReviewService.reject_pending_review(review_id)
    flash('Review rejected successfully!', 'success')
    return redirect(url_for('admin.pending_reviews'))

@admin_bp.route('/rate-limits', methods=['GET', 'POST'])
@login_required
def manage_rate_limits():
    if request.method == 'POST':
        ip_address = request.form.get('ip_address')
        action = request.form.get('action')
        
        if action == 'unblock':
            RateLimitService.unblock_ip(ip_address)
            flash('IP address unblocked successfully.', 'success')
        elif action == 'block':
            RateLimitService.block_ip(ip_address)
            flash('IP address blocked successfully.', 'success')
        elif action == 'delete':
            if RateLimitService.delete_rate_limit(ip_address):
                flash('Rate limit record deleted successfully.', 'success')
            else:
                flash('Rate limit record not found.', 'danger')
    
    rate_limits = RateLimitService.get_all_rate_limits()
    return render_template('rate_limits.html', rate_limits=rate_limits)

@admin_bp.route('/users')
@login_required
def manage_users():
    users = db.session.execute(db.select(User)).scalars().all()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/test-text-display')
@login_required
def test_text_display():
    """Display actual reviews to test text container sizing"""
    # Get all approved reviews from the database
    reviews = ReviewService.get_all_reviews()
    return render_template('test_text_display.html', reviews=reviews)

@admin_bp.route('/reset-votes/<int:review_id>', methods=['POST'])
@login_required
def reset_votes(review_id):
    """Reset votes for a specific review"""
    if ReviewService.reset_votes(review_id):
        flash('Votes reset successfully!', 'success')
    else:
        flash('Review not found.', 'error')
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/reset-all-votes', methods=['POST'])
@login_required
def reset_all_votes():
    """Reset votes for all reviews"""
    try:
        reviews = db.session.execute(db.select(Review)).scalars().all()
        for review in reviews:
            review.votes_headphones = 0
            review.votes_wine = 0
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/seed-reviews', methods=['POST'])
@login_required
def seed_reviews():
    """Seed reviews with random vote counts"""
    reviews = Review.query.all()
    for review in reviews:
        # Generate random vote counts between 0 and 100
        review.votes_headphones = random.randint(0, 100)
        review.votes_wine = random.randint(0, 100)
    
    db.session.commit()
    flash('Reviews seeded successfully!', 'success')
    return redirect(url_for('admin.manage_reviews')) 