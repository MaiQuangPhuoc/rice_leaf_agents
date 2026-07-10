# from pydantic_settings import BaseSettings
# from typing import Literal
# import os , sys 
# # ==

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# class EnvConfig(BaseSettings):
#     # OpenAI API
#     # openai_api_key: str
#     api_key_tavily: str
#     api_key_weather : str
#     # google_api_key: str
#     groq_api_key: str
#     model: str
#     embedding_model: str =""
#     api_provider: Literal["openai", "anthropic", "google", "groq"] = "groq"
#     # api_provider: Literal["openai", "anthropic", "google", "groq"] = "google"


#     # MongoDB
#     # mongodb_uri: str = "mongodb://localhost:27017"
    
#     # #QdrantDB
#     # qdrant_url: str = "http://localhost:6333"  
#     qdrant_url: str 
#     qdrant_api_key: str  
    
#     # Logging
#     console_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
#     file_log_format: str = "%(asctime)s %(levelname)s %(message)s"
#     console_log_format: str = "%(levelname)s %(message)s"
    
#     class Config:
#         env_file = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\.env"

# env_config = EnvConfig()

# # Setup logging after config is loaded
# from src.app_logging import setup_logging
# setup_logging()
# print(env_config.model)
# print(env_config.groq_api_key)
# # print(env_config.qdrant_api_key)

# # print(env_config.api_key_tavily)
# # print(env_config.api_key_weather)


from pydantic_settings import BaseSettings
from typing import Literal, Optional
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class EnvConfig(BaseSettings):
    # ── API keys (để trống nếu không dùng, không bắt buộc) ──
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # tavily/weather giữ optional luôn cho an toàn
    api_key_tavily: Optional[str] = None
    api_key_weather: Optional[str] = None

    # ── chọn provider đang dùng ──
    api_provider: Literal["openai", "groq", "openrouter"] = "groq"

    model: str
    embedding_model: str = ""

    qdrant_url: str
    qdrant_api_key: str

    console_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    file_log_format: str = "%(asctime)s %(levelname)s %(message)s"
    console_log_format: str = "%(levelname)s %(message)s"

    class Config:
        env_file = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\.env"
        extra = "ignore"

env_config = EnvConfig()

from src.app_logging import setup_logging
setup_logging()
print(env_config.model)
print(env_config.openrouter_api_key)