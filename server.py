from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import tempfile

app = FastAPI()

# CORS 설정 (개발 단계에서는 모든 origin 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메시지 모델 정의
class Message(BaseModel):
    role: str
    content: str


# 간단한 인메모리 메시지 저장소
message_store = {"role": "system", "content": "Initializing..."}

app.mount("/Interface", StaticFiles(directory="Interface", html=True), name="static")

@app.get("/")
async def root():
    return FileResponse("Interface/index.html")

# 클라이언트가 GET 요청을 보내면 저장된 메시지를 반환
@app.get("/message")
def get_message():
    return message_store

# 클라이언트가 POST 요청으로 메시지를 보내면 저장
@app.post("/message")
def post_message(message: Message):
    message_store["role"] = message.role
    message_store["content"] = message.content
    return {"status": "ok"}


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, "latest.wav")
    with tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=".wav", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name         
    os.replace(tmp_path, file_location)

    return {"status": "ok"}



# WAV 파일을 반환하는 엔드포인트 (클라이언트가 음성을 재생할 때 사용)
@app.get("/audio")
async def get_audio():
    file_location = os.path.join(UPLOAD_DIR, "latest.wav")
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="Audio file not found")
    response = FileResponse(file_location, media_type="audio/wav", filename="latest.wav")
    response.headers["Cache-Control"] = "no-store"
    return response


audio_finished_flag = False


@app.post("/audio_finished")
async def audio_finished():
    # This endpoint is called when the client signals that audio playback has ended.
    global audio_finished_flag
    audio_finished_flag = True
    print("[Server] Received audio playback finished signal.")
    return {"status": "ok"}


@app.get("/audio_finished")
async def get_audio_finished():
    global audio_finished_flag
    flag = audio_finished_flag
    # Reset flag after reading
    audio_finished_flag = False
    return {"audio_finished": flag}


# 서버 실행 (이 코드는 launcher.py에서 import 하여 run_server()로 호출할 수 있도록 만듭니다.)
def run_server():
    uvicorn.run("server:app", host="127.0.0.1", port=5500, reload=True, access_log=False)
