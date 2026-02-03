#!/usr/bin/env python3
"""
Quick Sort API Server
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

def quick_sort(arr):
    """Quick sort algorithm"""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

@app.route('/api/quick_sort', methods=['POST'])
def sort_numbers():
    """Sort a list of numbers"""
    data = request.get_json()
    
    if not data or 'numbers' not in data:
        return jsonify({'error': 'Please provide "numbers" field'}), 400
    
    numbers = data['numbers']
    
    if not isinstance(numbers, list):
        return jsonify({'error': '"numbers" must be a list'}), 400
    
    try:
        sorted_numbers = quick_sort(numbers)
        return jsonify({
            'input': numbers,
            'output': sorted_numbers,
            'count': len(sorted_numbers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("🚀 Quick Sort API Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
