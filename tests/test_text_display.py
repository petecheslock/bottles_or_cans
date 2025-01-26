import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import app, db, User
import time

def test_text_container_sizing(selenium_driver, flask_server):
    """Test that text containers size correctly for different review lengths"""
    driver = selenium_driver
    
    # First, create a test admin user in the test database
    with flask_server.ctx:
        # Clear existing users
        User.query.delete()
        
        # Create test admin user
        admin = User(username='test_admin', is_admin=True)
        admin.set_password('test_password')
        db.session.add(admin)
        db.session.commit()
    
    # Login first
    driver.get('http://localhost:5000/admin/login')
    
    # Wait for login form and fill it
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_input = driver.find_element(By.NAME, "password")
    
    username_input.send_keys('test_admin')
    password_input.send_keys('test_password')
    password_input.submit()
    
    # Now navigate to the test display page
    driver.get('http://localhost:5000/admin/test-text-display')
    
    # Wait for the page to load and all review containers to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "animate__fadeIn"))
    )
    
    # Expected heights from the debug info in the page
    expected_heights = {
        1: 33,   # Short review
        2: 98,   # Medium length review
        3: 163,  # Long review
        4: 325,  # Multi-paragraph review
        5: 130   # Heavy punctuation review
    }
    
    for i in range(1, 6):
        try:
            # Get the text container
            text_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f'reviewText{i}'))
            )
            
            # Get the actual height from the style attribute
            style_height = text_container.get_attribute('style')
            actual_height = int(style_height.split('height: ')[1].split('px')[0])
            
            # Print debug information
            print(f"\nTesting container {i}:")
            print(f"Expected height: {expected_heights[i]}px")
            print(f"Actual height: {actual_height}px")
            
            # Assert the height matches expected
            assert abs(actual_height - expected_heights[i]) <= 1, \
                f"Height mismatch for container {i}: expected={expected_heights[i]}, actual={actual_height}"
            
            # Assert that text is not overflowing
            assert not is_text_overflowing(text_container), \
                f"Text is overflowing in container {i}"
            
        except Exception as e:
            print(f"\nError testing container {i}:")
            print(f"Page source: {driver.page_source}")
            raise e

def is_text_overflowing(element):
    """Helper function to check if text is overflowing its container"""
    return element.value_of_css_property('overflow-y') == 'visible' and \
           element.rect['height'] < element.get_property('scrollHeight') 