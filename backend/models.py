from datetime import datetime
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from config import Config

bcrypt = Bcrypt()
client = MongoClient(Config.MONGO_URI)
db = client[Config.MONGO_DB]

class User:
    collection = db['users']
    
    @classmethod
    def create(cls, data):
        data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        data['created_at'] = datetime.utcnow()
        data['is_admin'] = False
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_by_email(cls, email):
        return cls.collection.find_one({'email': email})
    
    @classmethod
    def find_by_id(cls, user_id):
        return cls.collection.find_one({'_id': user_id})
    
    @classmethod
    def check_password(cls, hashed_password, password):
        return bcrypt.check_password_hash(hashed_password, password)

class MissingPerson:
    collection = db['missing_persons']
    
    @classmethod
    def create(cls, data):
        data['created_at'] = datetime.utcnow()
        data['status'] = 'pending'  # pending, approved, resolved, rejected
        data['match_found'] = False
        data['similarity_percentage'] = 0
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_all(cls, query={}):
        return list(cls.collection.find(query))
    
    @classmethod
    def find_by_id(cls, person_id):
        return cls.collection.find_one({'_id': person_id})
    
    @classmethod
    def update_status(cls, person_id, status):
        return cls.collection.update_one(
            {'_id': person_id},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
    
    @classmethod
    def update_match(cls, person_id, match_data):
        return cls.collection.update_one(
            {'_id': person_id},
            {'$set': {
                'match_found': True,
                'similarity_percentage': match_data['similarity'],
                'matched_with': match_data['unidentified_id'],
                'matched_at': datetime.utcnow()
            }}
        )

class UnidentifiedPerson:
    collection = db['unidentified_persons']
    
    @classmethod
    def create(cls, data):
        data['uploaded_at'] = datetime.utcnow()
        data['status'] = 'active'
        return cls.collection.insert_one(data)
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find({'status': 'active'}))
    
    @classmethod
    def find_by_id(cls, person_id):
        return cls.collection.find_one({'_id': person_id})