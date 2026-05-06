import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Download a sample traffic image from internet
image_url = 'https://images.unsplash.com/photo-1506015391300-4802dc74de2e?w=400'
print("Downloading sample traffic image...")

try:
    img_response = requests.get(image_url, timeout=10)
    img_response.raise_for_status()
    image_data = img_response.content
    print(f"Downloaded {len(image_data)} bytes")
    
    # Upload to server
    url = 'http://localhost:8000/reports/with-image'
    files = {'image': ('traffic.jpg', image_data, 'image/jpeg')}
    data = {
        'text': 'Ket xe nghiem trong tai nga tu Quan 1, nhieu xe may dung den do',
        'latitude': '10.8231',
        'longitude': '106.6297'
    }
    
    print("Uploading to server...")
    response = requests.post(url, files=files, data=data, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Report ID: {result.get('id')}")
        print(f"Status: {repr(result.get('status'))}")
        print(f"Categories: {repr(result.get('predicted_categories'))}")
        print(f"NLP Confidence: {result.get('nlp_confidence')}")
        print(f"Vision Confidence: {result.get('vision_confidence')}")
        print(f"Final Confidence: {result.get('final_confidence')}")
        print(f"Vision Labels: {repr(result.get('vision_labels')[:3] if result.get('vision_labels') else [])}")  # Show first 3
    else:
        print(f"❌ Error: {response.text[:500]}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
