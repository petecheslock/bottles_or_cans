import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
import threading
from werkzeug.serving import make_server

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

@pytest.fixture
def flask_server():
    # Configure Flask for testing
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    
    # Create all tables
    with app.app_context():
        db.create_all()
    
    # Start the server
    server = ServerThread(app)
    server.start()
    yield server
    
    # Cleanup
    with app.app_context():
        db.drop_all()
    
    # Shutdown the server
    server.shutdown()
    server.join()

@pytest.fixture
def selenium_driver(flask_server):
    # Setup Chrome options for testing
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Run in headless mode (no GUI)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Create and return the driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.implicitly_wait(10)
    
    yield driver
    
    # Cleanup after test
    driver.quit() 