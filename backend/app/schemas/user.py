from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, description="Updated full name")
