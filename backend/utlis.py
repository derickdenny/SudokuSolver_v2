import numpy as np
import cv2
from tensorflow.keras.models import load_model

def intializePredictionModel():
    model = load_model("Resources/model_trained_8.keras")
    return model

# 1-Preprocessing Image
def preProcess(img):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, 1, 1, 11, 2)
    return imgThreshold

# 2 - reorder points for wrap perspective
def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4,1,2), dtype= np.int32)
    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew

# 3. finding the biggest contour
def biggestContour(contours):
    biggest = np.array([])
    maxArea = 0
    for i in contours:
        area = cv2.contourArea(i)
        if area > 50:
            peri = cv2.arcLength(i,True)
            approx = cv2.approxPolyDP(i,0.02*peri,True)
            if area > maxArea and len(approx) == 4:
                biggest = approx
                maxArea = area
    return biggest, maxArea

# 4. Split the image into 81 diff images
def splitBoxes(img):
    rows = np.vsplit(img,9)
    boxes = []
    for row in rows:
        cols = np.hsplit(row,9)
        for box in cols:
            boxes.append(box)
    return boxes

# 5. get prediction on all images
def getPrediction(boxes, model):
    result = []
    for image in boxes:
        img = np.asarray(image)
        img = img[4: img.shape[0] - 4, 4: img.shape[1] - 4]
        img = cv2.resize(img, (32, 32))
        img = img / 255
        img = img.reshape(1, 32, 32, 1)
        predictions = model.predict(img)
        classIndex = np.argmax(predictions, axis=-1)
        probabilityValue = np.amax(predictions)
        print(f"Prediction: {classIndex}, Probability: {probabilityValue:.2f}")
        if probabilityValue > 0.7:
            result.append(classIndex[0])
        else:
            result.append(0)
    return result


# 6. display the solution on the image
def displayNumbers(img, numbers, color=(0,255,0)):
    secW = int(img.shape[1]/9)
    secH = int(img.shape[0]/9)
    for x in range(0,9):
        for y in range(0,9):
            if numbers[(y*9) + x] != 0:
                cv2.putText(img, str(numbers[(y*9) + x]),
                            (x*secW+int(secW/2)-10, int((y+0.8)*secH)),
                            cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            2, color, 2, cv2.LINE_AA)
    return img

# 7. draw grid
def drawGrid(img):
    secW = int(img.shape[1]/9)
    secH = int(img.shape[0]/9)
    for i in range(0,9):
        pt1 = (0,secH*i)
        pt2 = (img.shape[1],secH*i)
        pt3 = (secW*i,0)
        pt4 = (secW*i,img.shape[0])
        cv2.line(img,pt1,pt2,(255,255,0),2)
        cv2.line(img,pt3,pt4,(255,255,0),2)
    return img

# 8. stack images
def stackImages(imgArray, scale):
    rows = len(imgArray)
    if rows == 0 or not isinstance(imgArray[0], (list, np.ndarray)):
        return np.zeros((100, 100, 3), np.uint8)

    rowsAvailable = isinstance(imgArray[0], list)
    first_valid_img = None
    if rowsAvailable:
        for r_idx in range(rows):
            for c_idx in range(len(imgArray[r_idx])):
                if imgArray[r_idx][c_idx] is not None and imgArray[r_idx][c_idx].size > 0:
                    first_valid_img = imgArray[r_idx][c_idx]
                    break
            if first_valid_img is not None:
                break
    else:
        for r_idx in range(rows):
            if imgArray[r_idx] is not None and imgArray[r_idx].size > 0:
                first_valid_img = imgArray[r_idx]
                break

    if first_valid_img is None:
        return np.zeros((100, 100, 3), np.uint8)

    width = first_valid_img.shape[1]
    height = first_valid_img.shape[0]

    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, len(imgArray[x])):
                if imgArray[x][y] is None or imgArray[x][y].size == 0:
                    imgArray[x][y] = np.zeros((height, width, 3), np.uint8)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                if len(imgArray[x][y].shape) == 2:
                    imgArray[x][y] = cv2.cvtColor(imgArray[x][y], cv2.COLOR_GRAY2BGR)
        hor = [np.hstack(imgArray[x]) for x in range(rows)]
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x] is None or imgArray[x].size == 0:
                imgArray[x] = np.zeros((height, width, 3), np.uint8)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            if len(imgArray[x].shape) == 2:
                imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        ver = np.hstack(imgArray)
    return ver
