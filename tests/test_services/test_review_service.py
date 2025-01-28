from tests.base import BaseTestCase
from app.services.review import ReviewService
from datetime import datetime, timedelta, timezone

class TestReviewService(BaseTestCase):
    def test_create_review(self):
        review = ReviewService.create_review('Test service review')
        self.assertIsNotNone(review.id)
        self.assertEqual(review.text, 'Test service review')
        
    def test_get_random_review(self):
        """Test getting a random review"""
        self.create_test_review()
        random_review = ReviewService.get_random_review(voted_reviews=[])
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

    def test_add_vote_invalid_type(self):
        """Test adding vote with invalid vote type"""
        review = self.create_test_review()
        initial_headphones = review.votes_headphones
        initial_wine = review.votes_wine
        
        result = ReviewService.add_vote(review.id, 'invalid_type')
        
        # Votes should remain unchanged
        self.assertEqual(review.votes_headphones, initial_headphones)
        self.assertEqual(review.votes_wine, initial_wine)

    def test_add_vote_nonexistent_review(self):
        """Test adding vote to non-existent review"""
        result = ReviewService.add_vote(999, 'headphones')
        self.assertIsNone(result)

    def test_pending_review_workflow(self):
        """Test the complete pending review workflow"""
        # Create pending review
        pending = ReviewService.create_pending_review('Test pending', '127.0.0.1')
        self.assertEqual(pending.status, 'pending')
        self.assertEqual(pending.ip_address, '127.0.0.1')
        
        # Approve the review
        approved = ReviewService.approve_pending_review(pending.id)
        self.assertIsNotNone(approved)
        self.assertEqual(approved.text, 'Test pending')
        self.assertEqual(pending.status, 'approved')
        
        # Try to approve non-existent review
        with self.assertRaises(Exception):  # Should raise 404
            ReviewService.approve_pending_review(999)
        
        # Create another pending review for rejection
        pending2 = ReviewService.create_pending_review('Test reject')
        
        # Reject the review
        rejected = ReviewService.reject_pending_review(pending2.id)
        self.assertEqual(rejected.status, 'rejected')
        
        # Try to reject non-existent review
        with self.assertRaises(Exception):  # Should raise 404
            ReviewService.reject_pending_review(999)

    def test_get_pending_reviews(self):
        """Test getting pending reviews"""
        # Create mix of pending and rejected reviews with different timestamps
        pending1 = ReviewService.create_pending_review('Pending 1')
        pending1.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        pending2 = ReviewService.create_pending_review('Pending 2')
        # pending2 keeps current timestamp
        
        rejected = ReviewService.create_pending_review('Rejected')
        ReviewService.reject_pending_review(rejected.id)
        
        self.db.session.commit()  # Save the timestamp changes
        
        # Get pending reviews
        pending_reviews = ReviewService.get_pending_reviews()
        
        # Verify only pending reviews are returned
        self.assertEqual(len(pending_reviews), 2)
        self.assertTrue(all(r.status == 'pending' for r in pending_reviews))
        
        # Verify order (newest first)
        self.assertEqual(pending_reviews[0].id, pending2.id)
        self.assertEqual(pending_reviews[1].id, pending1.id)
        
        # Verify timestamps are in descending order
        self.assertTrue(pending_reviews[0].created_at > pending_reviews[1].created_at)

    def test_reset_votes(self):
        """Test resetting votes on a review"""
        review = self.create_test_review()
        review.votes_headphones = 5
        review.votes_wine = 3
        self.db.session.commit()
        
        # Reset votes
        success = ReviewService.reset_votes(review.id)
        self.assertTrue(success)
        
        # Verify votes were reset
        self.assertEqual(review.votes_headphones, 0)
        self.assertEqual(review.votes_wine, 0)
        
        # Try resetting non-existent review
        success = ReviewService.reset_votes(999)
        self.assertFalse(success) 