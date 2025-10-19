from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Button Dataset API", version="1.0.0")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ButtonDataItem(BaseModel):
    prompt: str
    first_option: str
    second_option: str
    first_score: float
    second_score: float

class ModelConfig(BaseModel):
    model_name: str
    model_path: str
    conda_env_name: str = "vllm"
    host: str = "0.0.0.0"
    port: int = 8001
    cuda_visible_devices: Optional[str] = None
    tensor_parallel_size: Optional[int] = 1
    gpu_memory_utilization: Optional[float] = 0.9

class ModelSelectionResponse(BaseModel):
    message: str
    selected_model: ModelConfig

# Global variable to store current model configuration
current_model_config: Optional[ModelConfig] = None

# Sample dataset matching the format you provided
sample_dataset = [
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
]



@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Button Dataset API with Model Management", 
        "version": "1.0.0",
        "endpoints": {
            "/dataset": "GET - Returns the complete button dataset",
            "/dataset/random": "GET - Returns a random item from the dataset",
            "/choose_model": "POST - Select a model for hosting (requires ModelConfig)",
            "/current_model": "GET - Returns currently selected model configuration",
            "/available_models": "GET - Lists available model paths in the project",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/dataset", response_model=List[ButtonDataItem])
async def get_dataset():
    """Returns the complete button dataset"""
    return sample_dataset

@app.get("/dataset/random", response_model=ButtonDataItem)
async def get_random_item():
    """Returns a random item from the dataset"""
    import random
    return random.choice(sample_dataset)

@app.get("/dataset/{index}", response_model=ButtonDataItem)
async def get_item_by_index(index: int):
    """Returns a specific item from the dataset by index"""
    if 0 <= index < len(sample_dataset):
        return sample_dataset[index]
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")
    
@app.post("/choose_model", response_model=ModelSelectionResponse)
async def choose_model(model_config: ModelConfig):
    """
    Select and configure a model for hosting.
    
    Args:
        model_config: Configuration for the model including name, path, and hosting settings
        
    Returns:
        Confirmation message with the selected model configuration
    """
    global current_model_config
    
    # Validate model path exists
    import os
    if not os.path.exists(model_config.model_path):
        raise HTTPException(
            status_code=400, 
            detail=f"Model path does not exist: {model_config.model_path}"
        )
    
    # Store the selected model configuration
    current_model_config = model_config
    
    return ModelSelectionResponse(
        message=f"Successfully selected model '{model_config.model_name}' at path '{model_config.model_path}'",
        selected_model=model_config
    )

@app.get("/current_model")
async def get_current_model():
    """
    Get the currently selected model configuration.
    
    Returns:
        Current model configuration or None if no model is selected
    """
    if current_model_config is None:
        return {"message": "No model currently selected", "selected_model": None}
    
    return {
        "message": "Current model configuration",
        "selected_model": current_model_config
    }

@app.get("/available_models")
async def list_available_models():
    """
    List available model paths by scanning common model directories.
    
    Returns:
        List of potential model paths found in the project
    """
    import os
    import glob
    
    # Common model directories to scan
    model_directories = [
        "./outputs/*/fused_model",
        "./trainer_output/checkpoint-*/",
        "./ab-test-rlhf/outputs/checkpoint-*/"
    ]
    
    available_models = []
    
    for pattern in model_directories:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                # Extract a reasonable model name from the path
                model_name = os.path.basename(os.path.dirname(path)) if "fused_model" in path else os.path.basename(path)
                available_models.append({
                    "suggested_name": model_name,
                    "path": os.path.abspath(path),
                    "type": "fused_model" if "fused_model" in path else "checkpoint"
                })
    
    return {
        "message": f"Found {len(available_models)} available model paths",
        "models": available_models
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
