from datetime import datetime
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from config import Config
import uuid

bcrypt = Bcrypt()

# MongoDB connection with error handling
try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    db = client[Config.MONGO_DB]
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"⚠️ MongoDB connection error: {e}")
    print("⚠️ Running in mock mode without database")
    db = None

class User:
    collection = db['users'] if db else None
    
    @classmethod
    def create(cls, data):
        """Create a new user"""
        if not cls.collection:
            # Mock mode - return success
            return {'inserted_id': str(uuid.uuid4())}
        
        data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        data['created_at'] = datetime.utcnow()
        data['is_admin'] = False
        data['updated_at'] = datetime.utcnow()
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        if not cls.collection:
            # Mock mode - return demo user
            if email == 'user@example.com':
                return {
                    '_id': 'mock_user_id',
                    'name': 'Demo User',
                    'email': 'user@example.com',
                    'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
                    'is_admin': False
                }
            return None
        return cls.collection.find_one({'email': email})
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        if not cls.collection:
            return {'_id': user_id, 'name': 'Demo User', 'email': 'user@example.com', 'is_admin': False}
        return cls.collection.find_one({'_id': user_id})
    
    @classmethod
    def check_password(cls, hashed_password, password):
        """Check password"""
        return bcrypt.check_password_hash(hashed_password, password)

class MissingPerson:
    collection = db['missing_persons'] if db else None
    
    @classmethod
    def create(cls, data):
        """Create a new missing person report"""
        if not cls.collection:
            return {'inserted_id': str(uuid.uuid4())}
        
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        data['status'] = 'pending'  # pending, approved, resolved, rejected
        data['match_found'] = False
        data['similarity_percentage'] = 0
        data['views'] = 0
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_all(cls, query={}):
        """Find all missing persons matching query"""
        if not cls.collection:
            # Return mock data
            return [
                {
                    '_id': '1',
                    'name': 'John Doe',
                    'age': 25,
                    'gender': 'male',
                    'last_seen_location': 'New York',
                    'last_seen_date': '2024-01-15',
                    'description': 'Wearing blue jacket',
                    'status': 'approved',
                    'images': ['https://via.placeholder.com/300'],
                    'created_at': datetime.utcnow()
                },
                {
                    '_id': '2',
                    'name': 'Jane Smith',
                    'age': 30,
                    'gender': 'female',
                    'last_seen_location': 'Los Angeles',
                    'last_seen_date': '2024-01-20',
                    'description': 'Wearing red dress',
                    'status': 'approved',
                    'images': ['https://via.placeholder.com/300'],
                    'created_at': datetime.utcnow()
                }
            ]
        return list(cls.collection.find(query).sort('created_at', -1))
    
    @classmethod
    def find_by_id(cls, person_id):
        """Find missing person by ID"""
        if not cls.collection:
            return None
        from bson import ObjectId
        return cls.collection.find_one({'_id': ObjectId(person_id)})
    
    @classmethod
    def update_status(cls, person_id, status):
        """Update missing person status"""
        if not cls.collection:
            return None
        from bson import ObjectId
        return cls.collection.update_one(
            {'_id': ObjectId(person_id)},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
    
    @classmethod
    def update_match(cls, person_id, match_data):
        """Update match information"""
        if not cls.collection:
            return None
        from bson import ObjectId
        return cls.collection.update_one(
            {'_id': ObjectId(person_id)},
            {'$set': {
                'match_found': True,
                'similarity_percentage': match_data['similarity'],
                'matched_with': match_data['unidentified_id'],
                'matched_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @classmethod
    def increment_views(cls, person_id):
        """Increment view count"""
        if not cls.collection:
            return None
        from bson import ObjectId
        return cls.collection.update_one(
            {'_id': ObjectId(person_id)},
            {'$inc': {'views': 1}}
        )

class UnidentifiedPerson:
    collection = db['unidentified_persons'] if db else None
    
    @classmethod
    def create(cls, data):
        """Create a new unidentified person record"""
        if not cls.collection:
            return {'inserted_id': str(uuid.uuid4())}
        
        data['uploaded_at'] = datetime.utcnow()
        data['status'] = 'active'
        data['updated_at'] = datetime.utcnow()
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_all(cls, query={}):
        """Find all unidentified persons"""
        if not cls.collection:
            return []
        return list(cls.collection.find({'status': 'active'}).sort('uploaded_at', -1))
    
    @classmethod
    def find_by_id(cls, person_id):
        """Find unidentified person by ID"""
        if not cls.collection:
            return None
        from bson import ObjectId
        return cls.collection.find_one({'_id': ObjectId(person_id)})