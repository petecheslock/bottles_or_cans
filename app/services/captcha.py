from flask import session
from PIL import Image, ImageDraw, ImageFont
import base64, random, string, io

class CaptchaService:
    ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Removed confusing chars
    CAPTCHA_LENGTH = 5
    
    @staticmethod
    def generate_captcha():
        """Generate a captcha image and text"""
        # Create an image with a white background
        width = 320  # Made wider
        height = 100  # Made taller
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Generate random text using allowed chars
        text = ''.join(random.choices(CaptchaService.ALLOWED_CHARS, k=CaptchaService.CAPTCHA_LENGTH))
        
        try:
            # Increased font size significantly
            font = ImageFont.truetype('arial.ttf', 64)
        except IOError:
            font = ImageFont.load_default()
        
        # Position text more to the left
        text_width = font.getlength(text)
        text_x = 30  # Fixed left position instead of centering
        text_y = (height - 64) // 2  # Center vertically
        
        # Add text with a slight shadow for better readability
        draw.text((text_x+2, text_y+2), text, font=font, fill='gray')  # Shadow
        draw.text((text_x, text_y), text, font=font, fill='black')  # Main text
        
        # Add fewer, more subtle noise lines
        for _ in range(6):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill='lightgray', width=1)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_str = base64.b64encode(buffer.getvalue()).decode()
        
        return image_str, text

    @staticmethod
    def verify_captcha(user_answer, stored_answer):
        """Verify a CAPTCHA answer."""
        if not user_answer or not stored_answer:
            return False
        return user_answer.upper() == stored_answer.upper() 