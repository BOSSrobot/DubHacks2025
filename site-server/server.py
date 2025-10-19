from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

def extract_button_text(html_string):
    """Extract text content from button HTML string."""
    try:
        start = html_string.find('>') + 1
        end = html_string.find('</button>')
        if start > 0 and end > 0:
            return html_string[start:end].strip()
        return 'Button'
    except:
        return 'Button'

def transform_ab_test_data(raw_data):
    """Transform raw A/B test data into frontend format."""
    tests = []
    
    for idx, comparison in enumerate(raw_data):
        first_score = comparison.get('first_score', 0)
        second_score = comparison.get('second_score', 0)
        
        first_text = extract_button_text(comparison.get('first_option', ''))
        second_text = extract_button_text(comparison.get('second_option', ''))
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
            'variant': f'{first_text[:30]}... vs {second_text[:30]}...',
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
'''
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
'''
@app.route('/api/abtests', methods=['GET'])
def get_ab_tests():
    return jsonify([
        {
            'id': 1,
            'name': 'E-Commerce Action Button Tests',
            'description': 'Button copy and color variations for e-commerce purchase',
            'totalTests': 10,
            'avgImprovement': '+10.0%',
            'tests': [
                {
                    'id': 1,
                    'name': 'Button Test 1',
                    'variant': 'Button A',
                    'winner': 'A',
                    'improvement': '+10.0%'
                },
                {
                    'id': 2,
                    'name': 'Button Test 2',
                    'variant': 'Button B',
                    'winner': 'B',
                    'improvement': '+10.0%'
                },
                {
                    'id': 3,
                    'name': 'Button Test 3',
                    'variant': 'Button C',
                    'winner': 'Tie',
                    'improvement': '0%'
                }
            ]
        },
        {
            'id': 2,
            'name': 'E-Commerce Action Button Tests 2',
            'description': 'Button copy and color variations for e-commerce purchase',
            'totalTests': 10,
            'avgImprovement': '+10.0%',
            'tests': [
                {
                    'id': 1,
                    'name': 'Button Test 1',
                    'variant': 'Button A',
                    'winner': 'A',
                    'improvement': '+10.0%'
                },
                {
                    'id': 2,
                    'name': 'Button Test 2',
                    'variant': 'Button B',
                    'winner': 'B',
                    'improvement': '+10.0%'
                },
                {
                    'id': 3,
                    'name': 'Button Test 3',
                    'variant': 'Button C',
                    'winner': 'Tie',
                    'improvement': '0%'
                }
            ]
        }
    ])

@app.route('/api/basemodels', methods=['GET'])
def get_base_models():
    base_models = [
        { 'id': 1, 'modelName': 'Qwen Coder 3', 'timestamp': 'Foundation model'},
        { 'id': 2, 'modelName': 'Qwen 0.6B', 'timestamp': 'Foundation model'},
        { 'id': 3, 'modelName': 'GPT OSS 20B', 'timestamp': 'Foundation model'},
    ]
    return jsonify(base_models)

@app.route('/api/finetunes', methods=['GET'])
def get_fine_tunes():
    fine_tunes = [
        { 'id': 0, 'modelName': 'flywheel-v1.4', 'timestamp': '2025-10-19 14:23:15'},
        { 'id': 1, 'modelName': 'flywheel-v1.3', 'timestamp': '2025-10-19 14:23:15'},
        { 'id': 2, 'modelName': 'flywheel-v1.2', 'timestamp': '2025-10-19 14:23:15'},
        { 'id': 3, 'modelName': 'flywheel-v1.1', 'timestamp': '2025-10-18 09:42:33'},
        { 'id': 4, 'modelName': 'flywheel-v1.0', 'timestamp': '2025-10-18 8:15:08'},
    ]
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