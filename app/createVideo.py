import json
from gtts import gTTS
from pdf2image import convert_from_path
import os
import subprocess
from datetime import timedelta
import shutil
import re


def createVideo(file_dir: str, video_path: str, script, speedup: float):

    # Convert the PDF to a list of images
    images = convert_from_path(file_dir)

    # Save the images to files
    image_files = []
    for i, image in enumerate(images):
        image_file = f'temp_files/slide_{i + 1}.png'
        image.save(image_file, 'PNG')
        image_files.append(image_file)
        

    def format_srt_time(timedelta_obj):
        """Convert a timedelta object into a string in SRT timestamp format."""
        total_seconds = int(timedelta_obj.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = timedelta_obj.microseconds // 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    # Initialize a list to store the video clips
    clips = []

    for i, response in enumerate(script):
        slide_number = i + 1

        # Extract the content from the response and remove newine
        content = response.replace('\n', ' ')  # Replace newline characters with spaces
        
        # Split the content into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        print (sentences)

        # Convert each sentence to speech and create a text clip for each sentence
        audio_files = []
        subtitles = []
        total_duration = timedelta()
        for j, sentence in enumerate(sentences):
            # Convert the sentence to speech
            tts = gTTS(text=sentence, lang="en")
            audio_file = f'temp_files/slide_{slide_number}_sentence_{j + 1}.mp3'
            tts.save(audio_file)

            # Speed up the audio
            fast_audio_file = f'temp_files/slide_{slide_number}_sentence_{j + 1}_fast.mp3'
            subprocess.call(['ffmpeg', '-i', audio_file, '-filter:a', f'atempo={speedup}', fast_audio_file])

            # Get the duration of the audio file
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', fast_audio_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            duration = timedelta(seconds=float(result.stdout))

            # Add the subtitle
            start_time = format_srt_time(total_duration)
            end_time = format_srt_time(total_duration + duration)
            subtitles.append(f"{j + 1}\n{start_time} --> {end_time}\n{sentence}\n\n")

            total_duration += duration
            audio_files.append(fast_audio_file)

        # Write the subtitles to a .srt file
        with open(f'temp_files/slide_{slide_number}.srt', 'w', encoding='utf-8') as f:
            f.writelines(subtitles)

        # Create a text file listing all the audio files
        with open('temp_files/concat_list.txt', 'w') as f:
            for audio_file in audio_files:
                # Remove the 'temp_files/' prefix from the filename
                filename = audio_file.replace('temp_files/', '')
                f.write(f"file '{filename}'\n")

        # Concatenate all audio files into a single audio file
        final_audio_file = f'temp_files/slide_{slide_number}_final.mp3'
        subprocess.call(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'temp_files/concat_list.txt', '-acodec', 'copy', final_audio_file])

        # Create a video clip from the image and audio
        video_file = f'temp_files/slide_{slide_number}_video.mp4'
        subprocess.call(['ffmpeg', '-loop', '1', '-i', image_files[i], '-i', final_audio_file, '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-shortest', video_file])

        # Add subtitles to the video
        subtitled_video_file = f'temp_files/slide_{slide_number}_subtitled.mp4'
        subtitle_file = f'temp_files/slide_{slide_number}.srt'
        subprocess.call(['ffmpeg', '-i', video_file, '-vf', f'subtitles={subtitle_file}', subtitled_video_file])

        clips.append(subtitled_video_file)

    # Create a text file listing all the video clips
    with open('temp_files/concat_list.txt', 'w') as f:
        for clip in clips:
            # Remove the 'temp_files/' prefix from the filename
            filename = clip.replace('temp_files/', '')
            f.write(f"file '{filename}'\n")

    # Concatenate all video clips into a single video
    subprocess.call(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'temp_files/concat_list.txt', '-c', 'copy', video_path])