import os

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from app.validate import validate_and_convert_file
from createVideo import createVideo
from getScript import getScript
import shutil
from fastapi import Response

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

@app.post("/createVideo", response_model=FileResponse, summary=
          """
            The project create a video presentation from a lecture document (<50 pages). The uploaded files can be in PDF, 
            Word, or PowerPoint format.

            
            Input Parameters:

            file: An UploadFile object representing the uploaded file. This file can be a PDF, a Word document, or a PowerPoint presentation.
            The file size must be between 1 and 5 MB.

            lecture_title: A string representing the title of the lecture for context purposes.

            conciseness: A string representing the level of conciseness of the lecture. The options are "concise", "medium", and "verbose".

            tempo: A float representing the speed of the video. The options are 0.5, 0.75, 1.0, 1.25, and 1.5, 1.75, and 2.
          """)
async def create_upload_file(lecture_data: LectureCreate):
    file = lecture_data.file
    lecture_title = lecture_data.lecture_title
    conciseness = lecture_data.conciseness
    tempo = lecture_data.tempo
    
    temp_dir = "temp_files"
    file_dir = os.path.join(temp_dir, "converted.pdf")
    video_file = os.path.join(temp_dir, "lecture_video.mp4")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Validate and convert the uploaded file to PDF
        await validate_and_convert_file(file_dir, file)
        
        # Generate the script for the lecture
        script = getScript(file_dir, lecture_title, conciseness)
        
        # Perform video creation using the generated script and tempo
        createVideo(file_dir, video_file, script, tempo)
        
        # Move the video file to the temp_files directory
        shutil.move(video_file, os.path.join(temp_dir, video_file))
        
        # Return the video file as a response
        return FileResponse(os.path.join(temp_dir, video_file), media_type="video/mp4")
    finally:
        # Remove the temp_files directory and its contents
        shutil.rmtree(temp_dir, ignore_errors=True)
