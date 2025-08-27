from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import base64
from sudokuMain import solve_sudoku_from_image

app = Flask(__name__)
# Enable CORS for the development server and your deployed Lovable app
CORS(app, origins=["http://localhost:5173", "https://sudoku-vision-spark.lovable.app"])

@app.route('/solve_sudoku', methods=['POST'])
def solve():
    """
    API endpoint to solve a Sudoku from an uploaded image.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    temp_image_path = "temp_sudoku_image.png"

    try:
        file.save(temp_image_path)
        result = solve_sudoku_from_image(temp_image_path)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)