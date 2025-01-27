from tests.base import BaseTestCase
from app.services.review import ReviewService
from datetime import datetime, timedelta, timezone

class TestReviewService(BaseTestCase):
    def test_create_review(self):
        review = ReviewService.create_review('Test service review')
        self.assertIsNotNone(review.id)
        self.assertEqual(review.text, 'Test service review')
        
    def test_get_random_review(self):
        self.create_test_review()
        random_review = ReviewService.get_random_review()
        self.assertIsNotNone(random_review)
        
    def test_vote_percentages(self):
        review = self.create_test_review()
        headphones_pct, wine_pct = ReviewService.calculate_vote_percentages(review)
        self.assertIsInstance(headphones_pct, int)
        self.assertIsInstance(wine_pct, int)
        
    def test_reviews_ordered_by_created_at(self):
        """Test that reviews are returned in correct order"""
        # Create reviews with different timestamps
        review1 = ReviewService.create_review('First review')
        review1.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        
        review2 = ReviewService.create_review('Second review')
        review2.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        review3 = ReviewService.create_review('Third review')
        # review3 keeps current timestamp
        
        self.db.session.commit()  # Save the timestamp changes
        
        # Get all reviews
        reviews = ReviewService.get_all_reviews()
        
        # Verify order (newest first)
        self.assertEqual(reviews[0].id, review3.id)
        self.assertEqual(reviews[1].id, review2.id)
        self.assertEqual(reviews[2].id, review1.id)
        
        # Verify timestamps are in descending order
        self.assertTrue(reviews[0].created_at > reviews[1].created_at)
        self.assertTrue(reviews[1].created_at > reviews[2].created_at) 