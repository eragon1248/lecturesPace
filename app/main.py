import os
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from app.validate import validate_and_convert_file
from app.createVideo import createVideo
from app.getScript import getScript
import shutil
import json

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
    lecture_title: str
    conciseness: str
    tempo: float
    subtitle: bool = True

@app.post("/createVideo", response_class=FileResponse)
async def create_upload_file(lecture_data_json: str = Form(...), lecture_file: UploadFile = File(...)):
    """
        The project create a video presentation from a lecture document (<50 pages). The uploaded files can be in PDF, 
        Word, or PowerPoint format. Input the parameters as a json string in the lecture_data_json field. The parameters are as follows:\n

        - **file**: An UploadFile object representing the uploaded file. This file can be a PDF, a Word document, or a PowerPoint presentation. The file size must be between 1 and 5 MB.\n

        - **lecture_title**: A string representing the title of the lecture for context purposes.

        - **conciseness**: A string representing the level of conciseness of the lecture. The options are "concise", "medium", and "verbose".

        - **tempo**: A float representing the speed of the video. The options are 0.5, 0.75, 1.0, 1.25, and 1.5, 1.75, and 2.

        Example parameter input: {"lecture_title": "Introduction to Python", "conciseness": "concise", "tempo": 1.5}
    """
    try:
        # Convert the stringified JSON to a dict
        item_data = json.loads(lecture_data_json)
        # Convert the dict to the desired Pydantic model
        item = LectureCreate(**item_data)
        params = item.model_dump(exclude={"restaurant_name"})
        lecture_title = params["lecture_title"]
        conciseness = params["conciseness"]
        tempo = params["tempo"]
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid item data")
    
    
    temp_dir = "temp_files"
    file_dir = os.path.join(temp_dir, "converted.pdf")
    video_file = os.path.join(temp_dir, "lecture_video.mp4")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Validate and convert the uploaded file to PDF
        await validate_and_convert_file(file_dir, lecture_file)
        
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
