import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_chat_model():
    timeout = float(os.getenv("INFERENCE_REQUEST_TIMEOUT_SEC", "180"))
    return ChatOpenAI(
        base_url=os.getenv("INFERENCE_BASE_URL"),
        api_key=os.getenv("INFERENCE_API_KEY"),
        model=os.getenv("LOCAL_MODEL"),
        request_timeout=timeout,
    )
