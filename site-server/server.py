from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://159.26.94.16:3000","http://localhost:3000"]}})

def extract_differences(option1, option2):
    """Extract the key differences between two HTML options."""
    import re
    
    def extract_attributes(html_string):
        """Extract text content and style attributes from HTML."""
        try:
            text_match = re.search(r'>([^<]+)</', html_string)
            text = text_match.group(1).strip() if text_match else ''
            
            # Extract backgroundColor from style attribute
            color_match = re.search(r"backgroundColor:\s*['\"](\w+)['\"]", html_string)
            color = color_match.group(1) if color_match else ''
            
            # Extract any other relevant attributes (could expand this)
            return {'text': text, 'color': color}
        except:
            return {'text': '', 'color': ''}
    
    attrs1 = extract_attributes(option1)
    attrs2 = extract_attributes(option2)
    
    # Build difference strings showing only what changed
    differences = []
    
    if attrs1['text'] != attrs2['text']:
        differences.append(f"text: '{attrs1['text']}' vs '{attrs2['text']}'")
    
    if attrs1['color'] != attrs2['color']:
        differences.append(f"color: {attrs1['color']} vs {attrs2['color']}")
    
    # If both text and color differ, create a compact representation
    if attrs1['text'] != attrs2['text'] and attrs1['color'] != attrs2['color']:
        return f"{attrs1['color']} '{attrs1['text']}' vs {attrs2['color']} '{attrs2['text']}'"
    elif attrs1['text'] != attrs2['text']:
        return f"'{attrs1['text']}' vs '{attrs2['text']}'"
    elif attrs1['color'] != attrs2['color']:
        return f"{attrs1['color']} vs {attrs2['color']}"
    else:
        return f"{attrs1['text']} (identical)"

def transform_ab_test_data(raw_data):
    """Transform raw A/B test data into frontend format."""
    tests = []
    
    for idx, comparison in enumerate(raw_data):
        first_score = comparison.get('first_score', 0)
        second_score = comparison.get('second_score', 0)
        
        # Extract differences between the two options
        first_option = comparison.get('first_option', '')
        second_option = comparison.get('second_option', '')
        variant_text = extract_differences(first_option, second_option)
        
        if first_score > second_score:
            winner = 'A'
            improvement_val = (first_score - second_score) * 100
        elif second_score > first_score:
            winner = 'B'
            improvement_val = (second_score - first_score) * 100
        else:
            winner = 'Tie'
            improvement_val = 0
        
        improvement = f"+{improvement_val:.1f}%"
        
        test = {
            'id': 101 + idx,
            'name': f'Button Test {idx + 1}',
            'variant': variant_text,
            'winner': winner,
            'improvement': improvement
        }
        tests.append(test)
    
    improvements = [float(t['improvement'].strip('+%')) for t in tests if t['improvement'] != '0%']
    avg_improvement = f"+{sum(improvements) / len(improvements):.1f}%" if improvements else '0%'
    
    test_groups = [
        {
            'id': 1,
            'name': 'E-Commerce Action Button Tests',
            'description': 'Button copy and color variations for e-commerce purchase',
            'totalTests': len(tests),
            'avgImprovement': avg_improvement,
            'tests': tests
        }
    ]
    
    return test_groups

@app.route('/api/abtests', methods=['GET'])
def get_ab_tests():
    try:
        response = requests.get('http://159.26.94.16:8001/dataset', timeout=5)
        response.raise_for_status()  
        
        raw_data = response.json()
        transformed_data = transform_ab_test_data(raw_data)
        return jsonify(transformed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from external API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/basemodels', methods=['GET'])
def get_base_models():
    base_models = [
        { 'id': 1, 'modelName': 'Qwen/Qwen3-Coder-30B-A3B-Instruct', 'timestamp': 'Foundation model'},
        { 'id': 2, 'modelName': 'Qwen/Qwen2.5-Coder-7B-Instruct', 'timestamp': 'Foundation model'},
        { 'id': 3, 'modelName': 'openai/gpt-oss-20b', 'timestamp': 'Foundation model'},
    ]
    return jsonify(base_models)

@app.route('/api/finetunes', methods=['GET'])
def get_fine_tunes():
    import os
    
    # Get list of checkpoint folders from outputs directory
    output_dir = '/home/user/projects/DubHacks2025/outputs'
    checkpoint_folders = []
    
    if os.path.exists(output_dir):
        # List all items in directory and filter for folders
        items = os.listdir(output_dir)
        checkpoint_folders = [
            item for item in items 
            if os.path.isdir(os.path.join(output_dir, item))
        ]
    fine_tunes = []
    for checkpoint in checkpoint_folders:
        checkpoint_name = os.path.basename(checkpoint)
        checkpoint_timestamp = os.path.getmtime(os.path.join(output_dir, checkpoint))
        fine_tunes.append({ 'id': len(fine_tunes), 'modelName': checkpoint_name, 'timestamp': checkpoint_timestamp })

    return jsonify(fine_tunes)

@app.route('/api/lossdata', methods=['GET'])
def get_loss_data():
    model_name = request.args.get('model', default='flywheel-v1.4', type=str)
    
    loss_data_by_model = {
        'flywheel-v1.4': [
            { 'epoch': 1, 'loss': 2.45 },
            { 'epoch': 2, 'loss': 1.68 },
            { 'epoch': 3, 'loss': 1.42 },
            { 'epoch': 4, 'loss': 1.28 },
            { 'epoch': 5, 'loss': 1.15 },
            { 'epoch': 6, 'loss': 1.05 },
            { 'epoch': 7, 'loss': 0.98 },
            { 'epoch': 8, 'loss': 0.92 },
        ],
        'flywheel-v1.3': [
            { 'epoch': 1, 'loss': 2.78 },
            { 'epoch': 2, 'loss': 2.35 },
            { 'epoch': 3, 'loss': 1.89 },
            { 'epoch': 4, 'loss': 1.71 },
            { 'epoch': 5, 'loss': 1.68 },
            { 'epoch': 6, 'loss': 1.52 },
            { 'epoch': 7, 'loss': 1.35 },
            { 'epoch': 8, 'loss': 1.24 },
        ],
        'flywheel-v1.2': [
            { 'epoch': 1, 'loss': 3.12 },
            { 'epoch': 2, 'loss': 2.68 },
            { 'epoch': 3, 'loss': 2.41 },
            { 'epoch': 4, 'loss': 2.28 },
            { 'epoch': 5, 'loss': 2.35 },
            { 'epoch': 6, 'loss': 2.18 },
            { 'epoch': 7, 'loss': 1.89 },
            { 'epoch': 8, 'loss': 1.67 },
        ],
        'flywheel-v1.1': [
            { 'epoch': 1, 'loss': 3.41 },
            { 'epoch': 2, 'loss': 3.28 },
            { 'epoch': 3, 'loss': 3.05 },
            { 'epoch': 4, 'loss': 2.92 },
            { 'epoch': 5, 'loss': 2.58 },
            { 'epoch': 6, 'loss': 2.21 },
            { 'epoch': 7, 'loss': 1.95 },
            { 'epoch': 8, 'loss': 1.79 },
        ],
        'flywheel-v1.0': [
            { 'epoch': 1, 'loss': 3.65 },
            { 'epoch': 2, 'loss': 3.52 },
            { 'epoch': 3, 'loss': 3.38 },
            { 'epoch': 4, 'loss': 3.21 },
            { 'epoch': 5, 'loss': 3.05 },
            { 'epoch': 6, 'loss': 2.89 },
            { 'epoch': 7, 'loss': 2.74 },
            { 'epoch': 8, 'loss': 2.58 },
        ],
    }
    
    return jsonify(loss_data_by_model.get(model_name, loss_data_by_model['flywheel-v1.4']))

if __name__ == '__main__':
    app.run(debug=True, port=8080)