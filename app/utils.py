from fastapi import HTTPException, status
from fastapi import UploadFile
from python_docx import Document
from PyPDF2 import PdfFileReader
from pptx import Presentation
import io

allowed_mimes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]

async def validate_and_convert_file(file: UploadFile):
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
        doc = Document(io.BytesIO(contents))
        # TODO: Convert Word document to PDF
    elif file_mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        pres = Presentation(io.BytesIO(contents))
        # TODO: Convert PowerPoint presentation to PDF

    # check if PDF file is above 50 pages
    if file_mime_type == "application/pdf":
        reader = PdfFileReader(io.BytesIO(contents))
        if reader.getNumPages() > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF file must not be more than 50 pages",
            )

    return file