import requests


def send_message_to_server(role: str, content: str):
    url = "http://127.0.0.1:5500/message"
    data = {"role": role, "content": content}
    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            print("Error: Received non-200 status code")
            return
        # JSON 파싱 시도
        try:
            json_data = response.json()
            print("Server response:", json_data)
        except Exception as json_err:
            print("Error parsing JSON response:", json_err)
            print("Raw response text:", response.text)
    except Exception as e:
        print("Error sending message:", e)


def send_wav_file_to_server(file_path):
    url = "http://127.0.0.1:5500/upload_audio"
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files)
            print("Audio file upload response:", response.text)
    except Exception as e:
        print("Error uploading audio file:", e)
        