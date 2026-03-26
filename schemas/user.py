from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    is_admin: bool = False


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool
    device_id: str | None

    class Config:
        from_attributes = True


class UserActiveUpdate(BaseModel):
    is_active: bool
