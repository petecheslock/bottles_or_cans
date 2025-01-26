from flask import session
from captcha.image import ImageCaptcha
import base64, random
from io import BytesIO

class CaptchaService:
    ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Removed confusing chars
    CAPTCHA_LENGTH = 5
    
    @staticmethod
    def generate_captcha():
        """Generate a CAPTCHA image and text."""
        image = ImageCaptcha(
            width=280,
            height=90,
            fonts=[
                'Arial',
                'Courier',
                'Times New Roman'
            ],
            font_sizes=(46, 58, 68)
        )

        captcha_text = ''.join(random.choices(CaptchaService.ALLOWED_CHARS, k=CaptchaService.CAPTCHA_LENGTH))
        
        # Generate image
        buffered = BytesIO()
        image.write(captcha_text, buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return captcha_text, img_str

    @staticmethod
    def verify_captcha(user_answer, stored_answer):
        """Verify a CAPTCHA answer."""
        if not user_answer or not stored_answer:
            return False
        return user_answer.upper() == stored_answer.upper() 