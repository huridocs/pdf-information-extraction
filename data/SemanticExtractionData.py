from pydantic import BaseModel


class SemanticExtractionData(BaseModel):
    text: str
    segment_text: str
