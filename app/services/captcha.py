from flask import session, current_app
from captcha.image import ImageCaptcha
import base64, random
from io import BytesIO

class CaptchaService:
    ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Removed confusing chars
    
    @staticmethod
    def generate_captcha():
        """Generate a CAPTCHA image and text."""
        # Create image with custom settings
        image = ImageCaptcha(
            width=320,          # Increased width
            height=100,         # Increased height
            fonts=[             # Use more readable fonts if available
                'Arial',
                'Courier',
                'Times New Roman'
            ],
            font_sizes=(64, 72, 80)  # Larger font sizes for better readability
        )

        # Generate random text using allowed chars
        length = current_app.config['CAPTCHA_LENGTH']
        captcha_text = ''.join(random.choices(CaptchaService.ALLOWED_CHARS, k=length))
        
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