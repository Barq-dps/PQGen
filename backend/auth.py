"""
User Authentication and Management with Firestore Integration
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from functools import wraps
from flask import request, jsonify, session

# Import database functions
from database import (
    create_user, get_user_by_email, get_user_by_id, 
    update_user_login, is_database_available
)

logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

class AuthManager:
    """Handles user authentication and session management"""
    
    def __init__(self):
        self.users = {}  # Fallback in-memory storage when Firestore is not available
        
    async def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user
        Returns: (success, message, user_data)
        """
        try:
            # Validate input
            validation_errors = self._validate_registration_data(username, email, password)
            if validation_errors:
                return False, validation_errors, None
            
            # Check if user already exists
            if is_database_available():
                existing_user = await get_user_by_email(email)
                if existing_user:
                    return False, "Email already registered", None
            else:
                # Fallback: check in-memory storage
                if any(user.get('email') == email for user in self.users.values()):
                    return False, "Email already registered", None
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user data
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'is_active': True
            }
            
            # Save to database
            if is_database_available():
                user_id = await create_user(user_data)
                if user_id:
                    user_data['id'] = user_id
                    # Remove password hash from returned data
                    safe_user_data = {k: v for k, v in user_data.items() if k != 'password_hash'}
                    return True, "User registered successfully", safe_user_data
                else:
                    return False, "Failed to create user account", None
            else:
                # Fallback: store in memory
                user_id = f"user_{len(self.users) + 1}"
                user_data['id'] = user_id
                user_data['created_at'] = datetime.now(timezone.utc)
                user_data['last_login'] = None
                user_data['stats'] = {
                    'total_challenges': 0,
                    'completed_challenges': 0,
                    'success_rate': 0.0,
                    'current_streak': 0,
                    'best_streak': 0,
                    'total_score': 0
                }
                self.users[user_id] = user_data
                safe_user_data = {k: v for k, v in user_data.items() if k != 'password_hash'}
                logger.warning("Using in-memory storage - data will be lost on restart")
                return True, "User registered successfully (development mode)", safe_user_data
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "Registration failed due to server error", None
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user login
        Returns: (success, message, user_data)
        """
        try:
            # Get user from database
            if is_database_available():
                user = await get_user_by_email(email)
            else:
                # Fallback: check in-memory storage
                user = None
                for user_data in self.users.values():
                    if user_data.get('email') == email:
                        user = user_data
                        break
            
            if not user:
                return False, "Invalid email or password", None
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return False, "Invalid email or password", None
            
            # Check if user is active
            if not user.get('is_active', True):
                return False, "Account is deactivated", None
            
            # Update last login
            if is_database_available():
                await update_user_login(user['id'])
            else:
                user['last_login'] = datetime.now(timezone.utc)
            
            # Remove password hash from returned data
            safe_user_data = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return True, "Login successful", safe_user_data
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, "Authentication failed due to server error", None
    
    def _validate_registration_data(self, username: str, email: str, password: str) -> Optional[str]:
        """Validate registration data"""
        errors = []
        
        # Username validation
        if not username or len(username.strip()) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if len(username) > 50:
            errors.append("Username must be less than 50 characters")
        
        # Email validation (basic)
        if not email or '@' not in email or '.' not in email:
            errors.append("Please provide a valid email address")
        
        # Password validation
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        
        return "; ".join(errors) if errors else None
    
    def generate_jwt_token(self, user_data: Dict) -> str:
        """Generate JWT token for user"""
        try:
            payload = {
                'user_id': user_data['id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
                'iat': datetime.now(timezone.utc)
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        try:
            if is_database_available():
                user = await get_user_by_id(user_id)
            else:
                user = self.users.get(user_id)
            
            if user:
                # Remove sensitive data
                profile = {k: v for k, v in user.items() if k != 'password_hash'}
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Profile retrieval error: {e}")
            return None

# Global auth manager instance
auth_manager = AuthManager()

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check for token in session (fallback)
        if not token:
            token = session.get('auth_token')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        payload = auth_manager.verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict]:
    """Get current authenticated user from request context"""
    return getattr(request, 'current_user', None)

# Convenience functions
async def register_user(username: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Register a new user"""
    return await auth_manager.register_user(username, email, password)

async def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticate user login"""
    return await auth_manager.authenticate_user(email, password)

def generate_jwt_token(user_data: Dict) -> str:
    """Generate JWT token"""
    return auth_manager.generate_jwt_token(user_data)

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    return auth_manager.verify_jwt_token(token)

async def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile"""
    return await auth_manager.get_user_profile(user_id)

def init_firebase() -> bool:
    ok = is_database_available()
    if ok:
        logger.info("Firebase is up ✅")
    else:
        logger.warning("Firebase not initialized, using dev fallback ⚠️")
    return ok

