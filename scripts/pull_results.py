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

def get_all_events(iterate_pages: bool = False):
    api_key = os.getenv('STATSIG_CONSOLE_KEY')
    if not api_key:
        raise ValueError("no api key!")
    
    url = f"https://statsigapi.net/console/v1/events"
    
    headers = {
        "STATSIG-API-KEY": api_key
    }

    all_events = []

    page = 1
    if iterate_pages:
        while True:
            querystring = {"page": str(page)}
            print("Fetching page ", page)
            response = requests.get(url, headers=headers, params=querystring)
            json = response.json()
            events = json.get('data', [])
            print(f"Page {page} has {len(events)} events")

            if len(events) == 0 or page >= 3:
                break

            all_events.extend(events)

            page += 1
    else:
        response = requests.get(url, headers=headers)
        json = response.json()
        events = json.get('data', [])
        all_events.extend(events)

    return all_events

def get_experiment_pairs(experiment_name: str, params_to_absolute_count, experiment_to_params):
    api_key = os.getenv('STATSIG_CONSOLE_KEY')

    url = f"https://statsigapi.net/console/v1/experiments/{experiment_name}"
    
    headers = {
        "STATSIG-API-KEY": api_key
    }

    description_to_params = {}

    for k, v in experiment_to_params.items():
        print(k, ": ", v)

    response = requests.get(url, headers=headers)
    json = response.json()
    experiment = json
    experiment_name = experiment.get('data', {}).get('id', '')
    if experiment_name not in experiment_to_params.keys():
        return []
    
    options = []
    if experiment.get('data', {}) and experiment.get('data', {}).get('groups', []):
        groups = experiment.get('data', {}).get('groups', [])
        for group in groups:
            # print(f"Group: {group}")
            if group.get('description', "") != "":
                description = group.get('description')
                params = tuple(sorted(group.get('parameterValues', {}).items()))
                # print("PRINTING MY EXPERIMENT TO PARAMS")
                for i in range(len(experiment_to_params[experiment_name])):
                    param = experiment_to_params[experiment_name][i]
                    # print(param)
                    contained_in_experiment_params = True
                    for tup in param:
                        # print(tup)
                        if tup not in params:
                            contained_in_experiment_params = False
                            break
                    if contained_in_experiment_params:
                        params = param
                        # print(f"Params: {params}")
                        break
                    # for k, v in param:
                    #     if k not in params or v != params[k]:
                    #         contained_in_experiment_params = False
                    #         break
                    # if contained_in_experiment_params:
                    #     params = param
                    #     break
                # return []
                if params not in params_to_absolute_count:
                    params_to_absolute_count[params] = 0
                    # continue
                # print(f"Description: {description}")
                options.append(description)
                # print(f"Parameters: {params}")
                # print(f"Params to absolute count: {params_to_absolute_count[params]}")
                description_to_params[description] = params
                # print(f"Description: {description} - Parameters: {content_to_params[description]}")
    
    # print("\n\n -------------------------- \n\n")
    # return

    final_pairs = []
    if len(options) < 2:
        return final_pairs
    elif len(options) > 2:
        for i in range(len(options)):
            for j in range(i+1, len(options)):
                final_pairs.append((options[i], options[j]))
    else:
        final_pairs.append((options[0], options[1]))

    print(f"Final pairs: {final_pairs}")
    
    dataset_pairs = []
    for pair in final_pairs:
        first_option = pair[0]
        second_option = pair[1]
        print(f"First option: {first_option} - Second option: {second_option}")
        first_params = description_to_params[first_option]
        second_params = description_to_params[second_option]
        # print(f"First params: {tuple(sorted(first_params.items()))} - Second params: {tuple(sorted(second_params.items()))}")
        # print(f"Params to absolute count: {params_to_absolute_count}")
        first_score = params_to_absolute_count.get(first_params, 0)
        second_score = params_to_absolute_count.get(second_params, 0)
        total = first_score + second_score
        if total == 0:
            print(f"Total is 0 for {first_option} and {second_option}")
            continue
        dataset_pairs.append({
            "first_option": first_option,
            "second_option": second_option,
            "first_score": first_score / total,
            "second_score": second_score / total,
        })
    return dataset_pairs

whitelist_experiments = [
    "experiment_-90156b26-0064-47b1-90aa-1705ee162d32"
]

# should aggregate all the events into categories with a name and pairwise 
def aggregate_into_categories(event_list):
    # save_directory = "pairs_datasets"
    # save_path = f"{experiment_category}_pairs_dataset.json"
    category_to_experiments = {}
    experiment_to_pairs = {}
    experiment_to_prompt = {}
    params_to_absolute_count = {}
    experiment_to_params = {}
    
    for event in event_list:
        experiment_name = event.get('value', '')
        if experiment_name == '' or experiment_name not in whitelist_experiments:
            continue


        metadata = event.get('metadata', {})
        if not metadata:
            continue

        experiment_category = experiment_name.split('-')[0]
        if experiment_category not in category_to_experiments:
            # print(f"Adding experiment category: {experiment_category}")
            category_to_experiments[experiment_category] = [experiment_name]
        else:
            if experiment_name not in category_to_experiments[experiment_category]:
                # print(f"Adding experiment {experiment_name} to category: {experiment_category}")
                category_to_experiments[experiment_category].append(experiment_name)
        
        params = tuple(sorted(metadata.items()))
        if experiment_name not in experiment_to_params:
            experiment_to_params[experiment_name] = [params]
        elif params not in experiment_to_params[experiment_name]:
            experiment_to_params[experiment_name].append(params)
        params_to_absolute_count[params] = params_to_absolute_count.get(params, 0) + 1

    for params, count in params_to_absolute_count.items():
        print(f"Params: {params} - Count: {count}")
    
    print("\n\n -------------------------- \n\n")
    
    pairs_dataset = []
    for category, experiment_name in category_to_experiments.items():
        for experiment in experiment_name:
            if experiment in whitelist_experiments:
                print(f"Getting pairs for experiment: {experiment}")
                pairs_dataset.extend(get_experiment_pairs(experiment, params_to_absolute_count, experiment_to_params))

    return pairs_dataset

if __name__ == "__main__":
    use_event_list = True
    # experiment_id = input("Enter experiment ID: ").strip()
    
    # try:
        # experiment = get_experiment(experiment_id)
        # print(f"\n✓ Successfully retrieved experiment: {experiment.get('id')}")
        
        # groups = experiment.get('groups', [])

        # control_group = groups[0].get('id')
        # test_group = groups[1].get('id')
        # print(f"Control group: {control_group}")
        # print(f"Test group: {test_group}")
        
    today = datetime.now().strftime('%Y-%m-%d')

    if use_event_list:
        # try: 
        event_list = get_all_events(True)
        # print(f"\n✓ Successfully retrieved event list")
        # print(f"Number of events: {len(event_list)}")

        pairs_dataset = aggregate_into_categories(event_list)
        print(f"Number of pairs dataset: {len(pairs_dataset)}")
        for pair in pairs_dataset:
            print(pair)
            
        # except ValueError as e:
        #     print(f"⚠ No event list available: {e}")
        # except Exception as e:
        #     print(f"✗ Failed to fetch event list: {e}")
    else:
        try:
            pulse_results = get_pulse_results(experiment_id, control_group, test_group, date=today)
            print(f"\n✓ Successfully retrieved pulse results")
            print(pulse_results)
        except ValueError as e:
            print(f"⚠ No pulse results available: {e}")
        except Exception as e:
            print(f"✗ Failed to fetch pulse results: {e}")
    
    # except Exception as e:
    #     print(f"✗ Error: {e}")

