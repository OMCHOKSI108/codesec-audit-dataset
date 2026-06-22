from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of results")


class SearchResultItem(BaseModel):
    rank: int
    score: float
    title: str = ""
    section_title: str = ""
    cwe_id: str = ""
    content: str = ""
    source_file: str = ""


class SearchMetadata(BaseModel):
    embedding_model: str
    dataset_repo: str
    total_chunks: int = 0
    query_time_ms: float = 0.0


class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[SearchResultItem] = Field(default_factory=list)
    metadata: SearchMetadata
