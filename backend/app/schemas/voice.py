from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VoiceTurnRequest(BaseModel):
    transcript: str = Field(..., description="Student spoken or text utterance")
    session_id: Optional[str] = None
    current_topic: str = Field(default="Operating Systems", description="Active learning topic")
    current_subject: str = Field(default="Operating Systems", description="Subject name")
    image_data: Optional[str] = Field(default=None, description="Base64 encoded image or diagram data")
    image_filename: Optional[str] = None
    document_id: Optional[str] = None
    page_number: Optional[int] = None


class VoiceTurnResponse(BaseModel):
    session_id: str
    intent: str
    teacher_reply_text: str
    spoken_text: str
    pedagogical_state: str
    concept_title: Optional[str] = None
    multimodal_analysis: Optional[Dict[str, Any]] = None
    suggested_quick_actions: List[str] = []
    citations: List[Dict[str, Any]] = []


class MultimodalAnalyzeRequest(BaseModel):
    image_data: Optional[str] = None
    image_filename: Optional[str] = None
    user_prompt: Optional[str] = None
    current_topic: str = "Operating Systems"
    document_id: Optional[str] = None
    page_number: Optional[int] = None


class MultimodalAnalyzeResponse(BaseModel):
    image_type: str
    detected_topic: str
    title: str
    visual_elements: List[str]
    extracted_text: str
    conceptual_explanation: str
    spoken_script: str
    check_question: str
    suggested_voice_prompts: List[str]
    rag_citations: List[Dict[str, Any]] = []


class TranscribeAudioResponse(BaseModel):
    transcript: str
    confidence: float
    detected_language: str


class SynthesizeSpeechRequest(BaseModel):
    text: str
    voice_speed: float = 1.0


class SynthesizeSpeechResponse(BaseModel):
    spoken_text: str
    audio_format: str
    audio_url: str
    duration_seconds: float
