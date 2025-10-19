import requests
import uuid
import re

def start_experiment(api_key: str, experiment_id: str):
    """Start a Statsig experiment using the correct PUT endpoint."""
    headers = {
        "STATSIG-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    
    # Use the correct PUT endpoint for starting experiments
    url = f"https://statsigapi.net/console/v1/experiments/{experiment_id}/start"
    response = requests.put(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def create_experiment(api_key: str, name: str, description: str, groups: list):
    """Create and automatically start a Statsig experiment."""
    
    # Name is now required, no fallback needed
    if not name:
        raise ValueError("Experiment name is required")
    
    # Convert name to kebab case and add UUID for uniqueness
    def to_kebab_case(text):
        # Replace spaces and underscores with hyphens, remove special characters, convert to lowercase
        kebab = re.sub(r'[^\w\s-]', '', text)  # Remove special chars except word chars, spaces, hyphens
        kebab = re.sub(r'[-_\s]+', '-', kebab)  # Replace spaces, underscores, multiple hyphens with single hyphen
        return kebab.lower().strip('-')  # Convert to lowercase and remove leading/trailing hyphens
    
    # Generate kebab case name with UUID suffix
    kebab_name = to_kebab_case(name)
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for brevity
    experiment_name = f"{kebab_name}-{unique_id}"

    # Automatically calculate group sizes evenly
    num_groups = len(groups)
    if num_groups == 0:
        raise ValueError("At least one group is required")
    
    base_size = 100 // num_groups
    remainder = 100 % num_groups
    
    # Assign sizes to groups
    for i, group in enumerate(groups):
        if i == 0:
            # Give any remainder to the first group
            group["size"] = base_size + remainder
        else:
            group["size"] = base_size

    payload = {
        "name": experiment_name,
        "stratifiedSampling": None,
        "description": description,
        "idType": "userID",
        "groups": groups,
        "allocation": 100,
    }

    headers = {
        "STATSIG-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    # Step 1: Create the experiment
    url = "https://statsigapi.net/console/v1/experiments"
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        experiment_data = response.json()
        # Extract the experiment ID from the nested data structure
        experiment_id = None
        if "data" in experiment_data and "id" in experiment_data["data"]:
            experiment_id = experiment_data["data"]["id"]
        
        if not experiment_id:
            # If no ID is returned, return the creation response
            return {
                "status": "created_but_not_started",
                "message": "Experiment created successfully but could not retrieve ID for starting",
                "experiment_data": experiment_data
            }
        
        try:
            # Step 2: Start the experiment
            start_response = start_experiment(api_key, experiment_id)
            
            return {
                "status": "created_and_started",
                "message": "Experiment created and started successfully",
                "experiment_data": experiment_data,
                "start_response": start_response
            }
            
        except Exception as start_error:
            # If starting fails, return the created experiment data with error info
            return {
                "status": "created_but_start_failed",
                "message": f"Experiment created successfully but failed to start: {str(start_error)}",
                "experiment_data": experiment_data,
                "start_error": str(start_error)
            }
    else:
        response.raise_for_status()


command_prompt = """
Creates and automatically starts a new Statsig experiment. The experiment will be created and then immediately started so it can run in your webapp. 
For the name, use either the component you are modifying (e.g., 'button') or the general idea behind the test (e.g., 'selling') in kebab-case format. 
CRITICAL: Change ONLY ONE parameter across all groups (e.g., ONLY color OR ONLY text, never multiple parameters).
Group sizes are automatically calculated and distributed evenly (e.g., 2 groups = 50%/50%, 3 groups = 33%/33%/34%).
Description should describe what the experiment is testing for. 
groups should be a list of dictionaries corresponding to each group. Each dictionary should contain: 
name - A string describing what the group is
description - MUST BE ACTUAL CODE/HTML - NOT text description. Provide the exact code snippet that would render when this group's parameters are applied
parameterValues -  A dictionary containing all the parameters and their corresponding values
"""

tools = [
    {
        "name": "create_experiment",
        "description": command_prompt,
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the experiment in kebab-case. Use either the component you are modifying (e.g., 'button') or the general idea behind the test (e.g., 'selling'). A UUID will be automatically appended to ensure uniqueness."
                },
                "description": {
                    "type": "string",
                    "description": "Describes what the experiment is testing for."
                },
                "groups": {
                    "type": "array",
                    "description": "List of groups (variants) in the experiment. Each group defines its share of users and parameter values.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The group name (e.g., 'Control', 'Treatment')."
                            },
                            "description": {
                                "type": "string",
                                "description": "MUST BE ACTUAL CODE/HTML - NOT text description. Provide the exact code snippet that would render when this group's parameters are applied (e.g., '<button style=\"color: blue\">Click me</button>')."
                            },
                            "parameterValues": {
                                "type": "object",
                                "description": "A dictionary of parameter names and their values for this group.",
                                "additionalProperties": True
                            }
                        },
                        "required": ["name", "parameterValues"]
                    }
                }
            },
            "required": ["name", "description", "groups"]
        }
    }
]


if __name__ == "__main__":

    g = [
        {
            "name": "Control",
            "parameterValues": {"color": "blue"},
            "description": "Existing blue UI"
        },
        {
            "name": "Treatment A",
            "parameterValues": {"color": "red"},
            "description": "Testing red button"
        },
        {
            "name": "Treatment B",
            "parameterValues": {"color": "green"},
            "description": "Testing green button"
        }
    ]


    result = create_experiment(
        api_key="console-OAyMznaZmKNxeHOARQiTnbfPjcxbaPpCC0ftafnZ9wU",
        name="Button Color Test Experiment",
        description="testing api",
        groups=g,
    )

    print(result)
