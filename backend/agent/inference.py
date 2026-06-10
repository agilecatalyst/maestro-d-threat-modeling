import os
import httpx
from typing import Dict, Any

def check_inference() -> Dict[str, Any]:
    base_url = os.getenv("INFERENCE_BASE_URL")
    api_key = os.getenv("INFERENCE_API_KEY")
    local_model = os.getenv("LOCAL_MODEL", "")

    if not base_url:
        return {
            "status": "disconnected",
            "service": "maestro-d-agent",
            "error": "INFERENCE_BASE_URL not set",
        }

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base_url.rstrip('/')}/models", headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Expecting a list of models, handle different possible structures
            models_list = data if isinstance(data, list) else data.get("data", [])
            models_count = len(models_list)
            
            model_loaded = False
            if local_model:
                model_loaded = any(local_model in str(m.get("id", "")) for m in models_list)

            return {
                "status": "connected",
                "service": "maestro-d-agent",
                "inference_base_url": base_url,
                "local_model": local_model,
                "models_count": models_count,
                "model_loaded": model_loaded
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "service": "maestro-d-agent",
            "inference_base_url": base_url,
            "local_model": local_model,
            "models_count": 0,
            "model_loaded": False,
            "error": str(e),
        }