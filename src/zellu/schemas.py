from pydantic import BaseModel, Field
from typing import Any, Dict, List

class WebhookInput(BaseModel):
    message: str = Field(..., description="Texto livre do usuário/cliente")
    metadata: Dict[str, Any] | None = None

class Recommendation(BaseModel):
    option: str
    score: float
    reason: str

class AnalysisData(BaseModel):
    problem: str
    rights: List[str]
    estimatedValue: float
    recommendations: List[Recommendation]

class WebhookResponse(BaseModel):
    status: str
    conv_id: str
    analysis_data: AnalysisData | None = None
    echo: Dict[str, Any] | None = None
