import logging
from typing import Optional

from langchain_core.messages import HumanMessage
from llm import get_chat_model
from diagram_loader import load_diagram_data_url
from db import update_job_summary

logger = logging.getLogger(__name__)


def run_summary(job_id: str, diagram_path: Optional[str], description: Optional[str]):
    try:
        model = get_chat_model()

        summary_text = ""
        
        # R1: Multimodal call with fallback
        if diagram_path:
            data_url = load_diagram_data_url(diagram_path)
            if data_url:
                try:
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": f"Summarize this architecture in ~150 words. Description: {description}"},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    )
                    response = model.invoke([message])
                    summary_text = response.content
                except Exception as e:
                    logger.error(f"Multimodal failed, falling back to text: {e}")
                    summary_text = f"Architecture summary (text fallback): {description} (Diagram: {diagram_path})"
            else:
                summary_text = f"Architecture summary (no image found): {description}"
        else:
            summary_text = f"Architecture summary (no diagram provided): {description}"

        # R2: Plain text response (handled by LLM prompt/logic)
        update_job_summary(job_id, summary_text, state="SUMMARIZED")
        
    except Exception as e:
        logger.error(f"Worker error for job {job_id}: {e}")
        update_job_summary(job_id, f"Error: {str(e)}", state="FAILED")