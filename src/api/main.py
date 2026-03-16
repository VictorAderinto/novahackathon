from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agents.orchestrator import Orchestrator
import pandapower as pp

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class SystemState:
    orchestrator: Orchestrator = None
    current_case: str = None

state_store = SystemState()

class LoadCaseRequest(BaseModel):
    case_name: str

class ChatRequest(BaseModel):
    message: str

def get_network_stats(net):
    """Extracts high-level stats from the pandapower network."""
    try:
        load_mw = net.load.p_mw.sum()
        gen_mw = net.gen.p_mw.sum() + net.sgen.p_mw.sum() if 'sgen' in net else net.gen.p_mw.sum()
        
        # Simple voltage checks (0.95 - 1.05 pu)
        min_vm = net.res_bus.vm_pu.min() if 'res_bus' in net and not net.res_bus.empty else 1.0
        max_vm = net.res_bus.vm_pu.max() if 'res_bus' in net and not net.res_bus.empty else 1.0
        
        line_loading_max = net.res_line.loading_percent.max() if 'res_line' in net and not net.res_line.empty else 0.0
        
        voltage_violations = len(net.res_bus[(net.res_bus.vm_pu < 0.95) | (net.res_bus.vm_pu > 1.05)]) if 'res_bus' in net and not net.res_bus.empty else 0
        current_violations = len(net.res_line[net.res_line.loading_percent > 100.0]) if 'res_line' in net and not net.res_line.empty else 0

        return {
            "n_buses": len(net.bus),
            "n_lines": len(net.line),
            "total_load_mw": round(load_mw, 2),
            "total_gen_mw": round(gen_mw, 2),
            "min_voltage_pu": round(min_vm, 3),
            "max_voltage_pu": round(max_vm, 3),
            "max_line_loading_pct": round(line_loading_max, 2),
            "voltage_violations": voltage_violations,
            "current_violations": current_violations
        }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/cases")
def list_cases():
    return {"cases": ["case57", "case118", "case14"]}

@app.post("/load")
def load_case(req: LoadCaseRequest):
    try:
        state_store.orchestrator = Orchestrator(network_name=req.case_name, n_clusters=3)
        state_store.current_case = req.case_name
        
        # Run initial power flow to get stats
        pp.runpp(state_store.orchestrator.net)
        
        stats = get_network_stats(state_store.orchestrator.net)
        return {"status": "success", "message": f"Loaded {req.case_name}", "stats": stats}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(req: ChatRequest):
    if not state_store.orchestrator:
        raise HTTPException(status_code=400, detail="No case loaded. Please load a case first.")
    
    query = req.message
    orch = state_store.orchestrator
    
    try:
        # Determine intent (Reuse logic from main.py or just try modification first?)
        # Let's use the simple keyword heuristic from main.py
        modification_keywords = ["outage", "modify", "increase", "decrease", "set", "create case", "disconnect", "change", "simulate"]
        
        response_text = ""
        if any(k in query.lower() for k in modification_keywords):
            response_text = orch.process_scenario_modification(query)
        else:
            response_text = orch.process_user_query(query)
            
        # Get updated stats (in case modification happened)
        stats = get_network_stats(orch.net)
        
        return {
            "response": response_text,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (React build)
# Assumes build is in ../../web/dist relative to this file
# AND that the Dockerfile copies it to /app/web/dist or similar
# We'll use a relative path here that works locally AND in Docker if structured right.
# In Docker: /app/web/dist
# Locally: ../../web/dist

# Construct absolute path to static folder
import pathlib
static_path = pathlib.Path(__file__).parent.parent.parent / "web" / "dist"

if static_path.exists():
    app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")

    # Catch-all for SPA (return index.html)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index_file = static_path / "index.html"
        if index_file.exists():
             return FileResponse(index_file)
        return {"error": "Frontend not built. Run 'npm run build' in web/"}
else:
    print(f"Warning: Static files not found at {static_path}. Frontend will not be served.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

