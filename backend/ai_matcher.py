import numpy as np
from PIL import Image
import requests
from io import BytesIO
import hashlib

class FaceMatcher:
    def __init__(self):
        """Initialize the FaceMatcher"""
        print("✅ FaceMatcher initialized (simplified version)")
    
    def get_image_hash(self, image_url):
        """Get perceptual hash of image"""
        try:
            response = requests.get(image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            # Resize to small size for hashing
            img = img.resize((8, 8), Image.Resampling.LANCZOS)
            # Convert to grayscale
            img = img.convert('L')
            # Get pixel values
            pixels = list(img.getdata())
            # Calculate average
            avg = sum(pixels) / len(pixels)
            # Generate hash
            bits = ''.join(['1' if px > avg else '0' for px in pixels])
            return int(bits, 2)
        except Exception as e:
            print(f"Error generating hash: {e}")
            return 0
    
    def calculate_similarity(self, hash1, hash2):
        """Calculate similarity based on hash difference"""
        if hash1 == 0 or hash2 == 0:
            return 0
        
        # Calculate Hamming distance
        xor = hash1 ^ hash2
        distance = bin(xor).count('1')
        
        # Convert to similarity percentage (64 bits total)
        similarity = ((64 - distance) / 64) * 100
        return similarity
    
    def compare_faces(self, face1_url, face2_url):
        """Compare two faces using perceptual hashing"""
        try:
            hash1 = self.get_image_hash(face1_url)
            hash2 = self.get_image_hash(face2_url)
            
            similarity = self.calculate_similarity(hash1, hash2)
            return similarity
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0
    
    def find_matches(self, missing_person_images, unidentified_persons, threshold=70):
        """Find matches between missing person and unidentified persons"""
        matches = []
        
        for unidentified in unidentified_persons:
            unidentified_id = str(unidentified.get('_id', 'unknown'))
            unidentified_images = unidentified.get('images', [])
            
            best_similarity = 0
            
            for missing_img in missing_person_images:
                for unidentified_img in unidentified_images:
                    similarity = self.compare_faces(missing_img, unidentified_img)
                    best_similarity = max(best_similarity, similarity)
                    
                    if best_similarity >= threshold:
                        break
                if best_similarity >= threshold:
                    break
            
            if best_similarity >= threshold:
                matches.append({
                    'unidentified_id': unidentified_id,
                    'similarity': best_similarity,
                    'unidentified_images': unidentified_images
                })
        
        return matches