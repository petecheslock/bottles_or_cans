from tests.base import BaseTestCase
from app.services.review import ReviewService

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