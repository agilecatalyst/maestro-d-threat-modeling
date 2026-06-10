from fastapi import FastAPI
from fastapi.responses import JSONResponse
from inference import check_inference
from routes.invocations import router as invocations_router
from routes.scan_flow import router as scan_flow_router
from workflow_graph import pipeline_graph

app = FastAPI(title="Maestro'D Agent")

@app.get("/ping")
async def ping():
    return {"status": "Healthy", "service": "maestro-d-agent"}

@app.get("/inference/health")
async def inference_health():
    result = check_inference()
    if result["status"] == "disconnected":
        return JSONResponse(status_code=503, content=result)
    return result

@app.get("/workflow")
async def workflow():
    graph = pipeline_graph.get_graph()
    return {
        "engine": "langgraph",
        "nodes": [name for name in graph.nodes.keys() if name not in ("__start__", "__end__")],
        "threats_subgraph": ["generate", "gap"],
    }

app.include_router(invocations_router)
app.include_router(scan_flow_router)