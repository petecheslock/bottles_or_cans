from flask import abort
from app.models.review import Review, PendingReview
from app.extensions import db
import random

class ReviewService:
    SEED_VOTES_MIN = 10
    SEED_VOTES_MAX = 20
    VIRTUAL_VOTES = 10

    @staticmethod
    def get_random_review():
        """Get a random review from the database."""
        return db.session.execute(
            db.select(Review).order_by(db.func.random()).limit(1)
        ).scalar()

    @staticmethod
    def calculate_vote_percentages(review):
        """Calculate vote percentages for a review."""
        total_votes = review.votes_headphones + review.votes_wine + (ReviewService.VIRTUAL_VOTES * 2)
        headphones_percentage = int(((review.votes_headphones + ReviewService.VIRTUAL_VOTES) / total_votes) * 100)
        wine_percentage = int(((review.votes_wine + ReviewService.VIRTUAL_VOTES) / total_votes) * 100)
        
        return headphones_percentage, wine_percentage

    @staticmethod
    def add_vote(review_id, vote_type):
        """Add a vote to a review."""
        review = db.session.get(Review, review_id)
        if review:
            if vote_type == 'headphones':
                review.votes_headphones += 1
            elif vote_type == 'wine':
                review.votes_wine += 1
            db.session.commit()
        return review

    @staticmethod
    def create_pending_review(text, ip_address=None):
        """Create a new pending review."""
        review = PendingReview(text=text, ip_address=ip_address)
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def create_review(text):
        """Create a new approved review with seed votes."""
        review = Review(
            text=text,
            votes_headphones=random.randint(ReviewService.SEED_VOTES_MIN, ReviewService.SEED_VOTES_MAX),
            votes_wine=random.randint(ReviewService.SEED_VOTES_MIN, ReviewService.SEED_VOTES_MAX)
        )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def approve_pending_review(review_id):
        """Approve a pending review and create a new review."""
        pending = db.session.get(PendingReview, review_id)
        if not pending:
            abort(404)
        
        review = Review(
            text=pending.text,
            votes_headphones=random.randint(ReviewService.SEED_VOTES_MIN, ReviewService.SEED_VOTES_MAX),
            votes_wine=random.randint(ReviewService.SEED_VOTES_MIN, ReviewService.SEED_VOTES_MAX)
        )
        
        pending.status = 'approved'
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def reject_pending_review(review_id):
        """Reject a pending review."""
        review = db.session.get(PendingReview, review_id)
        if not review:
            abort(404)
            
        review.status = 'rejected'
        db.session.commit()
        return review

    @classmethod
    def get_all_reviews(cls):
        """Get all reviews from the database"""
        return db.session.execute(db.select(Review)).scalars().all()

    @staticmethod
    def get_review(review_id):
        """Get a review by ID using the new SQLAlchemy 2.0 style."""
        return db.session.get(Review, review_id)

    @staticmethod
    def reset_votes(review_id):
        """Reset votes for a review."""
        review = db.session.get(Review, review_id)
        if review:
            review.votes_headphones = 0
            review.votes_wine = 0
            db.session.commit()
            return True
        return False

    @classmethod
    def get_pending_reviews(cls):
        """Get all pending reviews from the database"""
        return PendingReview.query.filter_by(status='pending').order_by(PendingReview.created_at.desc()).all()

    @staticmethod
    def update_review(review_id, text):
        """Update a review's text."""
        review = db.session.get(Review, review_id)
        if review:
            review.text = text
            db.session.commit()
            return review
        return None 