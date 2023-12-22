import os
import uvicorn
from fastapi import FastAPI, Form, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from app.validate import validate_and_convert_file
from app.createVideo import createVideo
from app.getScript import getScript
import shutil
import json
from typing import Optional

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
    lecture_title: Optional[str] = None
    conciseness: str
    tempo: float
    subtitle: bool = True

@app.post("/createVideo", response_class=FileResponse)
async def create_upload_file(background_tasks: BackgroundTasks, lecture_data_json: str = Form(...), lecture_file: UploadFile = File(...)):
    """
        This project creates a video presentation from a lecture document by repeatedly querying ChatGPT's vision API to generate a 
        lecture script in conjunction with gTTS and FFmpeg to automate video creation. Input the parameters as a json string in the 
        lecture_data_json field. The parameters are as follows:

        - **file**: An UploadFile object representing the uploaded file. This file can be a PDF, a Word document, or a PowerPoint presentation and up to 50 pages. The file size must be between 1 and 5 MB.
        
        - **lecture_title**: A string representing the title of the lecture for context purposes. The default value is None.

        - **conciseness**: A string representing the level of conciseness of the lecture. The options are "concise", "medium", and "verbose".

        - **tempo**: A float representing the speed of the video. The options are 0.5, 0.75, 1.0, 1.25, and 1.5, 1.75, and 2.

        - **subtitle**: A boolean representing whether subtitles should be included in the video. The default value is True.

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
        subtitle = params["subtitle"]
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid item data")
    
    
    temp_dir = "temp_files"
    file_dir = os.path.join(temp_dir, "converted.pdf")
    video_file = os.path.join(temp_dir, "final_video.mp4")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Validate and convert the uploaded file to PDF
        await validate_and_convert_file(file_dir, lecture_file, tempo, conciseness)
        
        # Generate the script and slides for the lecture
        script = await getScript(file_dir, lecture_title, conciseness)
        
        # Stitch sped up video clips together and add subtitles
        await createVideo(video_file, script, tempo, subtitle)
                
        # Return the video file as a response
        return FileResponse(video_file, media_type="video/mp4", filename='final_video.mp4')
    finally:
        # Schedule the deletion of the temp_files directory and its contents
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
