"""
Authentication Service for OAuth and Session Management
"""
import logging
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests
from app.config import Config

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        self.config = Config()
        self.sessions = {}  # In-memory session store (use Redis in production)
        
    def authenticate(self, authorization_code: str) -> bool:
        """
        Authenticate user with Breeze OAuth
        
        Args:
            authorization_code: OAuth authorization code from callback
            
        Returns:
            True if authentication successful
        """
        try:
            # Exchange authorization code for access token
            token_response = self._exchange_code_for_token(authorization_code)
            
            if token_response:
                # Store session information
                session_id = self._create_session(token_response)
                return session_id is not None
                
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _exchange_code_for_token(self, authorization_code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        try:
            # This would typically involve making a request to Breeze OAuth endpoint
            # For now, we'll simulate the token exchange
            
            # In production, you would make a request like:
            # token_url = "https://api.icicidirect.com/oauth/token"
            # data = {
            #     'grant_type': 'authorization_code',
            #     'code': authorization_code,
            #     'client_id': self.config.BREEZE_API_KEY,
            #     'client_secret': self.config.BREEZE_SECRET_KEY,
            #     'redirect_uri': 'your_redirect_uri'
            # }
            # response = requests.post(token_url, data=data)
            
            # Simulated token response
            token_response = {
                'access_token': f"mock_access_token_{authorization_code}",
                'token_type': 'Bearer',
                'expires_in': 3600,
                'refresh_token': f"mock_refresh_token_{authorization_code}",
                'scope': 'read write'
            }
            
            return token_response
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
    
    def _create_session(self, token_data: Dict) -> Optional[str]:
        """Create authenticated session"""
        try:
            session_id = secrets.token_urlsafe(32)
            
            session_data = {
                'session_id': session_id,
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600)),
                'created_at': datetime.now(),
                'user_id': self.config.BREEZE_USER_ID
            }
            
            self.sessions[session_id] = session_data
            
            logger.info(f"Session created: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is active and not expired"""
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # Check if token is expired
            if datetime.now() > session['expires_at']:
                # Try to refresh token
                if self._refresh_token(session_id):
                    return True
                else:
                    # Remove expired session
                    del self.sessions[session_id]
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def _refresh_token(self, session_id: str) -> bool:
        """Refresh expired access token"""
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            refresh_token = session.get('refresh_token')
            
            if not refresh_token:
                return False
            
            # Make refresh token request
            # refresh_url = "https://api.icicidirect.com/oauth/refresh"
            # data = {
            #     'grant_type': 'refresh_token',
            #     'refresh_token': refresh_token,
            #     'client_id': self.config.BREEZE_API_KEY,
            #     'client_secret': self.config.BREEZE_SECRET_KEY
            # }
            # response = requests.post(refresh_url, data=data)
            
            # Simulated refresh response
            new_token_data = {
                'access_token': f"refreshed_token_{session_id}",
                'token_type': 'Bearer',
                'expires_in': 3600,
                'refresh_token': refresh_token
            }
            
            # Update session with new token
            session['access_token'] = new_token_data['access_token']
            session['expires_at'] = datetime.now() + timedelta(seconds=new_token_data['expires_in'])
            
            logger.info(f"Token refreshed for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        try:
            if session_id in self.sessions and self.validate_session(session_id):
                session = self.sessions[session_id].copy()
                # Remove sensitive information
                session.pop('access_token', None)
                session.pop('refresh_token', None)
                return session
            return None
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    def logout(self, session_id: str) -> bool:
        """Logout and invalidate session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session logged out: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error logging out: {e}")
            return False
    
    def create_jwt_token(self, user_data: Dict) -> str:
        """Create JWT token for API authentication"""
        try:
            payload = {
                'user_id': user_data.get('user_id'),
                'session_id': user_data.get('session_id'),
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow(),
                'iss': 'MyBreezeApp'
            }
            
            token = jwt.encode(payload, self.config.SECRET_KEY, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT token: {e}")
            return ""
    
    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=['HS256'])
            
            # Validate session still exists
            session_id = payload.get('session_id')
            if session_id and self.validate_session(session_id):
                return payload
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return None
    
    def get_oauth_url(self, redirect_uri: str) -> str:
        """Generate OAuth authorization URL"""
        try:
            # Generate state parameter for security
            state = secrets.token_urlsafe(32)
            
            # In production, this would be the actual Breeze OAuth URL
            oauth_url = "https://api.icicidirect.com/oauth/authorize"
            
            params = {
                'response_type': 'code',
                'client_id': self.config.BREEZE_API_KEY,
                'redirect_uri': redirect_uri,
                'scope': 'read write',
                'state': state
            }
            
            # Build URL with parameters
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{oauth_url}?{param_string}"
            
            return full_url
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            return ""
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self.sessions.items():
                if current_time > session_data['expires_at']:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
            
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            current_time = datetime.now()
            active_count = 0
            
            for session_data in self.sessions.values():
                if current_time <= session_data['expires_at']:
                    active_count += 1
            
            return active_count
            
        except Exception as e:
            logger.error(f"Error getting active sessions count: {e}")
            return 0