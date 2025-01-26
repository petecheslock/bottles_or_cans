from functools import wraps

def rate_limit_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_address = request.remote_addr
        
        if not RateLimitService.check_rate_limit(ip_address):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }), 429
            
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/reviews', methods=['POST'])
@rate_limit_decorator
def create_review():
    # Your existing API logic
    ... 