from pydantic import BaseModel, ConfigDict, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)
