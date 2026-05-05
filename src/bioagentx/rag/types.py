from pydantic import BaseModel, Field


class BioPaper(BaseModel):
    """A biomedical research paper with metadata for retrieval and filtering."""

    paper_id: str
    title: str
    abstract: str
    source_url: str
    year: int
    gene: str | None = None
    disease: str | None = None
    document_type: str = "paper"
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievalFilter(BaseModel):
    """Metadata filters applied during retrieval."""

    gene: str | None = None
    disease: str | None = None
    document_type: str | None = None


class RagHit(BaseModel):
    """A single retrieval result with scoring breakdown."""

    paper: BioPaper
    score: float
    vector_score: float
    keyword_score: float
    rationale: str
