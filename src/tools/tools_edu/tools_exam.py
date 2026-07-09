import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..","..")))
import json
from langchain_core.tools import tool
from src.state_edu import StudentProfile
from src.clients.llm import LLMClient


