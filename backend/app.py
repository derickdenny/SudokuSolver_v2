# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS # Used to allow requests from your React frontend
import numpy as np
import cv2
import io
import base64
import os

# Import your Sudoku solving logic modules
# Ensure these files (sudokuMain.py, sudokuSolver.py, utlis.py) are in the same directory as app.py
import sudokuMain # The original sudokuMain.py will be treated as a module here
import sudokuSolver
import utlis

app = Flask(__name__)
# Enable CORS for all routes. This is crucial for local development where
# your React app (e.g., localhost:5173) needs to talk to your Flask app (e.g., localhost:5000).
CORS(app)

# --- TensorFlow Model Loading ---
# This part is critical. We load the model once when the Flask app starts.
# This avoids reloading the model for every single request, which would be very slow.
sudoku_model = None
try:
    # Ensure the path to the model is correct relative to app.py
    # os.path.join handles path separators correctly across OS
    model_path = os.path.join(os.path.dirname(__file__), "Resources", "model_trained_8.keras")
    sudoku_model = utlis.intializePredictionModel(model_path=model_path) # Pass the model path
    print(f"TensorFlow model loaded successfully from {model_path}.")
except Exception as e:
    print(f"Error loading TensorFlow model: {e}")
    # If the model fails to load, the server will still run, but API calls will return an error.

@app.route('/')
def index():
    """Simple route to check if the Flask API is running."""
    return "Sudoku Solver API is running! Send POST request to /solve_sudoku with an image file."

@app.route('/solve_sudoku', methods=['POST'])
def solve_sudoku_api():
    """
    API endpoint to receive a Sudoku image, process it, solve the puzzle,
    and return the solved board and an image with the solution overlaid.
    """
    # Check if the TensorFlow model was loaded successfully
    if sudoku_model is None:
        return jsonify({"error": "TensorFlow model not loaded. Please check server logs for model path issues."}), 500

    # Ensure an image file was sent in the request
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided in the 'image' field."}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected image file."}), 400

    try:
        # Read the image file content as bytes
        image_bytes = file.read()
        # Decode the image bytes into an OpenCV (numpy) image array
        np_img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Could not decode image. Please ensure it's a valid image format (e.g., PNG, JPG)."}), 400

        # --- Image Processing and Digit Recognition (using your existing utlis.py and sudokuMain.py logic) ---
        # Define fixed dimensions for consistent processing
        heightImg = 450
        widthImg = 450
        img = cv2.resize(img, (widthImg, heightImg)) # Resize the input image

        # Preprocess the image (grayscale, blur, threshold)
        imgThreshold = utlis.preProcess(img)

        # Find the biggest contour, assumed to be the Sudoku grid
        contours, _ = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        biggest, maxArea = utlis.biggestContour(contours)

        if biggest.size != 0 and maxArea > 1000: # Add a minimum area check for robustness
            # Reorder points for perspective transform
            biggest = utlis.reorder(biggest)
            pts1 = np.float32(biggest) # Points from the detected contour
            pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]]) # Target points for flat view
            matrix = cv2.getPerspectiveTransform(pts1, pts2) # Get the transformation matrix
            imgWrapColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg)) # Apply perspective transform
            imgWrapColored = cv2.cvtColor(imgWrapColored, cv2.COLOR_BGR2GRAY) # Convert to grayscale

            # Split the warped image into 81 cells and get predictions for digits
            boxes = utlis.splitBoxes(imgWrapColored)
            # Pass the pre-loaded model to getPrediction
            numbers = utlis.getPrediction(boxes, sudoku_model) # Use the loaded model
            numbers_np = np.asarray(numbers)

            # Create a positional array to know which cells were originally filled (non-zero)
            # This is crucial to only overlay the *solved* numbers into the empty cells.
            original_puzzle_numbers_mask = np.where(numbers_np > 0, 0, 1)

            # --- Sudoku Solving ---
            # Convert the 1D list of numbers to a 9x9 board format for the solver
            board_to_solve = np.array_split(numbers_np, 9)
            # Ensure numbers are integers for the solver (0 for empty cells)
            board_for_solver = [[int(x) for x in row] for row in board_to_solve]

            # Call the Sudoku solver. It modifies 'board_for_solver' in-place.
            if sudokuSolver.solve(board_for_solver):
                # Flatten the solved board back to a 1D list for displayNumbers
                flatList_solved = [item for sublist in board_for_solver for item in sublist]
                solvedNumbers = np.array(flatList_solved)

                # --- Overlay Solution on Image ---
                # Create a blank image to draw the solved digits on
                imgSolvedDigits = np.zeros((heightImg, widthImg, 3), np.uint8)
                # Only display numbers in cells that were *originally empty* (where mask is 1)
                imgSolvedDigits = utlis.displayNumbers(imgSolvedDigits, solvedNumbers * original_puzzle_numbers_mask, color=(0,255,255))

                # Inverse perspective transform to place the solved digits back onto the original image perspective
                matrix_inv = cv2.getPerspectiveTransform(pts2, pts1) # Invert the matrix
                imgInvWarpColored = cv2.warpPerspective(imgSolvedDigits, matrix_inv, (widthImg, heightImg))
                # Add the solved digits overlay to the original input image
                final_output_image = cv2.addWeighted(imgInvWarpColored, 1, img, 0.5, 1)

                # Encode the final image (with solution overlaid) to base64 for sending to frontend
                _, buffer = cv2.imencode('.png', final_output_image)
                encoded_image = base64.b64encode(buffer).decode('utf-8')

                # Return the solved board as a list of lists of integers, and the encoded image
                return jsonify({
                    "solved_board": [[int(num) for num in row] for row in board_for_solver],
                    "solved_image": encoded_image
                })
            else:
                return jsonify({"error": "Sudoku puzzle detected but could not be solved by the algorithm. It might be invalid or too complex."}), 400
        else:
            return jsonify({"error": "No clear Sudoku puzzle detected in the image. Please ensure the grid is visible."}), 400

    except Exception as e:
        import traceback
        traceback.print_exc() # Print full traceback to console for debugging
        return jsonify({"error": f"An unexpected error occurred during processing: {str(e)} Please check the image or server logs."}), 500

if __name__ == '__main__':
    # When running locally, ensure the Flask app is accessible by the frontend
    # host='0.0.0.0' makes it accessible from your local network (if needed)
    # debug=True provides helpful error messages during development
    app.run(debug=True, host='0.0.0.0', port=5000)

