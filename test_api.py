import requests
import json

def test_submit_report():
    url = "http://localhost:8000/reports/"
    payload = {
        "text": "Ngã tư Hàng Xanh đang kẹt xe cứng ngắc từ 6h sáng nay, nước lại bắt đầu dâng cao do triều cường."
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sening POST request to {url}...")
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_submit_report()
