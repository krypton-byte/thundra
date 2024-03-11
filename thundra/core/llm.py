from langchain_openai import AzureChatOpenAI
import os
from ..config import config_toml
from thundra.config import config_toml

openai_auth = config_toml["openai"]["auth"]
os.environ["AZURE_OPENAI_API_KEY"] = openai_auth["api_key"]
os.environ["AZURE_OPENAI_ENDPOINT"] = openai_auth["endpoint"]
os.environ["OPENAI_API_VERSION"] = openai_auth["api_version"]
llm = AzureChatOpenAI(
    deployment_name=openai_auth["deployment_name"],
    model_name=openai_auth["model_name"],
)
