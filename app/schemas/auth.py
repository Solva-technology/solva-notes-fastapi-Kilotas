from pydantic import BaseModel, ConfigDict, EmailStr  # алфавит внутри строки


class Credentials(BaseModel):
    email: EmailStr
    password: str


class RegisterIn(Credentials):
    pass


class LoginIn(Credentials):
    pass


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
