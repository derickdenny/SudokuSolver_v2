print('Setting up')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from utlis import *

import sudokuSolver
import numpy as np
import cv2

###########################################
pathImage = "Resources/1.png"
heightImg = 450
widthImg = 450
model = intializePredictionModel()
###########################################

# 1. Prepare the image
img = cv2.imread(pathImage)
if img is None:  # Check if image loaded successfully
    print(f"Error: Could not load image from '{pathImage}'. Check if it's a valid image file.")
    exit()

img = cv2.resize(img, (widthImg, heightImg))
imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8)  # A blank BGR image
imgThreshold = preProcess(img)

# 2. Find all contours
imgContours = img.copy()
imgBigContour = img.copy()
contours, hierarchy = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 3)

# 3. Find the biggest contour and use it as sudoku
biggest, maxArea = biggestContour(contours)
if biggest.size != 0:
    biggest = reorder(biggest)
    cv2.drawContours(imgBigContour, contours, -1, (0, 255, 0), 10)
    pts1 = np.float32(biggest)
    pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgWrapColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))
    imgDetectedDigits = imgBlank.copy()
    imgWrapColored = cv2.cvtColor(imgWrapColored, cv2.COLOR_BGR2GRAY)

    # 4. Split image and find each digit
    imgSolvedDigits = imgBlank.copy()
    boxes = splitBoxes(imgWrapColored)
    # cv2.imshow("Digits", boxes[4])
    numbers = getPrediction(boxes, model)
    imgDetectedDigits = displayNumbers(imgDetectedDigits, numbers, color=(255, 0, 255))
    numbers = np.asarray(numbers)
    posArray = np.where(numbers > 0, 0, 1)

    # 5. Solve board
    board = np.array_split(numbers, 9)
    try:
        sudokuSolver.solve(board)
    except Exception as e:
        print(f"Sudoku solver failed: {e}")

    flatList = []
    for sublist in board:
        for item in sublist:
            flatList.append(item)

    solvedNumbers = np.array(flatList) * posArray  # FIXED: convert to np.array
    imgSolvedDigits = displayNumbers(imgSolvedDigits, solvedNumbers, color=(0,255,255))

    # 6. Overlay Solution
    pts2 = np.float32(biggest)
    pts1 = np.float32([[0,0],[widthImg,0],[0,heightImg],[widthImg,heightImg]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgInvWarpColored = cv2.warpPerspective(imgSolvedDigits, matrix, (widthImg, heightImg))
    inv_perspective = cv2.addWeighted(imgInvWarpColored, 1, img, 0.5, 1)
    imgDetectedDigits = drawGrid(imgDetectedDigits)
    imgSolvedDigits = drawGrid(imgSolvedDigits)

    imageArray = ([img, imgThreshold, imgBigContour, imgWrapColored],
                  [imgDetectedDigits,imgSolvedDigits,inv_perspective,imgBlank])
    stackedImage = stackImages(imageArray, 0.5)
    cv2.imshow("StackedImage", stackedImage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

else:
    print("No Sudoku puzzle found in the image.")
