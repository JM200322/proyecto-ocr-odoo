#!/usr/bin/env python3
"""Test script to verify the language mapping fix"""

import base64
import json
import requests
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """Create a test image with Spanish text"""
    img = Image.new('RGB', (500, 100), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a larger font
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 30), 'Hola mundo - Test español', fill='black', font=font)
    img.save('test_spanish.jpg')
    return img

def test_ocr_api(language='es'):
    """Test OCR API with given language"""
    
    # Create test image
    img = create_test_image()
    
    # Convert to base64
    with open('test_spanish.jpg', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare request
    data = {
        'image_data': f'data:image/jpeg;base64,{image_data}',
        'language': language,
        'brightness': 0,
        'contrast': 100,
        'sharpness': 0
    }
    
    try:
        print(f"Testing OCR with language: '{language}'")
        print(f"Sending request to: http://127.0.0.1:5000/api/process-ocr")
        
        response = requests.post(
            'http://127.0.0.1:5000/api/process-ocr',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"SUCCESS!")
                print(f"Text: {result.get('text', '')}")
                print(f"Confidence: {result.get('confidence', 0)}%")
                print(f"Time: {result.get('processing_time', 0):.2f}s")
                if result.get('details'):
                    print(f"Details: {result['details']}")
            else:
                print(f"OCR failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Testing OCR Language Mapping Fix")
    print("=" * 50)
    
    # Test with standard language code 'es' (should be mapped to 'spa')
    test_ocr_api('es')
    
    print("\n" + "=" * 50)
    
    # Test with OCR.Space native code 'spa' (should work directly)
    test_ocr_api('spa')