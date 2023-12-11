import json
import os
from gtts import gTTS
import subprocess
from pdf2image import convert_from_path
import shutil
from pydub import AudioSegment
from pydub.playback import play


# Load the PDF file
pdf_path = 'CS376_Lecture_7.pdf'

# Convert the PDF to a list of images
images = convert_from_path(pdf_path)

# Load the JSON file
with open('responses.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Directory to save intermediate files
os.makedirs('temp_files', exist_ok=True)

# Process each slide and create individual video files
for i, response in enumerate(data):
    slide_number = i + 1
   
    # Get the slide number
    print('Working on slide', slide_number, '...')

    # Extract the content from the response
    content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

    # Convert the content to speech
    tts = gTTS(text=content, lang='en')

    # Save the speech to an audio file
    audio_file = f'temp_files/slide_{slide_number}.mp3'
    tts.save(audio_file)

    # Speed up by 1.5x
    audio = AudioSegment.from_file(audio_file)
    fast_audio = audio.speedup(playback_speed=1.5)

    # Save the output
    fast_audio.export("{audio}_fast.mp3", format="mp3")
    audio_file = f'temp_files/slide_{slide_number}_fast.mp3'

    # Save the image to a file
    image_path = f'temp_files/slide_{slide_number}.png'
    images[i].save(image_path, 'PNG')

    # Combine slide image with audio using FFmpeg
    video_file = f'temp_files/slide_{slide_number}_video.mp4'
    command = f'ffmpeg -loop 1 -i {image_path} -i {audio_file} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest {video_file}'
    subprocess.run(command, shell=True)

# Create a file listing all the individual video files
with open('temp_files/file_list.txt', 'w') as file:
    for slide_number in range(1, len(data) + 1):
        file.write(f"file 'temp_files/slide_{slide_number}_video.mp4'\n")

# Combine all the video files into one final video
final_video_file = 'final_video.mp4'
command = f'ffmpeg -f concat -safe 0 -i temp_files/file_list.txt -c copy {final_video_file}'
subprocess.run(command, shell=True)

# Delete the temp_files directory
shutil.rmtree('temp_files')

