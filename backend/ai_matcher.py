import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import InceptionResNetV2
from tensorflow.keras.applications.inception_resnet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
import cloudinary
import cloudinary.api
import requests
from io import BytesIO
from PIL import Image
import os

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class FaceMatcher:
    def __init__(self):
        """Initialize the FaceMatcher with pre-trained models"""
        try:
            # Load pre-trained model for feature extraction
            print("Loading InceptionResNetV2 model...")
            self.model = InceptionResNetV2(weights='imagenet', include_top=False, pooling='avg')
            print("Model loaded successfully!")
            
            # Load face cascade classifier
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if not os.path.exists(cascade_path):
                print(f"Warning: Cascade file not found at {cascade_path}")
                self.face_cascade = None
            else:
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                if self.face_cascade.empty():
                    print("Warning: Failed to load face cascade classifier")
                    self.face_cascade = None
                else:
                    print("Face cascade loaded successfully!")
        except Exception as e:
            print(f"Error initializing FaceMatcher: {e}")
            self.model = None
            self.face_cascade = None
    
    def download_image(self, image_url):
        """Download image from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return np.array(img)
        except Exception as e:
            print(f"Error downloading image from {image_url}: {e}")
            return None
    
    def extract_face(self, image_url):
        """Extract face from image"""
        try:
            if self.face_cascade is None:
                print("Face cascade not available")
                return None
            
            # Download image from URL
            img = self.download_image(image_url)
            if img is None:
                return None
            
            # Convert to RGB if necessary
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
            # Convert to uint8 if necessary
            if img.dtype != np.uint8:
                img = (img * 255).astype(np.uint8) if img.max() <= 1.0 else img.astype(np.uint8)
            
            # Detect faces
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Take the first face (largest face)
                (x, y, w, h) = max(faces, key=lambda rect: rect[2] * rect[3])
                # Add padding around face
                padding = int(min(w, h) * 0.2)
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(img.shape[1] - x, w + 2 * padding)
                h = min(img.shape[0] - y, h + 2 * padding)
                
                face = img[y:y+h, x:x+w]
                return face
            else:
                print(f"No face detected in image: {image_url}")
                # Return the whole image if no face detected
                return img
        except Exception as e:
            print(f"Error extracting face from {image_url}: {e}")
            return None
    
    def extract_features(self, face_img):
        """Extract features from face image"""
        try:
            if self.model is None:
                print("Model not available")
                return None
            
            if face_img is None:
                return None
            
            # Preprocess face for the model
            face_img = cv2.resize(face_img, (299, 299))
            
            # Convert to RGB if necessary
            if len(face_img.shape) == 2:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2RGB)
            
            # Ensure correct dtype
            face_img = face_img.astype(np.float32)
            
            # Expand dimensions and preprocess
            face_img = np.expand_dims(face_img, axis=0)
            face_img = preprocess_input(face_img)
            
            # Extract features
            features = self.model.predict(face_img, verbose=0)
            return features.flatten()
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def calculate_similarity(self, features1, features2):
        """Calculate cosine similarity between two feature vectors"""
        try:
            if features1 is None or features2 is None:
                return 0
            
            # Check if features are valid
            if len(features1) == 0 or len(features2) == 0:
                return 0
            
            # Normalize features
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            features1_norm = features1 / norm1
            features2_norm = features2 / norm2
            
            # Calculate cosine similarity
            similarity = np.dot(features1_norm, features2_norm)
            
            # Ensure similarity is between -1 and 1
            similarity = np.clip(similarity, -1, 1)
            
            # Convert to percentage (0-100)
            similarity_percentage = ((similarity + 1) / 2) * 100
            
            return float(similarity_percentage)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0
    
    def compare_faces(self, face1_url, face2_url):
        """Compare two faces and return similarity percentage"""
        try:
            print(f"Comparing faces: {face1_url[:50]}... and {face2_url[:50]}...")
            
            # Extract faces
            face1 = self.extract_face(face1_url)
            face2 = self.extract_face(face2_url)
            
            if face1 is None:
                print("Face 1 extraction failed")
                return 0
            
            if face2 is None:
                print("Face 2 extraction failed")
                return 0
            
            # Extract features
            features1 = self.extract_features(face1)
            features2 = self.extract_features(face2)
            
            if features1 is None or features2 is None:
                print("Feature extraction failed")
                return 0
            
            # Calculate similarity
            similarity = self.calculate_similarity(features1, features2)
            print(f"Similarity: {similarity:.2f}%")
            
            return similarity
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0
    
    def find_matches(self, missing_person_images, unidentified_persons, threshold=70):
        """Find matches between missing person and unidentified persons"""
        matches = []
        
        if not missing_person_images or not unidentified_persons:
            print("No images or unidentified persons to compare")
            return matches
        
        print(f"Finding matches for {len(missing_person_images)} missing person images against {len(unidentified_persons)} unidentified persons")
        
        for unidentified in unidentified_persons:
            unidentified_id = str(unidentified.get('_id', 'unknown'))
            unidentified_images = unidentified.get('images', [])
            
            if not unidentified_images:
                continue
            
            best_match = {
                'unidentified_id': unidentified_id,
                'similarity': 0,
                'unidentified_images': unidentified_images
            }
            
            for missing_img in missing_person_images:
                for unidentified_img in unidentified_images:
                    similarity = self.compare_faces(missing_img, unidentified_img)
                    
                    if similarity > best_match['similarity']:
                        best_match['similarity'] = similarity
                        
                        if similarity >= threshold:
                            print(f"Match found! Similarity: {similarity:.2f}%")
                            break
                
                if best_match['similarity'] >= threshold:
                    break
            
            if best_match['similarity'] >= threshold:
                matches.append(best_match)
        
        return matches

    def batch_compare(self, missing_person_images, unidentified_persons, threshold=70):
        """Batch compare multiple images efficiently"""
        matches = []
        
        # Pre-extract features for unidentified persons
        unidentified_features = []
        for unidentified in unidentified_persons:
            unidentified_id = str(unidentified.get('_id', 'unknown'))
            unidentified_images = unidentified.get('images', [])
            
            features_list = []
            for img_url in unidentified_images:
                face = self.extract_face(img_url)
                if face is not None:
                    features = self.extract_features(face)
                    if features is not None:
                        features_list.append(features)
            
            if features_list:
                unidentified_features.append({
                    'id': unidentified_id,
                    'features': features_list,
                    'images': unidentified_images
                })
        
        # Compare missing person images with pre-extracted features
        for missing_img in missing_person_images:
            missing_face = self.extract_face(missing_img)
            if missing_face is None:
                continue
            
            missing_features = self.extract_features(missing_face)
            if missing_features is None:
                continue
            
            for unidentified in unidentified_features:
                best_similarity = 0
                for unidentified_feature in unidentified['features']:
                    similarity = self.calculate_similarity(missing_features, unidentified_feature)
                    best_similarity = max(best_similarity, similarity)
                
                if best_similarity >= threshold:
                    matches.append({
                        'unidentified_id': unidentified['id'],
                        'similarity': best_similarity,
                        'unidentified_images': unidentified['images']
                    })
        
        return matches

# Test function
def test_face_matcher():
    """Test the FaceMatcher with sample images"""
    matcher = FaceMatcher()
    
    # Test with sample URLs (replace with actual image URLs)
    test_url1 = "https://example.com/face1.jpg"
    test_url2 = "https://example.com/face2.jpg"
    
    similarity = matcher.compare_faces(test_url1, test_url2)
    print(f"Test similarity: {similarity}%")

if __name__ == "__main__":
    print("Testing FaceMatcher...")
    test_face_matcher()