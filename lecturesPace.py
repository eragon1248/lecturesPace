import base64
import os
import requests
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader
from dotenv import load_dotenv
import json

# Load the .env file
load_dotenv()

# Get the API key
api_key = os.getenv('OPENAI_API_KEY')

filename = 'CS376_Lecture_7.pdf'

# Function to encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Open the PDF file
pdf_file = PdfFileReader(open(filename, 'rb'))

# Get the number of pages in the PDF
num_pages = pdf_file.getNumPages()

# Initialize a list to store responses
responses = []

# Parameters for the API
seconds_per_slide = 30

# Loop through each page
for page in range(num_pages):
    # Convert the page to an image
    images = convert_from_path(filename, dpi=300, first_page=page+1, last_page=page+1)

    # Save the image to a file
    image_path = f'page_{page+1}.png'
    images[0].save(image_path, 'PNG')

    try:
        # Encode the image to base64
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Can you explain the content of this slide as if you were teaching a class? Jump straight into the content and don't worry about introducing the topic. The output is intended to be used as a script for a video lecture throught Text To Speech with approximately {seconds_per_slide} seconds per slide, so don't include any special characters and such that will be read unnaturally."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        # Send the image to the GPT-4 Vision API
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        # Get the response from the API and store it
        responses.append(response.json())
        print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Delete the temporary image file
        os.remove(image_path)

# Save all responses to a JSON file
with open('responses.json', 'w', encoding='utf-8') as f:
    json.dump(responses, f, ensure_ascii=False, indent=4)
