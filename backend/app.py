from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import cloudinary
import cloudinary.uploader
from bson import ObjectId
from datetime import timedelta
import json
import os

from config import Config
from models import User, MissingPerson, UnidentifiedPerson, db
from ai_matcher import FaceMatcher

app = Flask(__name__)
app.config.from_object(Config)

# Fix CORS - allow all origins for development
CORS(app, origins=["*"], allow_headers=["*"], supports_credentials=True)

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

# Initialize AI Matcher
face_matcher = FaceMatcher()

# Test route
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'Backend is working!', 
        'status': 'ok',
        'endpoints': [
            '/api/register',
            '/api/login',
            '/api/admin/login',
            '/api/missing-person/report',
            '/api/missing-person/my-reports',
            '/api/missing-person/all',
            '/api/search'
        ]
    }), 200

# Custom JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

app.json_encoder = JSONEncoder

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Check if user exists
        if User.find_by_email(data['email']):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        User.create(data)
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = User.find_by_email(data['email'])
        
        if user and User.check_password(user['password'], data['password']):
            access_token = create_access_token(
                identity=str(user['_id']),
                expires_delta=timedelta(days=1)
            )
            return jsonify({
                'token': access_token,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email'],
                    'is_admin': user.get('is_admin', False)
                }
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        
        if data['email'] == Config.ADMIN_EMAIL and data['password'] == Config.ADMIN_PASSWORD:
            access_token = create_access_token(
                identity='admin',
                expires_delta=timedelta(days=1)
            )
            return jsonify({
                'token': access_token,
                'user': {
                    'id': 'admin',
                    'name': 'Admin',
                    'email': Config.ADMIN_EMAIL,
                    'is_admin': True
                }
            })
        
        return jsonify({'error': 'Invalid admin credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/report', methods=['POST'])
@jwt_required()
def report_missing_person():
    try:
        user_id = get_jwt_identity()
        data = request.form.to_dict()
        files = request.files.getlist('images')
        
        # Upload images to Cloudinary
        image_urls = []
        for file in files:
            result = cloudinary.uploader.upload(file)
            image_urls.append(result['secure_url'])
        
        # Create missing person record
        missing_person = {
            'user_id': user_id,
            'name': data['name'],
            'age': int(data['age']),
            'gender': data['gender'],
            'last_seen_location': data['location'],
            'last_seen_date': data['date'],
            'description': data['description'],
            'contact_details': data['contact'],
            'images': image_urls
        }
        
        result = MissingPerson.create(missing_person)
        
        return jsonify({
            'message': 'Missing person reported successfully',
            'id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/my-reports', methods=['GET'])
@jwt_required()
def get_my_reports():
    try:
        user_id = get_jwt_identity()
        reports = MissingPerson.find_all({'user_id': user_id})
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/all', methods=['GET'])
def get_all_reports():
    try:
        reports = MissingPerson.find_all()
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/missing-person/<person_id>/status', methods=['PUT'])
@jwt_required()
def update_missing_person_status(person_id):
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.json
        MissingPerson.update_status(ObjectId(person_id), data['status'])
        return jsonify({'message': 'Status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/unidentified/upload', methods=['POST'])
@jwt_required()
def upload_unidentified():
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        files = request.files.getlist('images')
        location = request.form.get('location')
        description = request.form.get('description')
        
        # Upload images to Cloudinary
        image_urls = []
        for file in files:
            result = cloudinary.uploader.upload(file)
            image_urls.append(result['secure_url'])
        
        # Create unidentified person record
        unidentified = {
            'images': image_urls,
            'location': location,
            'description': description
        }
        
        result = UnidentifiedPerson.create(unidentified)
        
        return jsonify({
            'message': 'Unidentified person uploaded successfully',
            'id': str(result.inserted_id),
            'matches_found': 0
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/unidentified/all', methods=['GET'])
@jwt_required()
def get_unidentified():
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        unidentified = UnidentifiedPerson.find_all()
        return jsonify(unidentified), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_missing_persons():
    try:
        location = request.args.get('location', '')
        name = request.args.get('name', '')
        
        query = {'status': 'approved'}
        
        if location:
            query['last_seen_location'] = {'$regex': location, '$options': 'i'}
        if name:
            query['name'] = {'$regex': name, '$options': 'i'}
        
        results = MissingPerson.find_all(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')