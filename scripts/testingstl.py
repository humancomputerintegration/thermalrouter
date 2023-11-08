from numpy2stl import numpy2stl 
from scipy.ndimage import gaussian_filter
from pylab import imread
from PIL import Image, ImageOps

'''
instructions:
1) change algo path to the route to the generativeAlgorithm folder. can b anywhere. i stuck it within my processing folder.

'''

gen_algo_folder = r"C:\Users\Dasha\Downloads\processing-3.5.4-windows64\processing-3.5.4\generativeAlgorithm"
silicone = gen_algo_folder + r"\output.png"

ImageOps.expand(Image.open(silicone),border=50,fill='white').save('output-border.png')

A = (256 * imread(r"output-border.png"))
A = A[:, :, 2] + 1.0*A[:,:, 0] # Compose RGBA channels to give depth
A = gaussian_filter(A, 3)  # smoothing

numpy2stl(A, "thubbermold.stl", scale=0.05, mask_val=1., solid=True)