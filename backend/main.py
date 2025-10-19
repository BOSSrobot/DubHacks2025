from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

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
        "message": "Button Dataset API", 
        "version": "1.0.0",
        "endpoints": {
            "/dataset": "GET - Returns the complete button dataset",
            "/dataset/random": "GET - Returns a random item from the dataset",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
