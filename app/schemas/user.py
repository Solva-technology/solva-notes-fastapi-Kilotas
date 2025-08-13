from pydantic import BaseModel, EmailStr, ConfigDict


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)
