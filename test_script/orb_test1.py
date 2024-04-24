import cv2
import numpy as np

# Load the image in grayscale
image = cv2.imread("../data/2/3.jpg", 0)

# Create an ORB object (adjust parameters as needed)
orb = cv2.ORB_create(nfeatures=1000)  # Adjust 'nfeatures' for the desired number of features

# Detect keypoints and compute descriptors
keypoints, descriptors = orb.detectAndCompute(image, None)

# Draw keypoints on the image
img_with_keypoints = cv2.drawKeypoints(image.copy(), keypoints, None, color=(0,255,0), flags=0)

# Display the image with keypoints
cv2.imshow("Image with ORB keypoints", img_with_keypoints)
# Save the image with keypoints
cv2.imwrite("data/2/3_orb_keypoints.jpg", img_with_keypoints)
cv2.waitKey(0)
cv2.destroyAllWindows()