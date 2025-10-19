import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

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


def get_pulse_results(experiment_id: str, control_group_id: str, test_group_id: str,
                     cuped: Optional[bool] = None, confidence: Optional[int] = None,
                     date: Optional[str] = None) -> Dict[str, Any]:
    api_key = os.getenv('STATSIG_CONSOLE_KEY')
    if not api_key:
        raise ValueError("no api key!")
    
    url = f"https://statsigapi.net/console/v1/experiments/{experiment_id}"
    
    headers = {
        "STATSIG-API-KEY": api_key
    }
    
    params = {
        "control": control_group_id,
        "test": test_group_id
    }
    
    if cuped is not None:
        params["cuped"] = str(cuped).lower()
    if confidence is not None:
        params["confidence"] = str(confidence)
    if date is not None:
        params["date"] = date
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 401:
        raise ValueError(f"Invalid API key: {response.json().get('message', 'Unauthorized')}")
    elif response.status_code == 404:
        raise ValueError(f"Pulse results not found for experiment: {experiment_id}")
    elif response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    result = response.json()
    return result.get('data', {})


if __name__ == "__main__":
    experiment_id = input("Enter experiment ID: ").strip()
    
    try:
        experiment = get_experiment(experiment_id)
        print(f"\n✓ Successfully retrieved experiment: {experiment.get('id')}")
        
        groups = experiment.get('groups', [])

        control_group = groups[0].get('id')
        test_group = groups[1].get('id')
        print(f"Control group: {control_group}")
        print(f"Test group: {test_group}")
        
        today = datetime.now().strftime('%Y-%m-%d')

    
        try:
            pulse_results = get_pulse_results(experiment_id, control_group, test_group, date=today)
            print(f"\n✓ Successfully retrieved pulse results")
            print(pulse_results)
        except ValueError as e:
            print(f"⚠ No pulse results available: {e}")
        except Exception as e:
            print(f"✗ Failed to fetch pulse results: {e}")
    
    except Exception as e:
        print(f"✗ Error: {e}")

