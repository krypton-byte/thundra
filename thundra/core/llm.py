from langchain_openai import AzureChatOpenAI, ChatOpenAI
import os
from ..config import config_toml
from thundra.config import config_toml

azure = config_toml.get("openai", {}).get("azure")
if isinstance(azure, dict) and azure.get("api_key"):
    openai_auth = config_toml["openai"]["azure"]
    os.environ["AZURE_OPENAI_API_KEY"] = openai_auth["api_key"]
    os.environ["AZURE_OPENAI_ENDPOINT"] = openai_auth["endpoint"]
    os.environ["OPENAI_API_VERSION"] = openai_auth["api_version"]
    llm = AzureChatOpenAI(
        deployment_name=openai_auth["deployment_name"],
        model_name=openai_auth["model_name"],
    )
else:
    os.environ["OPENAI_API_KEY"] = config_toml["openai"]["openai"]["api_key"]
    llm = ChatOpenAI(temperature=0)
