from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.voice.service import VoiceService
from app.multimodal.service import MultimodalService
from app.search.hybrid import KnowledgeSearchService
from app.schemas.voice import (
    VoiceTurnRequest,
    VoiceTurnResponse,
    MultimodalAnalyzeRequest,
    MultimodalAnalyzeResponse,
    TranscribeAudioResponse,
    SynthesizeSpeechRequest,
    SynthesizeSpeechResponse,
)

router = APIRouter(tags=["Voice & Multimodal Teacher"])


@router.post("/voice/chat", response_model=VoiceTurnResponse)
async def process_voice_dialogue_turn(
    request: VoiceTurnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Main voice conversation endpoint: accepts student speech, text, diagram, or page inquiry,
    routes through the Socratic Teaching Engine, and produces formatted text + natural spoken speech.
    """
    try:
        search_service = KnowledgeSearchService(db)
        service = VoiceService(db_session=db, search_service=search_service)
        result = await service.process_voice_turn(
            user_id=current_user.id,
            transcript=request.transcript,
            session_id=request.session_id,
            current_topic=request.current_topic,
            current_subject=request.current_subject,
            image_data=request.image_data,
            image_filename=request.image_filename,
            document_id=request.document_id,
            page_number=request.page_number,
        )
        return VoiceTurnResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice dialogue turn: {str(e)}",
        )


@router.post("/voice/transcribe", response_model=TranscribeAudioResponse)
async def transcribe_audio_stream(
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Speech-to-text endpoint: transcribes recorded student audio.
    """
    try:
        service = VoiceService(db_session=db)
        audio_bytes = await file.read() if file else b""
        result = await service.transcribe_speech(audio_data=audio_bytes)
        return TranscribeAudioResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe audio: {str(e)}",
        )


@router.post("/voice/synthesize", response_model=SynthesizeSpeechResponse)
async def synthesize_teacher_speech(
    request: SynthesizeSpeechRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Text-to-speech synthesis endpoint: produces speech audio and phoneme duration.
    """
    try:
        service = VoiceService(db_session=db)
        result = await service.synthesize_speech(text=request.text, voice_speed=request.voice_speed)
        return SynthesizeSpeechResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synthesize speech: {str(e)}",
        )


@router.post("/multimodal/analyze", response_model=MultimodalAnalyzeResponse)
async def analyze_study_material_image(
    request: MultimodalAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyzes student study visuals: diagrams, handwritten notes, formulas, code, and textbook pages.
    """
    try:
        search_service = KnowledgeSearchService(db)
        service = MultimodalService(db_session=db, search_service=search_service)
        result = await service.analyze_study_image(
            user_id=current_user.id,
            image_data=request.image_data,
            image_filename=request.image_filename,
            user_prompt=request.user_prompt,
            current_topic=request.current_topic,
            document_id=request.document_id,
            page_number=request.page_number,
        )
        return MultimodalAnalyzeResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze study image: {str(e)}",
        )
