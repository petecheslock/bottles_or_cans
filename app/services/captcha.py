from flask import session, current_app
from captcha.image import ImageCaptcha
import base64, random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import string
import io
import os

class CaptchaService:
    ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Removed confusing chars
    
    def __init__(self):
        # Get the absolute path to the fonts directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(current_dir, '..', 'static', 'fonts')
        self.font_path = os.path.join(fonts_dir, 'OpenSans-Regular.ttf')

    def generate_captcha(self):
        """Generate a CAPTCHA image and text."""
        # Create image with custom settings
        image = ImageCaptcha(
            width=320,          # Increased width
            height=100,         # Increased height
            fonts=[self.font_path],  # Use our downloaded font
            font_sizes=(64, 72, 80)  # Larger font sizes for better readability
        )

        # Generate random text using allowed chars
        length = current_app.config['CAPTCHA_LENGTH']
        captcha_text = ''.join(random.choices(self.ALLOWED_CHARS, k=length))
        
        # Generate image
        buffered = BytesIO()
        image.write(captcha_text, buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str, captcha_text

    @staticmethod
    def verify_captcha(user_answer, stored_answer):
        """Verify a CAPTCHA answer."""
        if not user_answer or not stored_answer:
            return False
        return user_answer.upper() == stored_answer.upper()