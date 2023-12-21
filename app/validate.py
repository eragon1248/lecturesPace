from fastapi import HTTPException, status, UploadFile
from docx2pdf import convert as docx2pdf
from PyPDF2 import PdfFileReader
import os
import subprocess

allowed_mimes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]

async def validate_and_convert_file(pdf_path: str, file: UploadFile):
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

    # check file MIME type
    file_mime_type = file.content_type
    if file_mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_mime_type}. Supported types are: {allowed_mimes}",
        )

    # convert file to PDF if it is in Word or PowerPoint
    if file_mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with open("temp_files/temp.docx", "wb") as temp_file:
            temp_file.write(contents)
        docx2pdf("temp_files/temp.docx", pdf_path)
        os.remove("temp_files/temp.docx")
    elif file_mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        with open("temp_files/temp.pptx", "wb") as temp_file:
            temp_file.write(contents)
        subprocess.run(["ppt2pdf", "file", pdf_path], check=True)
        os.remove("temp_files/temp.pptx")
    else:  # If the file is already a PDF
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