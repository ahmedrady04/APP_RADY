import json

from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from dependencies.auth import get_current_user
from services.gemini import process_audio

router = APIRouter(
    prefix="/api",
    tags=["audio"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/process")
async def process(
    api_key:       str        = Form(...),
    model_name:    str        = Form("gemini-2.5-flash"),
    recorder_name: str        = Form(""),
    sheet_name:    str        = Form("بيانات المركبات"),
    gps_data:      str        = Form("[]"),
    audio:         UploadFile = File(...),
):
    api_key    = api_key.strip()
    model_name = model_name.strip() or "gemini-2.5-flash"

    if not api_key:
        raise HTTPException(status_code=400, detail="أدخل مفتاح Gemini API")

    try:
        gps_points = json.loads(gps_data)
    except Exception:
        gps_points = []

    file_content = await audio.read()

    try:
        plates = await process_audio(
            file_content=file_content,
            filename=audio.filename or "audio.mp3",
            api_key=api_key,
            model_name=model_name,
            recorder_name=recorder_name.strip(),
            sheet_name=sheet_name.strip(),
            gps_points=gps_points,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse({"plates": plates, "total": len(plates)})