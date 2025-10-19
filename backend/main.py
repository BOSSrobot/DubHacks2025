# app.py
from __future__ import annotations
import os
import re
import glob
import json
import subprocess
from typing import List, Optional

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- at top-level (near your globals) ---
import asyncio, concurrent.futures, threading
import time
from pathlib import Path
from enum import Enum
from training_manager import TrainingManagerConda
from vllm_manager import VLLMServerConda

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)  # serialize startups

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass  # Client disconnected

manager = ConnectionManager()

class ModelStatus(str, Enum):
    idle = "idle"
    starting = "starting"
    ready = "ready"
    error = "error"

class TrainingStatus(str, Enum):
    idle = "idle"
    starting = "starting"
    running = "running"
    completed = "completed"
    failed = "failed"

status_lock = threading.Lock()
model_status: ModelStatus = ModelStatus.idle
status_detail: str | None = None

training_lock = threading.Lock()
training_status: TrainingStatus = TrainingStatus.idle
training_detail: str | None = None

pull_data_lock = threading.Lock()
pull_data_status: str = "idle"
pull_data_log_file: str | None = None

log_streaming_lock = threading.Lock()
log_streaming_active: bool = False
log_streaming_file: str | None = None
log_streaming_task: Optional[asyncio.Task] = None
log_streaming_pattern: str | None = None

current_model_config: Optional[ModelConfig] = None
current_inference_process: Optional[VLLMServerConda] = None
current_future: Optional[concurrent.futures.Future] = None
current_training_process: Optional[TrainingManagerConda] = None
current_training_future: Optional[concurrent.futures.Future] = None

# ========== Existing FastAPI app base ==========
app = FastAPI(title="Merged Backend (FastAPI)", version="1.0.0")

# CORS (match your Flask CORS and keep open for dev)
ALLOWED_ORIGINS = [
    "http://159.26.94.16:3000",
    "http://localhost:3000",
    "*",  # tighten in prod
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Models (existing FastAPI types) ======
class ButtonDataItem(BaseModel):
    prompt: str
    first_option: str
    second_option: str
    first_score: float
    second_score: float

class ModelConfig(BaseModel):
    model_name: str
    model_path: str

class ModelSelectionResponse(BaseModel):
    message: str
    selected_model: ModelConfig

class TrainingConfig(BaseModel):
    dataset_name: str
    model_name: Optional[str] = None

class TrainingResponse(BaseModel):
    message: str
    training_config: TrainingConfig
    status: str


# Sample dataset (existing)
sample_dataset: List[ButtonDataItem] = [
    {
        "prompt": "generate a button",
        "first_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'blue\' }}>Yes, I want one!</button>',
        "second_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'green\' }}>Get My Husky Hoodie!</button>',
        "first_score": 1.0,
        "second_score": 0.0
    },
    {
        "prompt": "generate a button",
        "first_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'blue\' }}>Yes, I want one!</button>',
        "second_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'red\' }}>Buy Now!</button>',
        "first_score": 0.75,
        "second_score": 0.25
    },
    {
        "prompt": "generate a button",
        "first_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'green\' }}>Get My Husky Hoodie!</button>',
        "second_option": '<button type="submit" className="w-full rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity" style={{ backgroundColor: \'red\' }}>Buy Now!</button>',
        "first_score": 0.0,
        "second_score": 1.0
    }
]  # type: ignore

def _start_model_sync(log_file_path, model_config: ModelConfig):
    """Runs in a worker thread. Blocks while vLLM spins up."""
    global current_inference_process, model_status, status_detail
    try:
        with status_lock:
            model_status = ModelStatus.starting
            status_detail = f"Starting {model_config.model_name}..."

        # stop previous if running
        if current_inference_process is not None:
            try:
                print(f"Stopping previous inference process (PID: {current_inference_process.process.pid if current_inference_process.process else 'unknown'})")
                current_inference_process.stop()
                print("Previous inference process stopped successfully")
            except Exception as e:
                print(f"Error stopping previous inference process: {e}")
                # Force cleanup
                try:
                    if current_inference_process.process and current_inference_process.process.poll() is None:
                        current_inference_process.process.kill()
                        current_inference_process.process.wait()
                        print("Force killed previous process")
                except Exception as kill_error:
                    print(f"Error force killing process: {kill_error}")

        proc = VLLMServerConda(
            model_name=model_config.model_name,
            model_path=model_config.model_path,
            log_file_path=log_file_path
        )
        proc.start()  # blocking call

        # mark ready
        with status_lock:
            current_inference_process = proc
            model_status = ModelStatus.ready
            status_detail = f"Ready: {model_config.model_name}"
    except Exception as e:
        with status_lock:
            model_status = ModelStatus.error
            status_detail = f"Startup failed: {e!r}"
        raise

def _start_training_sync(log_file_path: str, training_config: TrainingConfig):
    """Runs in a worker thread. Blocks while training completes."""
    global current_training_process, training_status, training_detail
    try:
        with training_lock:
            training_status = TrainingStatus.starting
            training_detail = f"Starting training with dataset {training_config.dataset_name}..."

        # stop previous training if running
        if current_training_process is not None:
            try:
                current_training_process.stop()
            except Exception:
                pass

        # Create training manager
        trainer = TrainingManagerConda(
            log_file_path=log_file_path,
            dataset_name=training_config.dataset_name,
            model_name=training_config.model_name,
        )
        
        # Start training
        trainer.start()
        
        with training_lock:
            current_training_process = trainer
            training_status = TrainingStatus.running
            training_detail = f"Training running with dataset {training_config.dataset_name}"

        # Wait for completion (this will block)
        success, stdout, stderr = trainer.wait_for_completion(timeout=7200)  # 2 hour timeout
        
        if success:
            with training_lock:
                training_status = TrainingStatus.completed
                training_detail = f"Training completed successfully. Output: {trainer.get_output_directory()}"
        else:
            with training_lock:
                training_status = TrainingStatus.failed
                training_detail = f"Training failed: {stderr[:200] if stderr else 'Unknown error'}"
            
    except Exception as e:
        with training_lock:
            training_status = TrainingStatus.failed
            training_detail = f"Training startup failed: {e!r}"
        raise

# ========= Existing FastAPI endpoints =========
@app.get("/")
async def root():
    return {
        "message": "Merged Backend (FastAPI)",
        "version": "1.0.0",
        "endpoints": {
            "/dataset": "GET - Returns the complete button dataset",
            "/dataset/random": "GET - Returns a random item from the dataset",
            "/choose_model": "POST - Select a model for hosting (requires ModelConfig)",
            "/current_model": "GET - Returns currently selected model configuration",
            "/available_models": "GET - Lists available model paths in the project",
            "/start_training": "POST - Start DPO training (requires TrainingConfig)",
            "/training_status": "GET - Returns current training status and details",
            # Flask-migrated paths:
            "/api/abtests": "GET - Transformed AB test data",
            "/api/basemodels": "GET - Base model list",
            "/api/finetunes": "GET - Local checkpoints",
            "/api/lossdata": "GET - Loss curves by model",
            "/api/pulldata": "POST - Trigger data pull from Statsig (non-blocking)",
            "/api/pulldata/status": "GET - Get current pull data status",
            "/api/pulldata/logs": "GET - Get full pull data logs",
            "/api/pulldata/logs/recent": "GET - Get recent pull data logs (last N lines)",
            "/ws": "WebSocket - Real-time notifications for data pull completion",
        },
        "/docs": "OpenAPI docs",
    }

@app.get("/dataset", response_model=List[ButtonDataItem])
async def get_dataset():
    return sample_dataset

@app.get("/dataset/random", response_model=ButtonDataItem)
async def get_random_item():
    import random
    return random.choice(sample_dataset)

@app.get("/dataset/{index}", response_model=ButtonDataItem)
async def get_item_by_index(index: int):
    if 0 <= index < len(sample_dataset):
        return sample_dataset[index]
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/choose_model", response_model=ModelSelectionResponse)
async def choose_model(model_config: ModelConfig):
    global current_model_config, current_future, model_status, status_detail
    model_path = f"/home/user/projects/DubHacks2025/outputs/{model_config.model_path}/fused_model"
    model_config.model_path = model_path

    log_file_path = create_log_file('training')

    
    if not os.path.exists(model_config.model_path):
        raise HTTPException(status_code=400, detail=f"Model path does not exist: {model_config.model_path}")

    current_model_config = model_config
    

    # If a previous startup is in-flight, cancel if possible
    if current_future and not current_future.done():
        # cannot truly cancel a running thread; just note it
        with status_lock:
            status_detail = "New request received; previous startup will be superseded."

    # Kick off in background thread
    loop = asyncio.get_running_loop()
    current_future = loop.run_in_executor(executor, _start_model_sync, log_file_path, model_config)

    with status_lock:
        model_status = ModelStatus.starting
        status_detail = f"Starting {model_config.model_name}..."

    # Return immediately
    return ModelSelectionResponse(
        message=f"Launching model '{model_config.model_name}' in background.",
        selected_model=model_config,
    )

@app.get("/model_status")
async def get_model_status():
    with status_lock:
        return {
            "status": model_status, 
            "detail": status_detail, 
            "selected_model": current_model_config,
            "log_file": current_inference_process.get_log_file_path() if current_inference_process else None
        }

@app.get("/current_model")
async def get_current_model():
    if current_model_config is None:
        return {"message": "No model currently selected", "selected_model": None}
    return {"message": "Current model configuration", "selected_model": current_model_config}

@app.get("/available_models")
async def list_available_models():
    model_directories = ["./outputs/*/fused_model"]
    available_models = []
    for pattern in model_directories:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                model_name = os.path.basename(os.path.dirname(path)) if "fused_model" in path else os.path.basename(path)
                available_models.append({
                    "suggested_name": model_name,
                    "path": os.path.abspath(path),
                    "type": "fused_model" if "fused_model" in path else "checkpoint"
                })
    return {"message": f"Found {len(available_models)} available model paths", "models": available_models}

async def monitor_and_stream_log_file(log_file_path: str, check_status_fn=None):
    """Monitor a log file and stream new lines as they're written
    
    Args:
        log_file_path: Path to the log file to monitor
        check_status_fn: Optional function that returns True if operation is still running
    """
    global log_streaming_active, log_streaming_file
    
    await manager.broadcast({
        "type": "log_stream_started",
        "log_file": log_file_path
    })
    
    # Follow the log file and stream new lines
    try:
        with open(log_file_path, 'r') as f:
            # Read and stream all lines as they come
            while True:
                line = f.readline()
                if line:
                    await manager.broadcast({
                        "type": "log_line",
                        "line": line.rstrip('\n')
                    })
                else:
                    # Check if operation is still running (if check function provided)
                    if check_status_fn and not check_status_fn():
                        break
                    await asyncio.sleep(0.1)
        
        await manager.broadcast({
            "type": "log_stream_ended",
            "log_file": log_file_path
        })
    except Exception as e:
        await manager.broadcast({
            "type": "log_stream_error",
            "message": f"Error streaming logs: {str(e)}"
        })
    finally:
        with log_streaming_lock:
            log_streaming_active = False
            log_streaming_file = None
            log_streaming_pattern = None

def create_log_file(prefix: str) -> str:
    """Create a new log file and return its path
    
    Args:
        prefix: Prefix for the log file (e.g., 'training', 'pull_data')
    
    Returns:
        Path to the created log file
    """
    from datetime import datetime
    
    logs_dir = Path('/home/user/projects/DubHacks2025/logs')
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file_path = logs_dir / f'{prefix}_{timestamp}.log'
    
    # Create the file
    log_file_path.touch()
    
    return str(log_file_path)

async def stream_logs(log_file_path: str, check_status_fn=None):
    """Start log streaming in background for a specific log file
    
    Args:
        log_file_path: Path to the log file to stream
        check_status_fn: Optional function that returns True if operation is still running
    """
    global log_streaming_active, log_streaming_task, log_streaming_file
    
    with log_streaming_lock:
        if log_streaming_active:
            return  # Already streaming
        log_streaming_active = True
        log_streaming_file = log_file_path
    
    # Start monitoring and streaming in background
    log_streaming_task = asyncio.create_task(monitor_and_stream_log_file(log_file_path, check_status_fn))

@app.post("/start_training", response_model=TrainingResponse)
async def start_training(training_config: TrainingConfig):
    global current_training_future, training_status, training_detail

    # Create log file and start streaming
    log_file_path = create_log_file('training')
    
    def is_training_running():
        with training_lock:
            return training_status not in [TrainingStatus.completed, TrainingStatus.failed]
    
    await stream_logs(log_file_path, is_training_running)
    
    # If a previous training is in-flight, cancel if possible
    if current_training_future and not current_training_future.done():
        with training_lock:
            training_detail = "New training request received; previous training will be superseded."

    # Kick off training in background thread
    loop = asyncio.get_running_loop()
    current_training_future = loop.run_in_executor(executor, _start_training_sync, log_file_path, training_config)

    with training_lock:
        training_status = TrainingStatus.starting
        training_detail = f"Starting training with dataset {training_config.dataset_name}..."

    # Return immediately
    return TrainingResponse(
        message=f"Starting training with dataset '{training_config.dataset_name}' in background.",
        training_config=training_config,
        status=training_status.value,
    )

@app.get("/training_status")
async def get_training_status():
    with training_lock:
        return {
            "status": training_status,
            "detail": training_detail,
            "log_file": current_training_process.get_log_file_path() if current_training_process else None,
            "training_config": {
                "dataset_name": current_training_process.dataset_name if current_training_process else None,
                "model_name": current_training_process.model_name if current_training_process else None,
                "cuda_visible_devices": current_training_process.cuda_visible_devices if current_training_process else None,
            } if current_training_process else None
        }

@app.get("/training_logs")
async def get_training_logs():
    """Get full training logs"""
    with training_lock:
        if current_training_process:
            logs, error = current_training_process.get_logs()
            if error:
                raise HTTPException(status_code=500, detail=error)
            return {"logs": logs, "log_file": current_training_process.get_log_file_path()}
        else:
            return {"logs": "No training process active", "log_file": None}

@app.get("/training_logs/recent")
async def get_recent_training_logs(lines: int = Query(50, ge=1, le=1000)):
    """Get recent training logs (last N lines)"""
    with training_lock:
        if current_training_process:
            logs, error = current_training_process.get_recent_logs(lines)
            if error:
                raise HTTPException(status_code=500, detail=error)
            return {"logs": logs, "lines": lines, "log_file": current_training_process.get_log_file_path()}
        else:
            return {"logs": "No training process active", "lines": 0, "log_file": None}

@app.get("/inference_logs")
async def get_inference_logs():
    """Get full inference/vLLM server logs"""
    with status_lock:
        if current_inference_process:
            logs, error = current_inference_process.get_logs()
            if error:
                raise HTTPException(status_code=500, detail=error)
            return {"logs": logs, "log_file": current_inference_process.get_log_file_path()}
        else:
            return {"logs": "No inference process active", "log_file": None}

@app.get("/inference_logs/recent")
async def get_recent_inference_logs(lines: int = Query(50, ge=1, le=1000)):
    """Get recent inference/vLLM server logs (last N lines)"""
    with status_lock:
        if current_inference_process:
            logs, error = current_inference_process.get_recent_logs(lines)
            if error:
                raise HTTPException(status_code=500, detail=error)
            return {"logs": logs, "lines": lines, "log_file": current_inference_process.get_log_file_path()}
        else:
            return {"logs": "No inference process active", "lines": 0, "log_file": None}

@app.post("/stop_inference")
async def stop_inference_server():
    """Force stop the current inference server"""
    global current_inference_process, model_status, status_detail
    
    with status_lock:
        if not current_inference_process:
            return {"message": "No inference process running", "status": "idle"}
        
        process_info = f"PID: {current_inference_process.process.pid if current_inference_process.process else 'unknown'}"
        
        try:
            print(f"Force stopping inference process ({process_info})")
            current_inference_process.stop()
            current_inference_process = None
            model_status = ModelStatus.idle
            status_detail = "Manually stopped"
            print("Inference process force stopped successfully")
            return {"message": f"Inference server stopped successfully ({process_info})", "status": "stopped"}
        except Exception as e:
            error_msg = f"Error stopping inference process: {e}"
            print(error_msg)
            status_detail = error_msg
            model_status = ModelStatus.error
            return {"message": error_msg, "status": "error", "error": str(e)}


# ========= Migrated Flask helpers → FastAPI =========
def extract_differences(option1: str, option2: str) -> str:
    """Extract the key differences between two HTML options (text & color)."""
    def extract_attributes(html_string: str):
        try:
            text_match = re.search(r'>([^<]+)</', html_string)
            text = text_match.group(1).strip() if text_match else ''

            # Extract backgroundColor from style={{ backgroundColor: 'blue' }}
            color_match = re.search(r"backgroundColor:\s*['\"](\w+)['\"]", html_string)
            color = color_match.group(1) if color_match else ''
            return {'text': text, 'color': color}
        except Exception:
            return {'text': '', 'color': ''}

    attrs1 = extract_attributes(option1 or "")
    attrs2 = extract_attributes(option2 or "")

    if attrs1['text'] != attrs2['text'] and attrs1['color'] != attrs2['color']:
        return f"{attrs1['color']} '{attrs1['text']}' vs {attrs2['color']} '{attrs2['text']}'"
    elif attrs1['text'] != attrs2['text']:
        return f"'{attrs1['text']}' vs '{attrs2['text']}'"
    elif attrs1['color'] != attrs2['color']:
        return f"{attrs1['color']} vs {attrs2['color']}"
    else:
        return f"{attrs1['text']} (identical)"

def transform_ab_test_data(raw_data_list: List[dict], dataset_paths: List[str]) -> List[dict]:
    """Transform raw A/B test data into frontend format."""
    
    # assert len(raw_data_list) == len(dataset_paths), "Length of raw data list and dataset paths must be the same"
    datasets = []
    for i in range(len(raw_data_list)):
        tests = []
        raw_data = raw_data_list[i]
        for idx, comparison in enumerate(raw_data):
            first_score = float(comparison.get('first_score', 0) or 0)
            second_score = float(comparison.get('second_score', 0) or 0)
            first_option = comparison.get('first_option', '') or ''
            second_option = comparison.get('second_option', '') or ''
            variant_text = extract_differences(first_option, second_option)

            if first_score > second_score:
                winner = 'A'
                improvement_val = (first_score - second_score) * 100
            elif second_score > first_score:
                winner = 'B'
                improvement_val = (second_score - first_score) * 100
            else:
                winner = 'Tie'
                improvement_val = 0.0

            improvement = f"+{improvement_val:.1f}%"
            tests.append({
                'id': 101 + idx,
                'name': f'Button Test {idx + 1}',
                'variant': variant_text,
                'winner': winner,
                'improvement': improvement
            })
        improvements = [float(t['improvement'].strip('+%')) for t in tests if t['improvement'] != '0%']
        avg_improvement = f"+{sum(improvements) / len(improvements):.1f}%" if improvements else '0%'
        
        name = dataset_paths[i].replace('_dataset.json', '').replace('_', ' ').title()
        datasets.append({
            'id': len(datasets) + 1,
            'name': f'Dataset {name}',
            'path': dataset_paths[i],
            'description': f'Dataset for optimizing the model for generating {name}',
            'totalTests': len(tests),
            'avgImprovement': avg_improvement,
            'tests': tests
        })

    return datasets

# ========= Migrated Flask endpoints (same paths) =========
EXTERNAL_DATASET_URL = "http://159.26.94.16:8080/dataset"  # your FastAPI dataset endpoint

@app.get("/api/abtests")
async def get_ab_tests():
    # Get all dataset files from the datasets directory
    datasets_dir = os.path.join('/home/user/projects/DubHacks2025/datasets')
    raw_data = []
    
    try:
        for filename in os.listdir(datasets_dir):
            if filename.endswith('_dataset.json'):
                with open(os.path.join(datasets_dir, filename)) as f:
                    dataset = json.load(f)
                    raw_data.append(dataset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset files: {str(e)}")
    
    # try:
    #     async with httpx.AsyncClient(timeout=5.0) as client:
    #         r = await client.get(EXTERNAL_DATASET_URL)
    #         r.raise_for_status()
    #         raw_data = r.json()
    # except httpx.HTTPError as e:
    #     raise HTTPException(status_code=500, detail=f"Error fetching from external API: {str(e)}")

    # multi_transformed = []
    # for data in raw_data:
    #     transformed = transform_ab_test_data(data)
    #     multi_transformed.append(transformed[0])
    # print("Length of raw data: ", len(raw_data))
    # print(raw_data)
    parsed_result = transform_ab_test_data(raw_data, os.listdir(datasets_dir))
    print(parsed_result)
    return parsed_result

@app.get("/api/basemodels")
async def get_base_models():
    base_models = [
        { 'id': 1, 'modelName': 'Qwen/Qwen3-Coder-30B-A3B-Instruct', 'timestamp': 'Foundation model'},
        { 'id': 2, 'modelName': 'Qwen/Qwen2.5-Coder-7B-Instruct', 'timestamp': 'Foundation model'},
        { 'id': 3, 'modelName': 'openai/gpt-oss-20b', 'timestamp': 'Foundation model'},
    ]
    return base_models

@app.get("/api/finetunes")
async def get_fine_tunes():
    output_dir = '/home/user/projects/DubHacks2025/outputs'
    checkpoint_folders: List[str] = []
    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            p = os.path.join(output_dir, item)
            if os.path.isdir(p):
                checkpoint_folders.append(item)
    
    def compare(item1, item2):
        return item2["timestamp"] - item1["timestamp"]

    fine_tunes = []
    for i, chk in enumerate(checkpoint_folders):
        p = os.path.join(output_dir, chk)
        try:
            ts = os.path.getmtime(p)
        except Exception:
            ts = 0.0
        
        chk

        fine_tunes.append({ 'id': i, 'modelName': chk, 'timestamp': ts })
    
    sorted(fine_tunes, key=lambda x: x['timestamp'])
    import datetime
    for idx, fine_tune in enumerate(fine_tunes):
        fine_tune['id'] = idx
        fine_tune['timestamp'] = datetime.datetime.fromtimestamp(fine_tune['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    return fine_tunes

# loss data identical to Flask
_LOSS_DATA = {
    'flywheel-v1.4': [
        {'epoch': 1, 'loss': 2.45}, {'epoch': 2, 'loss': 1.68},
        {'epoch': 3, 'loss': 1.42}, {'epoch': 4, 'loss': 1.28},
        {'epoch': 5, 'loss': 1.15}, {'epoch': 6, 'loss': 1.05},
        {'epoch': 7, 'loss': 0.98}, {'epoch': 8, 'loss': 0.92},
    ],
    'flywheel-v1.3': [
        {'epoch': 1, 'loss': 2.78}, {'epoch': 2, 'loss': 2.35},
        {'epoch': 3, 'loss': 1.89}, {'epoch': 4, 'loss': 1.71},
        {'epoch': 5, 'loss': 1.68}, {'epoch': 6, 'loss': 1.52},
        {'epoch': 7, 'loss': 1.35}, {'epoch': 8, 'loss': 1.24},
    ],
    'flywheel-v1.2': [
        {'epoch': 1, 'loss': 3.12}, {'epoch': 2, 'loss': 2.68},
        {'epoch': 3, 'loss': 2.41}, {'epoch': 4, 'loss': 2.28},
        {'epoch': 5, 'loss': 2.35}, {'epoch': 6, 'loss': 2.18},
        {'epoch': 7, 'loss': 1.89}, {'epoch': 8, 'loss': 1.67},
    ],
    'flywheel-v1.1': [
        {'epoch': 1, 'loss': 3.41}, {'epoch': 2, 'loss': 3.28},
        {'epoch': 3, 'loss': 3.05}, {'epoch': 4, 'loss': 2.92},
        {'epoch': 5, 'loss': 2.58}, {'epoch': 6, 'loss': 2.21},
        {'epoch': 7, 'loss': 1.95}, {'epoch': 8, 'loss': 1.79},
    ],
    'flywheel-v1.0': [
        {'epoch': 1, 'loss': 3.65}, {'epoch': 2, 'loss': 3.52},
        {'epoch': 3, 'loss': 3.38}, {'epoch': 4, 'loss': 3.21},
        {'epoch': 5, 'loss': 3.05}, {'epoch': 6, 'loss': 2.89},
        {'epoch': 7, 'loss': 2.74}, {'epoch': 8, 'loss': 2.58},
    ],
}

@app.get("/api/lossdata")
async def get_loss_data(model: str = Query("flywheel-v1.4")):
    return _LOSS_DATA.get(model, _LOSS_DATA['flywheel-v1.4'])

async def monitor_pull_results(process: subprocess.Popen, log_file_path: str):
    """Background task to monitor pull_results.py and notify clients when done"""
    global pull_data_status
    try:
        # Wait for the process to complete (this runs in background)
        loop = asyncio.get_event_loop()
        returncode = await loop.run_in_executor(None, process.wait)
        
        # Process completed
        with pull_data_lock:
            if returncode == 0:
                pull_data_status = "completed"
                await manager.broadcast({
                    "type": "pull_complete",
                    "status": "success",
                    "message": "Data pull completed successfully",
                    "log_file": log_file_path
                })
            else:
                pull_data_status = "failed"
                await manager.broadcast({
                    "type": "pull_complete",
                    "status": "error",
                    "message": f"Data pull failed with return code {returncode}",
                    "log_file": log_file_path
                })
    except Exception as e:
        with pull_data_lock:
            pull_data_status = "failed"
        await manager.broadcast({
            "type": "pull_complete",
            "status": "error",
            "message": f"Error monitoring pull_results: {str(e)}",
            "log_file": log_file_path
        })

@app.post("/api/pulldata")
async def pull_data():
    """Trigger pull_results.py script to fetch new data from Statsig"""
    global pull_data_status, pull_data_log_file
    
    # Create log file and start streaming
    log_file_path = create_log_file('pull_data')
    
    def is_pull_running():
        with pull_data_lock:
            return pull_data_status == "running"
    
    await stream_logs(log_file_path, is_pull_running)
    
    try:
        # Path to the pull_results.py script
        script_path = os.path.join('/home/user/projects/DubHacks2025/scripts', 'pull_results.py')
        
        # Check if script exists
        if not os.path.exists(script_path):
            raise HTTPException(status_code=500, detail=f"Script not found: {script_path}")
        
        # Open log file for writing
        log_file = open(log_file_path, 'w', buffering=1)  # Line buffered
        
        # Load environment variables from .env.local if it exists
        env_local_path = os.path.join('/home/user/projects/DubHacks2025', '.env.local')
        subprocess_env = dict(os.environ)
        subprocess_env['PYTHONUNBUFFERED'] = '1'
        
        if os.path.exists(env_local_path):
            # Read .env.local and add to environment
            with open(env_local_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        subprocess_env[key.strip()] = value.strip()
        
        # Spawn the process in the background without waiting
        # Redirect stdout and stderr to the log file
        # Use -u flag for unbuffered output to ensure real-time logging
        # Use conda environment 'datapipe2' which has all required dependencies
        conda_python = '/home/user/miniconda3/envs/datapipe2/bin/python'
        
        # Fall back to system python if conda environment not found
        python_executable = conda_python if os.path.exists(conda_python) else 'python'
        
        process = subprocess.Popen(
            [python_executable, '-u', script_path],
            stdout=log_file,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            cwd=os.path.dirname(script_path),
            start_new_session=True,  # Detach from parent process
            env=subprocess_env  # Pass environment with variables from .env.local
        )
        
        # Update status
        with pull_data_lock:
            pull_data_status = "running"
            pull_data_log_file = log_file_path
        
        # Start monitoring task in background (don't wait for it)
        asyncio.create_task(monitor_pull_results(process, log_file_path))
        
        # Notify clients that pull has started
        await manager.broadcast({
            "type": "pull_started",
            "status": "running",
            "message": "Data pull started",
            "log_file": log_file_path
        })
        
        return {
            "message": "Data pull started successfully",
            "process_id": process.pid,
            "status": "running",
            "log_file": log_file_path
        }
    except Exception as e:
        with pull_data_lock:
            pull_data_status = "failed"
        raise HTTPException(status_code=500, detail=f"Error starting pull_results.py: {str(e)}")

@app.get("/api/pulldata/status")
async def get_pull_data_status():
    """Get the current status of data pull operation"""
    with pull_data_lock:
        return {
            "status": pull_data_status,
            "log_file": pull_data_log_file
        }

@app.get("/api/pulldata/logs")
async def get_pull_data_logs():
    """Get full pull data logs"""
    with pull_data_lock:
        if pull_data_log_file and os.path.exists(pull_data_log_file):
            try:
                with open(pull_data_log_file, 'r') as f:
                    logs = f.read()
                return {"logs": logs, "log_file": pull_data_log_file}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")
        else:
            return {"logs": "No pull data operation active or log file not found", "log_file": None}

@app.get("/api/pulldata/logs/recent")
async def get_recent_pull_data_logs(lines: int = Query(50, ge=1, le=1000)):
    """Get recent pull data logs (last N lines)"""
    with pull_data_lock:
        if pull_data_log_file and os.path.exists(pull_data_log_file):
            try:
                with open(pull_data_log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    logs = ''.join(recent_lines)
                return {"logs": logs, "lines": len(recent_lines), "log_file": pull_data_log_file}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")
        else:
            return {"logs": "No pull data operation active or log file not found", "lines": 0, "log_file": None}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for client messages (if any)
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# ========= Shutdown cleanup (existing) =========
@app.on_event("shutdown")
async def shutdown_event():
    if current_inference_process is not None:
        try:
            current_inference_process.stop()
        except Exception:
            pass
    executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    # Run the unified app (same port you already expose for FastAPI)
    uvicorn.run(app, host="0.0.0.0", port=8080)
