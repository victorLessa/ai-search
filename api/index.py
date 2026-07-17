import os
import tempfile
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from mangum import Mangum
import pymupdf4llm

app = FastAPI()

ALLOWED_CONTENT_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}


@app.get("/api")
def root():
    return {"message": "Hello from FastAPI on Vercel!"}


@app.post("/api/documents/convert", status_code=200)
async def convert_document_to_markdown(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()

    if file.content_type not in ALLOWED_CONTENT_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF files are accepted.",
        )

    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        markdown = pymupdf4llm.to_markdown(tmp_path)
    finally:
        os.unlink(tmp_path)

    return JSONResponse(
        content={
            "filename": file.filename,
            "content_type": file.content_type,
            "markdown": markdown,
        }
    )


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "João"}


@app.post("/api/items")
def create_item(item: dict):
    return {"created": item}


# Handler para o runtime serverless da Vercel
handler = Mangum(app)
