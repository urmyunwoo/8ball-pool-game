from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email:    str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    nickname:     str
    user_id:      int


class UserInfo(BaseModel):
    id:       int
    email:    str
    nickname: str
