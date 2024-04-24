import cv2
import numpy as np

# Load the image in grayscale
image = cv2.imread("../data/2/1.jpg", 0)

# Create a SIFT object
sift = cv2.SIFT_create()

# Detect keypoints and compute descriptors
keypoints, descriptors = sift.detectAndCompute(image, None)

filtered_keypoints = [kp for kp in keypoints if kp.size > 30] 

# Draw filtered keypoints on the image
img_with_filtered_keypoints = cv2.drawKeypoints(image.copy(), filtered_keypoints, None, color=(0,255,0), flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

cv2.imshow("Image with filtered SIFT keypoints", img_with_filtered_keypoints)
cv2.waitKey(0)
cv2.destroyAllWindows()
