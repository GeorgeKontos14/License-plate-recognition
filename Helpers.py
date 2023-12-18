import numpy as np
import cv2
import matplotlib.pyplot as plt

def plotImage(img, title=None, cmapType=None):
    # Display image
    if (cmapType):
        plt.imshow(img, cmap=cmapType, vmin=0, vmax=255)
    else:
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), vmin=0, vmax=255)
    if (title):
        plt.title(title)
    plt.show()

def close(image):
    s1 = np.ones((5,5))
    s2 = np.ones((3,3))
    s3 = np.ones((5,2))
    res = cv2.dilate(image, s1)
    res = cv2.dilate(res, s1)
    res = cv2.dilate(res, s3)
    res = cv2.erode(res, s2)
    return res

def drawBoxes(boxes, image, channel="green"): 
    copied = np.copy(image)
    arr = []
    if channel == "green":
        arr = [0,255,0]
    elif channel == "red":
        arr = [0,0,255]
    else:
        arr = [255,0,0]
    for box in boxes:
        copied[box.y1, box.x1:(box.x2+1)] = arr
        copied[box.y2, box.x1:(box.x2+1)] = arr
        copied[box.y1:(box.y2+1), box.x1] = arr
        copied[box.y1:(box.y2+1), box.x2] = arr
    plotImage(copied)        

class BoundingBox:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def intersection_over_union(self, other):
        """
        Returns the area of the IoU of this bounding box with another bounding box
        """
        x_a = max(self.x1, other.x1)
        y_a = max(self.y1, other.y1)
        x_b = min(self.x2, other.x2)
        y_b = min(self.y2, other.y2)
        
        intersection = (x_b-x_a).clamp(0)*(y_b-y_a).clamp(0)
        box1 = abs((self.x2-self.x1)*(self.y2-self.y1))
        box2 = abs((other.x2-other.x1)*(other.y2-other.y1))

        return intersection/(box1+box2-intersection+1e-6)
    
    def is_close(self, other):
        """
        Returns true if this object and another bounding box are close; False otherwise
        """
        return abs(self.x1-other.x2) < 5 or abs(self.x2-other.x1) < 5 or abs(self.y1-other.y2) < 5 or abs(self.y2-other.y1) < 5
    
    def merge(self, other):
        """
        Merges the two given bounding boxes into one
        """
        box = BoundingBox(0,0,0,0)
        box.x1 = min(self.x1, other.x1)
        box.x2 = max(self.x2, other.x2)
        box.y1 = min(self.y1, other.y1)
        box.y2 = max(self.y2, other.y2)
        return box
    
    def __str__(self):
        return 'x_1: ' + str(self.x1) + '\nx_2: ' + str(self.x2) + '\ny_1: ' + str(self.y1) + '\ny_2: ' + str(self.y2)