from loaders import DocumentLoader
import logging
import sys , os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..","..")))

from qdrant_client import QdrantClient
from src.configs import env_config

client = QdrantClient(
    url=env_config.qdrant_url,
    api_key=env_config.qdrant_api_key,
    check_compatibility=False,
)

info = client.get_collection("documents")
print(info)