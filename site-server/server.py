from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

@app.route('/api/double', methods=['GET'])
def double_number():
    number_str = request.args.get('number', default='0', type=str)

    number = int(number_str)
    doubled_number = number * 2

    return jsonify({'result': doubled_number})

@app.route('/api/abtests', methods=['GET'])
def get_ab_tests():
    ab_tests = [
        { 'id': 1, 'name': 'Hero CTA Button', 'variant': 'A vs B', 'winner': 'B', 'improvement': '+12.3%', 'conversions': 287, 'visitors': 2431 },
        { 'id': 2, 'name': 'Navigation Layout', 'variant': 'A vs B', 'winner': 'A', 'improvement': '+8.7%', 'conversions': 412, 'visitors': 4102 },
        { 'id': 3, 'name': 'Color Scheme', 'variant': 'A vs B', 'winner': 'B', 'improvement': '+15.2%', 'conversions': 198, 'visitors': 1823 },
        { 'id': 4, 'name': 'Pricing Display', 'variant': 'A vs B', 'winner': 'B', 'improvement': '+9.4%', 'conversions': 121, 'visitors': 1089 },
    ]
    return jsonify(ab_tests)

@app.route('/api/basemodels', methods=['GET'])
def get_base_models():
    base_models = [
        { 'id': 1, 'modelName': 'Qwen Coder 3', 'timestamp': 'Foundation model', 'status': 'active' },
        { 'id': 2, 'modelName': 'Qwen 0.6B', 'timestamp': 'Foundation model', 'status': '' },
        { 'id': 3, 'modelName': 'GPT OSS 20B', 'timestamp': 'Foundation model', 'status': '' },
    ]
    return jsonify(base_models)

@app.route('/api/finetunes', methods=['GET'])
def get_fine_tunes():
    fine_tunes = [
        { 'id': 0, 'modelName': 'flywheel-v1.4', 'timestamp': '2025-10-19 14:23:15', 'status': 'active'},
        { 'id': 1, 'modelName': 'flywheel-v1.3', 'timestamp': '2025-10-19 14:23:15', 'status': ''},
        { 'id': 2, 'modelName': 'flywheel-v1.2', 'timestamp': '2025-10-19 14:23:15', 'status': ''},
        { 'id': 3, 'modelName': 'flywheel-v1.1', 'timestamp': '2025-10-18 09:42:33', 'status': ''},
        { 'id': 4, 'modelName': 'flywheel-v1.0', 'timestamp': '2025-10-18 8:15:08', 'status': ''},
    ]
    return jsonify(fine_tunes)

@app.route('/api/lossdata', methods=['GET'])
def get_loss_data():
    model_name = request.args.get('model', default='flywheel-v1.4', type=str)
    
    # Different loss curves for each tuned model - each with unique training patterns
    loss_data_by_model = {
        'flywheel-v1.4': [
            # Steep initial drop, then gradual improvement
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
            # More consistent decline with a small plateau
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
            # Gradual decline with slight bump in middle
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
            # Slow initial drop, then steeper improvement
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
            # Very gradual, steady decline - slower convergence
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
    
    # Return the loss data for the requested model, or the default if not found
    return jsonify(loss_data_by_model.get(model_name, loss_data_by_model['flywheel-v1.4']))

if __name__ == '__main__':
    app.run(debug=True, port=8080)