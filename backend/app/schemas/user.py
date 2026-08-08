from pydantic import BaseModel, EmailStr  # type: ignore[import]


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True