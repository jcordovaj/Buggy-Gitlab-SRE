from typing import Optional
from pydantic_settings import BaseSettings

class EnvSettings(BaseSettings):
    gitlab_token: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
