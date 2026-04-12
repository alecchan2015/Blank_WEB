from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    credits: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class LLMConfigCreate(BaseModel):
    name: str
    provider: str  # "openai", "anthropic", "volcano"
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    agent_type: str  # "strategy", "brand", "operations", "all"


class LLMConfigOut(BaseModel):
    id: int
    name: str
    provider: str
    model_name: str
    base_url: Optional[str]
    agent_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCreate(BaseModel):
    agent_type: str
    title: str
    content: str


class KnowledgeOut(BaseModel):
    id: int
    agent_type: str
    title: str
    content: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    query: str
    agents_selected: List[str]
    brand_name: Optional[str] = None


class TaskResultOut(BaseModel):
    id: int
    agent_type: str
    content: Optional[str]
    file_type: Optional[str]
    file_name: Optional[str]
    download_credits: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    query: str
    agents_selected: List[str]
    status: str
    brand_name: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    results: List[TaskResultOut] = []

    class Config:
        from_attributes = True


class UserCreditsUpdate(BaseModel):
    credits: int
    reason: Optional[str] = "管理员调整"


class UserStatusUpdate(BaseModel):
    is_active: bool
