import secrets
from functools import wraps
from flask import request, jsonify

def generate_api_key(length=32):
    """
    Generates a cryptographically secure, URL-safe API key.
    
    Args:
        length (int): The number of bytes of randomness to use.
                      The resulting key will be longer due to hex encoding.
                      
    Returns:
        str: A new, securely generated API key.
    """
    return secrets.token_hex(length)

def create_security_decorator(config):
    """
    Creates a decorator to secure routes with API key and IP whitelisting.
    This factory pattern allows injecting the config dependency, making it
    more modular and testable.
    """
    def security_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check API Key from request header
            api_key = request.headers.get('X-API-Key')
            if not api_key or api_key != config.get('api_key'):
                return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

            whitelist = config.get('whitelist', [])
            if whitelist:
                client_ip = request.remote_addr
                if client_ip not in whitelist:
                    return jsonify({"error": f"Forbidden: IP {client_ip} not whitelisted"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return security_decorator