"""
Firebase/Firestore Database Configuration and Management
"""
from dotenv import load_dotenv
load_dotenv() 
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase/Firestore database operations"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase with service account credentials"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.db = firestore.client()
                self.initialized = True
                logger.info("Firebase already initialized, using existing instance")
                return
            
            # Try to get credentials from environment variable
            firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
            
            if firebase_creds:
                # Parse JSON credentials from environment variable
                try:
                    cred_dict = json.loads(firebase_creds)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    self.initialized = True
                    logger.info("Firebase initialized with environment credentials")
                    return
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in FIREBASE_CREDENTIALS environment variable")
            
            # Try to use service account file
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
            
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                logger.info(f"Firebase initialized with service account file: {service_account_path}")
                return
            
            # Fallback: Use default credentials (for Google Cloud environments)
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                logger.info("Firebase initialized with default credentials")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize with default credentials: {e}")
            
            # If all methods fail, log warning but continue (for development)
            logger.warning("Firebase not initialized - running in development mode without database")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if Firebase/Firestore is available"""
        return self.initialized and self.db is not None
    
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user in Firestore"""
        if not self.is_available():
            logger.warning("Firestore not available, cannot create user")
            return None
        
        try:
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
            
            doc_ref = self.db.collection('users').document()
            doc_ref.set(user_data)
            
            logger.info(f"User created with ID: {doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        if not self.is_available():
            return None
        
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            docs = query.stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not self.is_available():
            return None
        
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    async def update_user_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        if not self.is_available():
            return False
        
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.update({
                'last_login': datetime.now(timezone.utc)
            })
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user login: {e}")
            return False
    
    async def update_user_stats(self, user_id: str, stats_update: Dict[str, Any]) -> bool:
        """Update user statistics"""
        if not self.is_available():
            return False
        
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.update({f'stats.{key}': value for key, value in stats_update.items()})
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")
            return False
    
    # Challenge History Management
    async def save_challenge_session(self, user_id: str, session_data: Dict[str, Any]) -> Optional[str]:
        """Save a challenge session to user's history"""
        if not self.is_available():
            return None
        
        try:
            session_data['user_id'] = user_id
            session_data['created_at'] = datetime.now(timezone.utc)
            
            doc_ref = self.db.collection('challenge_sessions').document()
            doc_ref.set(session_data)
            
            logger.info(f"Challenge session saved with ID: {doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save challenge session: {e}")
            return None
    
    async def get_user_challenge_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's challenge history"""
        if not self.is_available():
            return []
        
        try:
            sessions_ref = self.db.collection('challenge_sessions')
            query = sessions_ref.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            sessions = []
            for doc in docs:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get challenge history: {e}")
            return []
    
    async def save_challenge_result(self, user_id: str, challenge_data: Dict[str, Any]) -> Optional[str]:
        """Save individual challenge result"""
        if not self.is_available():
            return None
        
        try:
            challenge_data['user_id'] = user_id
            challenge_data['completed_at'] = datetime.now(timezone.utc)
            
            doc_ref = self.db.collection('challenge_results').document()
            doc_ref.set(challenge_data)
            
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save challenge result: {e}")
            return None
    
    # Document Management
    async def save_document_metadata(self, user_id: str, document_data: Dict[str, Any]) -> Optional[str]:
        """Save document metadata"""
        if not self.is_available():
            return None
        
        try:
            document_data['user_id'] = user_id
            document_data['uploaded_at'] = datetime.now(timezone.utc)
            
            doc_ref = self.db.collection('documents').document()
            doc_ref.set(document_data)
            
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save document metadata: {e}")
            return None
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's uploaded documents"""
        if not self.is_available():
            return []
        
        try:
            docs_ref = self.db.collection('documents')
            query = docs_ref.where('user_id', '==', user_id).order_by('uploaded_at', direction=firestore.Query.DESCENDING)
            docs = query.stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            return []

# Global Firebase manager instance
firebase_manager = FirebaseManager()

# Convenience functions
async def create_user(user_data: Dict[str, Any]) -> Optional[str]:
    """Create a new user"""
    return await firebase_manager.create_user(user_data)

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    return await firebase_manager.get_user_by_email(email)

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return await firebase_manager.get_user_by_id(user_id)

async def update_user_login(user_id: str) -> bool:
    """Update user login timestamp"""
    return await firebase_manager.update_user_login(user_id)

async def save_challenge_session(user_id: str, session_data: Dict[str, Any]) -> Optional[str]:
    """Save challenge session"""
    return await firebase_manager.save_challenge_session(user_id, session_data)

async def get_user_challenge_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user challenge history"""
    return await firebase_manager.get_user_challenge_history(user_id, limit)

def is_database_available() -> bool:
    """Check if database is available"""
    return firebase_manager.is_available()

