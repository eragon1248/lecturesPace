# lecturesPace
This project creates a video presentation from a lecture document by repeatedly querying ChatGPT's vision API to generate a 
lecture script in conjunction with gTTS and FFmpeg to automate video creation. The FastAPI based API takes in the following 
parameters as a json string in the lecture_data_json field. 

- **file**: An UploadFile object representing the uploaded file. This file can be a PDF, a Word document, or a PowerPoint presentation and up to 50 pages. The file size must be between 1 and 5 MB.

- **lecture_title**: A string representing the title of the lecture for context purposes. The default value is None.

- **conciseness**: A string representing the level of conciseness of the lecture. The options are "concise", "medium", and "verbose".

- **tempo**: A float representing the speed of the video. The options are 0.5, 0.75, 1.0, 1.25, and 1.5, 1.75, and 2.

- **subtitle**: A boolean representing whether subtitles should be included in the video. The default value is True.

Example parameter input: {"lecture_title": "Introduction to Python", "conciseness": "concise", "tempo": 1.5}
