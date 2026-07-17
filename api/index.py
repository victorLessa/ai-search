import os
import tempfile
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel
import pymupdf4llm
from sentence_transformers import SentenceTransformer
from supabase import create_client
    
app = FastAPI()

ALLOWED_CONTENT_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

class DocumentInput(BaseModel):
    title: str
    body: str


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


@app.post("/api/documents/embed", status_code=201)
async def embed_and_store_document(doc: DocumentInput):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_URL or SUPABASE_KEY environment variable is not configured.",
        )

    model = SentenceTransformer("Supabase/gte-small")
    embedding = model.encode(doc.body, normalize_embeddings=True).tolist()

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.from_("documents").insert({
        "title": doc.title,
        "body": doc.body,
        "embedding": embedding,
    }).execute()

    return JSONResponse(status_code=201, content={"data": result.data})


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "João"}


@app.post("/api/items")
def create_item(item: dict):
    return {"created": item}


# Handler para o runtime serverless da Vercel
handler = Mangum(app)