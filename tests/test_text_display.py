import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models.user import User
from app.models.review import Review
from app.extensions import db
from app import create_app
from app.config import TestingConfig
import time

def test_text_container_sizing(selenium_driver, flask_server):
    """Test that text containers size correctly for different review lengths"""
    driver = selenium_driver
    
    # First, create a test admin user and sample reviews in the test database
    with flask_server.ctx:
        # Clear existing data
        User.query.delete()
        Review.query.delete()
        db.session.commit()
        
        # Create test admin user
        admin = User(username='test_admin', is_admin=True)
        admin.set_password('test_password')
        db.session.add(admin)

        # Create sample reviews of varying lengths from the backup
        sample_reviews = [
            # Short review
            Review(text="Silky and balanced, with a graceful interplay of richness and precision. The subtle undertones add depth, while the finish lingers elegantly, leaving a memorable impression."),
            # Medium review
            Review(text="The experience opens with pristine clarity before embracing darker, more mysterious elements. Warmth radiates from its core while maintaining exceptional poise throughout."),
            # Long review
            Review(text="Rich and full-bodied, it offers a luxurious experience with layers of complexity. Subtle hints of warmth and depth reveal themselves gradually, creating a lasting impression that's both refined and versatile. Ideal for an evening of quiet indulgence."),
            # Multi-paragraph review
            Review(text="The presentation is quite balanced, featuring a dark, velvety character that feels rich without being overwhelming. The bass response is deep and authoritative but never muddy. There are subtle textures throughout that reveal themselves with time, and while the profile might be too intense for beginners, purists will appreciate its complexity."),
            # Medium-long review
            Review(text="Initial boldness mellows into honeyed subtleties, while deeper currents provide steady grounding. The experience unfolds patiently, rewarding those who take time to explore its nuances.")
        ]
        
        for review in sample_reviews:
            db.session.add(review)
        db.session.commit()

    # Login process remains the same
    driver.get('http://localhost:5000/admin/login')
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys('test_admin')
    password_input.send_keys('test_password')
    password_input.submit()
    
    # Wait for redirect and navigate to test page
    WebDriverWait(driver, 10).until(
        EC.url_to_be('http://localhost:5000/admin/dashboard')
    )
    driver.get('http://localhost:5000/admin/test-text-display')
    
    # Wait for containers to be present
    containers = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "text-container"))
    )
    
    # Get all container heights
    container_heights = {}
    for index in range(1, 6):
        height_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, f'containerHeight{index}'))
        )
        container_heights[index] = int(height_element.text.replace('px', ''))

    # Print heights for debugging (moved to before assertions)
    print("\nContainer heights:")
    for index, height in container_heights.items():
        print(f"Container {index}: {height}px")
    
    # Test assertions about relative heights
    # 1. Short, Medium, and Medium-long reviews should be within reasonable range
    assert abs(container_heights[1] - container_heights[2]) <= 35, "Short and medium reviews should be within reasonable height range"
    assert abs(container_heights[2] - container_heights[5]) <= 35, "Medium and medium-long reviews should be within reasonable height range"
    
    # 2. Long review should be taller than medium reviews
    assert container_heights[3] > container_heights[2], "Long review should be taller than medium review"
    
    # 3. Multi-paragraph review should be the tallest
    assert container_heights[4] > container_heights[3], "Multi-paragraph review should be the tallest"
    
    # 4. All containers should have reasonable minimum heights
    for index, height in container_heights.items():
        assert height >= 100, f"Container {index} height ({height}px) is too small"
        assert height <= 300, f"Container {index} height ({height}px) is too large"

def is_text_overflowing(element):
    """Helper function to check if text is overflowing its container"""
    return element.value_of_css_property('overflow-y') == 'visible' and \
           element.rect['height'] < element.get_property('scrollHeight') 