from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from bson import ObjectId
from datetime import datetime, timedelta
import json
import os
import cloudinary
import cloudinary.uploader

from config import Config
from models import User, MissingPerson, UnidentifiedPerson
from ai_matcher import FaceMatcher

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize Cloudinary (optional)
try:
    if Config.CLOUDINARY_CLOUD_NAME:
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET
        )
        print("✅ Cloudinary configured")
    else:
        print("⚠️ Cloudinary not configured - using local storage")
except Exception as e:
    print(f"⚠️ Cloudinary config error: {e}")

# Initialize AI Matcher
try:
    face_matcher = FaceMatcher()
except Exception as e:
    print(f"⚠️ AI Matcher initialization error: {e}")
    face_matcher = None

# Custom JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

app.json_encoder = JSONEncoder

# Serve frontend
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ============ API ROUTES ============

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify API is working"""
    return jsonify({
        'message': 'Missing Person Finder API is working!',
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': [
            '/api/register',
            '/api/login',
            '/api/admin/login',
            '/api/missing-person/report',
            '/api/missing-person/my-reports',
            '/api/missing-person/all',
            '/api/missing-person/<id>',
            '/api/search',
            '/api/admin/missing-person/<id>/status',
            '/api/admin/unidentified/upload',
            '/api/admin/unidentified/all'
        ]
    })

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user exists
        if User.find_by_email(data['email']):
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        result = User.create({
            'name': data['name'],
            'email': data['email'],
            'password': data['password'],
            'phone': data.get('phone', ''),
            'user_type': data.get('userType', 'family')
        })
        
        return jsonify({
            'message': 'User registered successfully',
            'id': str(result.inserted_id) if hasattr(result, 'inserted_id') else 'mock_id'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
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
                    'name': user.get('name', 'User'),
                    'email': user['email'],
                    'is_admin': user.get('is_admin', False)
                }
            })
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        
        if data.get('email') == Config.ADMIN_EMAIL and data.get('password') == Config.ADMIN_PASSWORD:
            access_token = create_access_token(
                identity='admin',
                expires_delta=timedelta(days=1)
            )
            return jsonify({
                'token': access_token,
                'user': {
                    'id': 'admin',
                    'name': 'Administrator',
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
    """Report a missing person"""
    try:
        user_id = get_jwt_identity()
        
        # Handle multipart form data (for file uploads)
        if request.files:
            data = request.form.to_dict()
            files = request.files.getlist('images')
            
            # Upload images (mock for now)
            image_urls = []
            for file in files[:5]:  # Limit to 5 images
                # In production, upload to Cloudinary
                # For now, use placeholder
                image_urls.append('https://via.placeholder.com/300')
        else:
            data = request.get_json()
            image_urls = data.get('images', ['https://via.placeholder.com/300'])
        
        # Create report
        report_data = {
            'user_id': user_id,
            'name': data.get('name'),
            'age': int(data.get('age', 0)),
            'gender': data.get('gender'),
            'last_seen_location': data.get('location'),
            'last_seen_date': data.get('date'),
            'description': data.get('description'),
            'contact_details': data.get('contact'),
            'images': image_urls,
            'status': 'pending'
        }
        
        result = MissingPerson.create(report_data)
        
        return jsonify({
            'message': 'Missing person reported successfully',
            'id': str(result.inserted_id) if hasattr(result, 'inserted_id') else 'mock_id'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/my-reports', methods=['GET'])
@jwt_required()
def get_my_reports():
    """Get current user's reports"""
    try:
        user_id = get_jwt_identity()
        reports = MissingPerson.find_all({'user_id': user_id})
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/all', methods=['GET'])
def get_all_reports():
    """Get all missing person reports"""
    try:
        reports = MissingPerson.find_all({'status': 'approved'})
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-person/<person_id>', methods=['GET'])
def get_report(person_id):
    """Get single report by ID"""
    try:
        report = MissingPerson.find_by_id(person_id)
        if report:
            # Increment view count
            MissingPerson.increment_views(person_id)
            return jsonify(report), 200
        return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search():
    """Search missing persons"""
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

# Admin routes
@app.route('/api/admin/missing-person/<person_id>/status', methods=['PUT'])
@jwt_required()
def update_status(person_id):
    """Update missing person status (admin only)"""
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        MissingPerson.update_status(person_id, data.get('status'))
        
        return jsonify({'message': 'Status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/unidentified/upload', methods=['POST'])
@jwt_required()
def upload_unidentified():
    """Upload unidentified person (admin only)"""
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Handle file uploads
        files = request.files.getlist('images')
        location = request.form.get('location')
        description = request.form.get('description')
        
        # Mock image URLs
        image_urls = ['https://via.placeholder.com/300' for _ in files[:5]]
        
        # Create record
        unidentified = {
            'images': image_urls,
            'location': location,
            'description': description
        }
        
        result = UnidentifiedPerson.create(unidentified)
        
        # Find matches
        matches = []
        if face_matcher:
            # Get all pending/approved missing persons
            missing_persons = MissingPerson.find_all({'status': {'$in': ['pending', 'approved']}})
            
            for missing in missing_persons:
                similarity = face_matcher.compare_faces(
                    missing['images'][0] if missing['images'] else '',
                    image_urls[0] if image_urls else ''
                )
                
                if similarity >= 70:
                    matches.append({
                        'missing_person_id': str(missing['_id']),
                        'name': missing['name'],
                        'similarity': similarity
                    })
        
        return jsonify({
            'message': 'Unidentified person uploaded successfully',
            'id': str(result.inserted_id) if hasattr(result, 'inserted_id') else 'mock_id',
            'matches_found': len(matches),
            'matches': matches
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/unidentified/all', methods=['GET'])
@jwt_required()
def get_all_unidentified():
    """Get all unidentified persons (admin only)"""
    try:
        user_id = get_jwt_identity()
        if user_id != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        unidentified = UnidentifiedPerson.find_all()
        return jsonify(unidentified), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handler
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api'):
        return jsonify({
            'error': 'API endpoint not found',
            'message': 'The requested URL was not found on the server',
            'valid_endpoints': [
                '/api/test',
                '/api/register',
                '/api/login',
                '/api/admin/login',
                '/api/missing-person/report',
                '/api/missing-person/my-reports',
                '/api/missing-person/all',
                '/api/search'
            ]
        }), 404
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 MISSING PERSON FINDER API")
    print("="*60)
    print("\n📡 Server Information:")
    print("   • Backend URL: http://localhost:5000")
    print("   • Frontend URL: http://localhost:5000")
    print("\n📡 Available API Endpoints:")
    print("   • GET  /api/test                    - Test connection")
    print("   • POST /api/register                 - Register user")
    print("   • POST /api/login                     - User login")
    print("   • POST /api/admin/login               - Admin login")
    print("   • POST /api/missing-person/report     - Report missing person")
    print("   • GET  /api/missing-person/my-reports - Get user reports")
    print("   • GET  /api/missing-person/all        - Get all reports")
    print("   • GET  /api/search                     - Search reports")
    print("\n📡 Frontend Pages:")
    print("   • http://localhost:5000/              - Home page")
    print("   • http://localhost:5000/login.html    - Login page")
    print("   • http://localhost:5000/register.html - Register page")
    print("   • http://localhost:5000/dashboard.html - User dashboard")
    print("   • http://localhost:5000/report.html    - Report page")
    print("   • http://localhost:5000/admin.html     - Admin panel")
    print("\n" + "="*60)
    print("✅ Server is running! Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')