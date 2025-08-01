from pydantic import BaseModel, Field


class GenerationResult(BaseModel):
    """
    Result of commit message generation
    """

    message: str = Field(description="The generated commit message")


class GenerationRequest(BaseModel):
    """Request for commit message generation"""

    repo_path: str = Field(default=".", description="Path to git repository")
