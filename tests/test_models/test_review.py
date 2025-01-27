from tests.base import BaseTestCase
from app.models.review import Review, PendingReview
from datetime import datetime, timezone

class TestReviewModel(BaseTestCase):
    def test_review_creation(self):
        """Test Review model creation and defaults"""
        review = Review(text="Test review")
        self.db.session.add(review)
        self.db.session.commit()
        
        self.assertEqual(review.text, "Test review")
        self.assertEqual(review.votes_headphones, 0)  # Default value from model
        self.assertEqual(review.votes_wine, 0)  # Default value from model
        self.assertIsInstance(review.created_at, datetime)
        self.assertTrue(review.is_active)
        
    def test_review_repr(self):
        """Test Review string representation"""
        review = Review(text="A test review that is longer than thirty characters")
        self.assertEqual(repr(review), '<Review A test review that is longer t...>')  # Model truncates at 30 chars
        
    def test_vote_calculations(self):
        """Test vote calculation properties"""
        review = Review(
            text="Test review",
            votes_headphones=60,
            votes_wine=40
        )
        self.db.session.add(review)  # Need to add to session to initialize defaults
        self.db.session.commit()
        
        self.assertEqual(review.total_votes, 100)
        self.assertEqual(review.headphones_percentage, 60.0)
        self.assertEqual(review.wine_percentage, 40.0)
        
    def test_pending_review(self):
        """Test PendingReview model"""
        pending = PendingReview(
            text="Pending review",
            ip_address="127.0.0.1",
            status="pending"
        )
        self.db.session.add(pending)
        self.db.session.commit()
        
        self.assertEqual(pending.text, "Pending review")
        self.assertEqual(pending.ip_address, "127.0.0.1")
        self.assertEqual(pending.status, "pending")
        self.assertIsInstance(pending.created_at, datetime)
        
        # Test string representation
        self.assertEqual(repr(pending), '<PendingReview Pending review...>')
        
        # Test approve method
        approved = pending.approve()
        self.assertIsInstance(approved, Review)
        self.assertEqual(approved.text, "Pending review")
        self.assertTrue(approved.is_active) 