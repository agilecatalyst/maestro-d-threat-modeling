import logging
from typing import Optional

from langchain_core.messages import HumanMessage
from llm import get_chat_model
from diagram_loader import load_diagram_data_url
from db import update_job_summary

logger = logging.getLogger(__name__)


def _text_summary(model, description: Optional[str], diagram_path: Optional[str]) -> str:
    prompt = (
        "Summarize this software architecture in about 150 words for threat modeling. "
        f"Description: {description or 'No description provided.'}"
    )
    if diagram_path:
        prompt += f" A diagram was uploaded ({diagram_path}) but could not be analyzed visually."
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


def run_summary(job_id: str, diagram_path: Optional[str], description: Optional[str]):
    try:
        model = get_chat_model()
        summary_text = ""

        if diagram_path:
            data_url = load_diagram_data_url(diagram_path)
            if data_url:
                try:
                    message = HumanMessage(
                        content=[
                            {
                                "type": "text",
                                "text": f"Summarize this architecture in ~150 words. Description: {description}",
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ]
                    )
                    response = model.invoke([message])
                    summary_text = response.content
                except Exception as exc:
                    logger.error("Multimodal failed, falling back to text-only LLM: %s", exc)
                    summary_text = _text_summary(model, description, diagram_path)
            else:
                summary_text = _text_summary(model, description, diagram_path)
        else:
            summary_text = _text_summary(model, description, None)

        update_job_summary(job_id, summary_text, state="SUMMARIZED")

    except Exception as exc:
        logger.error("Worker error for job %s: %s", job_id, exc)
        update_job_summary(job_id, f"Error: {str(exc)}", state="FAILED")
