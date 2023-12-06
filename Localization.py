import cv2
import numpy as np
import matplotlib.pyplot as plt

def plate_detection(image):
    """
    In this file, you need to define plate_detection function.
    To do:
        1. Localize the plates and crop the plates
        2. Adjust the cropped plate images
    Inputs:(One)
        1. image: captured frame in CaptureFrame_Process.CaptureFrame_Process function
        type: Numpy array (imread by OpenCV package)
    Outputs:(One)
        1. plate_imgs: cropped and adjusted plate images
        type: list, each element in 'plate_imgs' is the cropped image(Numpy array)
    Hints:
        1. You may need to define other functions, such as crop and adjust function
        2. You may need to define two ways for localizing plates(yellow or other colors)
    """

    # TODO: Replace the below lines with your code.
    #masked = masked_image(image, 10,31,112,255,56,255) #75, 85, 70
    #masked = masked_image(image, 12, 29, 128, 254, 78, 251) #78, 100, 80
    #masked = masked_image(image, 14, 27,144,238, 99, 229) #78, 92, 60
    masked = masked_image(image, 13, 28, 136,246,89, 240) #78, 100, 80
    plates, boxes = crop_plates(masked, image)
    copied = np.copy(image)
    for box in boxes:
        copied[box.y1, box.x1:(box.x2+1)] = [0,255,0]
        copied[box.y2, box.x1:(box.x2+1)] = [0,255,0]
        copied[box.y1:(box.y2+1), box.x1] = [0,255,0]
        copied[box.y1:(box.y2+1), box.x2] = [0,255,0]
    plotImage(cv2.cvtColor(copied, cv2.COLOR_BGR2RGB), "Annotated")
    return plates

def masked_image(image, minH, maxH, minS, maxS, minV, maxV):
    """
    This function applies a color to mask to an image in order to make everything with 
    a color outside of the given range. This is used to have an image that only shows the
    color of the license plate. The parameters minH, maxH, minS, maxS, minV, maxV determine
    the desired color range in HSV format.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    colorMin = np.array([minH, minS, minV])
    colorMax = np.array([maxH, maxS, maxV])

    mask = cv2.inRange(hsv, colorMin, colorMax)
    masked = np.copy(hsv)
    masked[mask == 0] = [0,0,0]

    #plotImage(cv2.cvtColor(masked, cv2.COLOR_HSV2RGB), "")
    return masked

def crop_plates(masked, original):
    """
    This function, given a masked image, crops the parts of the image that contain license plates.
    It returns a list of the cropped images.
    """
    bgr = cv2.cvtColor(masked, cv2.COLOR_HSV2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    binary = np.copy(gray)
    binary[gray!=0] = 255
    #plotImage(binary, "", cmapType="gray")
    i = 0
    images = []
    boxes = []
    while i < binary.shape[0]:
        if len(images) == 2:
            break
        j = 0
        while j < binary.shape[1]:
            if binary[i][j] != 0:
                old_i = i
                while np.count_nonzero(binary[i]) != 0 and i < binary.shape[0]-1:
                    i += 1
                a = 0
                while np.count_nonzero(binary[old_i:i, a]) == 0 and a < binary.shape[1]-1:
                    a += 1
                old_a = a
                while np.count_nonzero(binary[old_i:i, a]) != 0 and a < binary.shape[1]-1:
                    a += 1
                if a-old_a >= 70:
                    images.append(gray[old_i:i, old_a:a])
                    boxes.append(BoundingBox(old_a, old_i, a-1, i-1))
                    binary[old_i:i, old_a:a] = 0
                    i = min(old_i + 1, binary.shape[0])
                    j = 0
                else:
                    i = min(old_i + 1, binary.shape[0])
                    j = min(a, binary.shape[1])
            j += 1
        i += 1
    #plotImage(images[1], "Image", cmapType="gray")
    return images, boxes

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

# Displays a given RGB image using matplotlib.pyplot
def plotImage(img, title, cmapType=None):
    # Display image
    if (cmapType):
        plt.imshow(img, cmap=cmapType, vmin=0, vmax=255)
    else:
        plt.imshow(img, vmin=0, vmax=255)
    plt.title(title)
    plt.show()