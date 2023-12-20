import base64
import os
import requests
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader
from dotenv import load_dotenv
import json
from typing import List

def getScript(filename: str, lecture_title: str, elaboration: str):
    # Load the .env file
    load_dotenv()

    # Get the API key
    api_key = os.getenv("OPENAI_API_KEY")

    # Function to encode image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Open the PDF file
    pdf_file = PdfFileReader(open(filename, "rb"))

    # Get the number of pages in the PDF
    num_pages = pdf_file.getNumPages()

    # Initialize a list to store responses
    responses = []

    # Initialize the previous response
    previous_response = '(This is the first slide)'

    # Loop through each page
    for page in range(num_pages):
        # Convert the page to an image
        images = convert_from_path(
            filename, dpi=300, first_page=page + 1, last_page=page + 1
        )

        # Save the image to a file
        image_path = f"page_{page+1}.png"
        images[0].save(image_path, "PNG")

        try:
            # Encode the image to base64
            base64_image = encode_image(image_path)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text" : f'''Can you explain the content of this slide as if you were conducting a lecture? 
                                Jump straight into the content and don't worry about introducing the topic. 
                                The output is intended to be passed through Text To Speech as page {page + 1} of a lecture titled {lecture_title}.
                                The explanation is intended to be {elaboration}. 
                                Don't include any special characters and such that will be read unnaturally by gTTS. 
                                If this is a Title slide, simply read out the title.
                                This is the response from the previous slide for context/transition: {previous_response}'''
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
            }

            # Send the image to the GPT-4 Vision API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
            )

            # Get the response from the API and store it
            responses.append(response.json())
            previous_response = response.json()['choices'][0]['message']['content']
            print( f'Page {page + 1}: {previous_response}\n\n')

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Delete the temporary image file
            os.remove(image_path)

        # return responses as json
        return responses
