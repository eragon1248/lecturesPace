from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from utils import validate_and_convert_file
from createVideo import createVideo
from getScript import getScript

app = FastAPI()

# CORS middleware settings for allowing frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LectureCreate(BaseModel):
    file: UploadFile
    lecture_title: str
    conciseness: str
    tempo: float
    subtitle: bool = True

@app.post("/createVideo")
async def create_upload_file(lecture_data: LectureCreate):
    file = lecture_data.file
    lecture_title = lecture_data.lecture_title
    conciseness = lecture_data.conciseness
    tempo = lecture_data.tempo
    
    lecture_pdf = validate_and_convert_file(file)
    script = getScript(lecture_pdf, lecture_title, conciseness)
    video_file = "lecture_video.mp4"
    return FileResponse(video_file, media_type="video/mp4")