import skimage.filters as sf
from skimage.io import imsave, imread
from skimage.feature import canny
from scipy.ndimage.filters import sobel, gaussian_filter
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

eps = 10e-6 #for division of zero stuff

#REMINDER: dy = rows, first in numpy indexing, dx = columns, second in numpy indexing

def plot_img(image):
	plt.imshow(image, cmap=plt.cm.gray); plt.show()

def check_edge_grad(source_grads, target_grads):
	#check if opposite diection, then if the orientation is right?
	sdy, sdx = source_grads; tdy, tdx = target_grads
	source_ori = np.arctan(sdy/(sdx+eps)); target_ori = np.arctan(tdy/(tdx+eps))
	if source_ori - target_ori < np.pi/4: #accept as opposite candidate if true (what about direction?)
		return True

	return False


def get_swts(edges, dxs, dys):
	posy, posx = np.where(edges)
	edgeset = set(zip(posy, posx)) #for checking if weve hit another edgepixel in the line
	stroke_widths = np.zeros_like(edges).astype(np.float64)
	stroke_widths[:,:] = np.inf
	maxy,maxx = edges.shape
	nondiscarded_rays = []

	for i in range(len(posx)): #go through all the edge pixels
		this_x = posx[i]; this_y = posy[i]
		dy = dys[this_y, this_x]; dx = dxs[this_y, this_x]
		source_grad = (dy, dx)
		#xs = [this_x]; ys = [this_y]
		xs = []; ys = []

		for step in range(1, 15):
			incrx = int(dx*step); incry = int(dy*step)
			newx = this_x + incrx; newy = this_y + incry
			if newx >= maxx or newy >= maxy or newy < 0 or newx < 0: break

			#xs.append(newx); ys.append(newy) #do we include edge pixels or not?
			if (newy, newx) in edgeset and len(xs) > 0: #we hit another edge
				target_grad = (dys[newy, newx], dxs[newy, newx])
				if check_edge_grad(source_grad, target_grad):
					assign_pixels = (np.array(ys), np.array(xs))
					nondiscarded_rays.append(assign_pixels)
					width = np.hypot(newy - this_y, newx - this_x)
					stroke_widths[assign_pixels] = np.minimum(stroke_widths[assign_pixels], width)

				break

			xs.append(newx); ys.append(newy) #need these to possibly assign new values to these pixels

	for ray in nondiscarded_rays:
		median = np.median(stroke_widths[ray])
		stroke_widths[ray] = np.minimum(stroke_widths[ray], median)


	return stroke_widths

	
img = imread("../images/testimage.png", as_grey=True).astype(np.float64)
img /= np.max(img)
#img = np.array(Image.open("../images/test2.png").convert("L"))
filtered = gaussian_filter(img, sigma=0.5, truncate=3) #5x5 filter
dx = sobel(img, 1).astype(np.float64) * -1 #maybe multiply with -1, easier to think that way (normally white = 1, black = 0)
dy = sobel(img, 0).astype(np.float64) * -1
maxes = np.max(np.abs(np.stack([dx, dy])), axis=0) #for normalizing gradients so the bigger is 1, easier to step
maxes[maxes==0] = 1.0 #if both are zero max is zero, fix divide by zero (number doesnt matter here as zero will be divided)
magnitudes = np.hypot(dx, dy)
dx = dx/maxes
dy = dy/maxes
edges = canny(img, low_threshold=0.3, high_threshold=0.9, sigma=0.5).astype(np.int32)

swts = get_swts(edges, dx, dy)
plot_img(swts)