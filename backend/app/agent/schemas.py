from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """A single file modification proposed by the LLM."""

    path: str = Field(
        description="Path relative to the repository root."
    )

    content: str = Field(
        min_length=1,
        description=(
            "Complete new content for the file. "
            "Must not be empty."
        ),
    )


class CodeChangePlan(BaseModel):
    """Structured code modification plan."""

    changes: list[FileChange] = Field(
        default_factory=list,
        description="Files that should be created or modified.",
    )

    test_command: str = Field(
        default="pytest -q",
        description="Command used to test the changes.",
    )