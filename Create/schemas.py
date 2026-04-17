from pydantic import BaseModel

class ProfileCreate(BaseModel):
    name: str

class ProfileResponse(BaseModel):
    status: str
    data: dict