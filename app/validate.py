from fastapi import HTTPException, status, UploadFile
from docx2pdf import convert as docx2pdf
from pptxtopdf import convert as pptxtopdf
from PyPDF2 import PdfFileReader
import os
import subprocess


# Define the allowed values for tempo and conciseness
allowed_tempos = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2]
allowed_conciseness = ["concise", "medium", "verbose"]
allowed_mimes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]

async def validate_and_convert_file(pdf_path: str, file: UploadFile, tempo: float, conciseness: str):
    # check file size
    contents = await file.read()
    size = len(contents)
    MB = 1024**2
    if not 0 < size <= 5 * MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be between 1 and 5 MB",
        )
    await file.seek(0)

    # Validate tempo
    if tempo not in allowed_tempos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tempo: {tempo}. Allowed tempos are: {allowed_tempos}",
        )

    # Validate conciseness
    if conciseness not in allowed_conciseness:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conciseness: {conciseness}. Allowed conciseness levels are: {allowed_conciseness}",
        )
    
    # check file MIME type
    file_mime_type = file.content_type
    if file_mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_mime_type}. Supported types are: {allowed_mimes}",
        )

    # Convert Word doc to pdf
    if file_mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with open("temp_files/temp.docx", "wb") as temp_file:
            temp_file.write(contents)
        docx2pdf("temp_files/temp.docx", pdf_path)
        os.remove("temp_files/temp.docx")

    # Convert PowerPoint presentation to pdf
    elif file_mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        with open("temp_files/temp.pptx", "wb") as temp_file:
            temp_file.write(contents)
        pptxtopdf("temp_files", "temp_files")
        os.remove("temp_files/temp.pptx")
        os.rename("temp_files/temp.pdf", pdf_path)
    
    # If the file is already a PDF
    else:  
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(contents)

    # check if PDF file is above 50 pages
    with open(pdf_path, "rb") as pdf_file:
        reader = PdfFileReader(pdf_file)
        if reader.getNumPages() > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF file must not be more than 50 pages",
            )
        reader.stream.close()  # Close the PdfFileReader object