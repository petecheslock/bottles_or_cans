import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models.user import User
from app.extensions import db
from app import create_app
from app.config import TestingConfig
import time

def test_text_container_sizing(selenium_driver, flask_server):
    """Test that text containers size correctly for different review lengths"""
    driver = selenium_driver
    
    # First, create a test admin user in the test database
    with flask_server.ctx:
        # Clear existing users and ensure clean state
        User.query.delete()
        db.session.commit()
        
        # Create test admin user with proper admin privileges
        admin = User(
            username='test_admin',
            is_admin=True
        )
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
    
    # Wait for redirect to dashboard and verify we're logged in
    WebDriverWait(driver, 10).until(
        EC.url_to_be('http://localhost:5000/admin/dashboard')
    )
    
    # Now navigate to the test display page
    driver.get('http://localhost:5000/admin/test-text-display')
    
    # Wait for the page to load and all review containers to be present
    containers = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "text-container"))
    )
    
    # Expected heights from the debug info in the page
    expected_heights = {
        1: 33,   # Short review
        2: 98,   # Medium length review
        3: 163,  # Long review
        4: 325,  # Multi-paragraph review
        5: 130   # Heavy punctuation review
    }
    
    # Check each container's height
    for index, expected_height in expected_heights.items():
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, f'measureText{index}'))
        )
        actual_height = container.size['height']
        assert abs(actual_height - expected_height) <= 5, f"Container {index} height mismatch"

def is_text_overflowing(element):
    """Helper function to check if text is overflowing its container"""
    return element.value_of_css_property('overflow-y') == 'visible' and \
           element.rect['height'] < element.get_property('scrollHeight') 