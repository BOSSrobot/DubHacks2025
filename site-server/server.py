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

@app.route('/api/finetunes', methods=['GET'])
def get_fine_tunes():
    fine_tunes = [
        { 'id': 0, 'modelName': 'flywheel-v1.4', 'timestamp': '2025-10-19 14:23:15', 'status': 'active' },
        { 'id': 1, 'modelName': 'flywheel-v1.3', 'timestamp': '2025-10-19 14:23:15', 'status': 'archived' },
        { 'id': 2, 'modelName': 'flywheel-v1.2', 'timestamp': '2025-10-19 14:23:15', 'status': 'archived' },
        { 'id': 3, 'modelName': 'flywheel-v1.1', 'timestamp': '2025-10-18 09:42:33', 'status': 'archived' },
        { 'id': 4, 'modelName': 'flywheel-v1.0', 'timestamp': '2025-10-18 8:15:08', 'status': 'archived' },
    ]
    return jsonify(fine_tunes)

@app.route('/api/lossdata', methods=['GET'])
def get_loss_data():
    loss_data = [
        { 'epoch': 1, 'loss': 2.22 },
        { 'epoch': 2, 'loss': 2.12 },
        { 'epoch': 3, 'loss': 1.89 },
        { 'epoch': 4, 'loss': 1.75 },
        { 'epoch': 5, 'loss': 1.58 },
        { 'epoch': 6, 'loss': 1.42 },
        { 'epoch': 7, 'loss': 1.31 },
        { 'epoch': 8, 'loss': 1.18 },
    ]
    return jsonify(loss_data)

if __name__ == '__main__':
    app.run(debug=True, port=8080)