import sys,os,math
from cv2 import cv2
from PIL import Image, ImageOps


output_folder = r"C:\Users\Dasha\Documents\images"
processing_command = r"C:\Users\Dasha\Downloads\processing-3.5.4-windows64\processing-3.5.4\processing-java" #your processing-java path! maybe its in your PATH file. in that case u might just write processing-java
gen_algo_folder = r"C:\Users\Dasha\Downloads\processing-3.5.4-windows64\processing-3.5.4\generativeAlgorithm"
imgFile = output_folder + r"\testit1.png "
img = cv2.imread(imgFile)
if(sys.argv[2] == "0"):
    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
image = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
# create a binary thresholded image
_, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
# find the contours from the thresholded image
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
cnt = sorted(cnts, key=cv2.contourArea)[-1]
x,y,w,h = cv2.boundingRect(cnt)
rgbMatrix = img[y:y+h,x:x+w]
cv2.imwrite(imgFile, rgbMatrix)
inputimg = cv2.imread(imgFile)
height, width, c = inputimg.shape
os.system(processing_command +  r" --sketch=generativeAlgorithm --run " + imgFile + "  " + str(width) + " " + str(height))
ImageOps.expand(Image.open(gen_algo_folder + r"\output.png"),border=20,fill='black').save(gen_algo_folder + r"\output2.png")
silicone = gen_algo_folder + r"\output2.png"
thubberimg = cv2.imread(silicone)
thubberimg = cv2.bitwise_not(thubberimg)
cv2.imwrite(gen_algo_folder + r"\silicone.png",thubberimg)
def makeSVG():
    thubber = gen_algo_folder + r"\silicone.png"
    temp_file = output_folder + r"\temp.pnm"
    os.system(r'magick convert ' + silicone + " " + temp_file)
    os.system(r'potrace ' + temp_file + " -s -o " + output_folder + r'\treegensilicone.svg')
    os.system(r'magick convert ' + thubber + " " + temp_file)
    os.system(r'potrace ' + temp_file + " -s -o " + output_folder +  r'\treegenthubber.svg')
makeSVG()