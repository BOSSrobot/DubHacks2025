import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv('.env.local')


def get_experiment(experiment_id: str) -> Dict[str, Any]:

    api_key = os.getenv('STATSIG_CONSOLE_KEY')
    if not api_key:
        raise ValueError("no api key!")
    
    url = f"https://statsigapi.net/console/v1/experiments/{experiment_id}"
    
    headers = {
        "STATSIG-API-KEY": api_key
    }
  
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        raise ValueError(f"Invalid API key: {response.json().get('message', 'Unauthorized')}")
    elif response.status_code == 404:
        raise ValueError(f"Experiment not found: {experiment_id}")
    elif response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    result = response.json()
    return result.get('data', {})


if __name__ == "__main__":
    experiment_id = input("Enter experiment ID: ").strip()
    
    try:
        experiment = get_experiment(experiment_id)
        print(f"\n✓ Successfully retrieved experiment: {experiment.get('id')}")
    except Exception as e:
        print(f"✗ Error: {e}")

