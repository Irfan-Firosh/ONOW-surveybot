from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from processor import Processor

router = APIRouter()
processor = Processor("EFI_seed_cleaned.db")


class Chat(BaseModel):
    message: str


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.get("/chat")
async def chat(message: str):     
    response = processor.create_query(message)
    data = processor.execute_query(response)
    data = data.to_dict()
    return {"message": response, "data": data}