from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    title_ja: str = Field(min_length=1, max_length=120)
    supplement_ja: str = Field(min_length=1, max_length=240)
    category: str = Field(min_length=1, max_length=80)
    importance_score: float = Field(ge=0.0, le=1.0)
