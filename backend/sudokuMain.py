print('Setting up')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from utlis import *
import sudokuSolver
import numpy as np
import cv2
import base64

heightImg = 450
widthImg = 450
model = intializePredictionModel()

def solve_sudoku_from_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Could not load image: {image_path}")

    img = cv2.resize(img, (widthImg, heightImg))
    imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8)
    imgThreshold = preProcess(img)

    contours, _ = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    biggest, maxArea = biggestContour(contours)
    if biggest.size == 0:
        raise Exception("No Sudoku puzzle found in the image.")

    biggest = reorder(biggest)
    pts1 = np.float32(biggest)
    pts2 = np.float32([[0,0],[widthImg,0],[0,heightImg],[widthImg,heightImg]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgWrapColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))
    imgDetectedDigits = imgBlank.copy()
    imgWrapGray = cv2.cvtColor(imgWrapColored, cv2.COLOR_BGR2GRAY)

    boxes = splitBoxes(imgWrapGray)
    numbers = getPrediction(boxes, model)
    numbers = np.asarray(numbers)
    posArray = np.where(numbers > 0, 0, 1)

    board = np.array_split(numbers, 9)
    if not sudokuSolver.solve(board):
        raise Exception("Solver could not find a solution.")

    flatList = []
    for sublist in board:
        for item in sublist:
            flatList.append(int(item))

    solvedNumbers = np.array(flatList) * posArray
    imgSolvedDigits = displayNumbers(imgBlank.copy(), solvedNumbers, color=(0, 255, 255))

    # inverse warp back to original image shape
    matrix_inv = cv2.getPerspectiveTransform(pts2, pts1)
    imgInvWarpColored = cv2.warpPerspective(imgSolvedDigits, matrix_inv, (widthImg, heightImg))
    overlay = cv2.addWeighted(imgInvWarpColored, 1, img, 0.5, 1)

    # encode original and overlay to base64 PNG
    _, orig_png = cv2.imencode('.png', img)
    _, overlay_png = cv2.imencode('.png', overlay)
    orig_b64 = base64.b64encode(orig_png.tobytes()).decode('utf-8')
    overlay_b64 = base64.b64encode(overlay_png.tobytes()).decode('utf-8')

    solved_board = [list(map(int, row)) for row in board]

    # NEW: Split the original numbers back into a board format
    original_board = [list(map(int, row)) for row in np.array_split(numbers, 9)]

    return {
        "solved_board": solved_board,
        "original_board": original_board,  # Added this to send original numbers to the frontend
        "original_image": orig_b64,
        "overlay_image": overlay_b64
    }


# If you run this file standalone, it will process the configured pathImage
if __name__ == "__main__":
    pathImage = "Resources/6.png"
    try:
        res = solve_sudoku_from_image(pathImage)
        print("Solved board:")
        for r in res["solved_board"]:
            print(r)
    except Exception as e:
        print("Failed to solve Sudoku:", e)
