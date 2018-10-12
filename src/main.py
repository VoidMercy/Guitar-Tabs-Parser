from pdf2image import convert_from_path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pytesseract

def hash_point(x, y):
	return x * height + y

def unhash_point(hashed):
	y = hashed % height
	x = hashed / height
	return (x, y)

def pdf_to_image(filepath):
	#extract images from pdf file
	pages = convert_from_path(filepath)
	c = 0
	for page in pages:
		page.save("out{}.jpg".format(str(c + 1)), "JPEG")
		c += 1

#loads the image and calculates some data using numpy
img = Image.open("out1.jpg").convert("L")
width, height = img.size
print "Width: " + str(width)
print "Height: " + str(height)
data = np.array(img)
sum_rows = data.sum(axis=1)
average_rows = sum_rows / width
mean = average_rows.sum() / height
standard_deviation = np.sqrt(((average_rows - mean)**2).sum() / height)
print "Standard Deviation: " + str(standard_deviation)

#finds the horizontal lines in the score
fig, ax = plt.subplots()
found = False
horizontal_lines = []
ranges = []
for i in range(len(average_rows)):
	z_score = abs(average_rows[i] - mean) / standard_deviation
	if z_score > 3:
		if not found:
			horizontal_lines.append(i)
			ranges.append([i, i])
			#ax.add_artist(plt.Circle((i, average_rows[i]), 2, color='r'))
			found = True
		else:
			ranges[len(ranges) - 1][1] = i
	elif found:
		found = False

print horizontal_lines
print ranges

#erase horizontal lines
for i in horizontal_lines:
	data[i] = 255

#error correction - put back pixels that should belong when the horizontal lines were cut out
neighborhood_sums = []

for i in horizontal_lines:
	for a in range(width):
		cursum = 0
		count = 0
		if a > 0:
			cursum += data[i][a - 1]
			count += 1
		if a > 0 and i > 0:
			cursum += data[i - 1][a - 1]
			count += 1
		if a > 0 and i + 1 < height:
			cursum += data[i + 1][a - 1]
			count += 1
		if i + 1 < height:
			cursum += data[i + 1][a]
			count += 1
		if i > 0:
			cursum += data[i - 1][a]
			count += 1
		if a + 1 < width:
			cursum += data[i][a + 1]
			count += 1
		if a + 1 < width and i > 0:
			cursum += data[i - 1][a + 1]
			count += 1
		if a + 1 < width and i + 1 < height:
			cursum += data[i + 1][a + 1]
			count += 1
		averaged = float(cursum) / count
		neighborhood_sums.append(averaged)

neighborhood_sums = np.array(neighborhood_sums)
mean = neighborhood_sums.sum() / len(neighborhood_sums)
standard_deviation = np.sqrt(((neighborhood_sums - mean)**2).sum() / len(neighborhood_sums))
print mean
print standard_deviation

for i in horizontal_lines:
	for a in range(width):
		cursum = 0
		count = 0
		if a > 0:
			cursum += data[i][a - 1]
			count += 1
		if a > 0 and i > 0:
			cursum += data[i - 1][a - 1]
			count += 1
		if a > 0 and i + 1 < height:
			cursum += data[i + 1][a - 1]
			count += 1
		if i + 1 < height:
			cursum += data[i + 1][a]
			count += 1
		if i > 0:
			cursum += data[i - 1][a]
			count += 1
		if a + 1 < width:
			cursum += data[i][a + 1]
			count += 1
		if a + 1 < width and i > 0:
			cursum += data[i - 1][a + 1]
			count += 1
		if a + 1 < width and i + 1 < height:
			cursum += data[i + 1][a + 1]
			count += 1
		averaged = float(cursum) / count
		z_score = abs(averaged - mean) / standard_deviation
		if z_score > 2:
			data[i][a] = 0

#clean up grayscaled image
data = np.where(data < 200, 0, 255)

#only guitar tab lines
res = []
gucci = False
i = 0
while i < len(horizontal_lines):
	if gucci:
		res += horizontal_lines[i:i+6]
		gucci = False
		i += 6
	else:
		i += 5
		gucci = True
horizontal_lines = res

original_data = np.array(Image.open("out1.jpg"))

#perform BFS on each of the horizontal lines to identify objects
visited = []
for i in horizontal_lines:
	for a in range(width):
		starting_hash = hash_point(i, a)
		if data[i][a] != 255 and starting_hash not in visited:
			#do bfs
			queue = []
			visited.append(starting_hash)
			queue.append(starting_hash)
			least = [999999999999, 999999999999]
			greatest = [-1, -1]
			c = 0
			while len(queue) > 0:
				current_hash = queue.pop(0)
				c += 1
				if c > 200:
					break
				y, x = unhash_point(current_hash)
				least[0] = min(least[0], x)
				least[1] = min(least[1], y)
				greatest[0] = max(greatest[0], x)
				greatest[1] = max(greatest[1], y)
				temp = hash_point(y, x - 1)
				if x > 0 and data[y][x - 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y - 1, x - 1)
				if x > 0 and y > 0 and data[y - 1][x - 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y + 1, x - 1)
				if x > 0 and y + 1 < height and data[y + 1][x - 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y + 1, x)
				if y + 1 < height and data[y + 1][x] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y - 1, x)
				if y > 0 and data[y - 1][x] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y, x + 1)
				if x + 1 < width and data[y][x + 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y - 1, x + 1)
				if x + 1 < width and y > 0 and data[y - 1][x + 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
				temp = hash_point(y + 1, x + 1)
				if x + 1 < width and y + 1 < height and data[y + 1][x + 1] != 255 and temp not in visited:
					visited.append(temp)
					queue.append(temp)
			#print str(least) + " " + str(greatest)
			least[0] -= 3
			least[1] -= 3
			greatest[0] += 2
			greatest[1] += 2
			#once completed bfs, crop the bfs'd area and feed into OCR
			temp = Image.fromarray(data)
			temp = temp.crop((least[0], least[1], greatest[0], greatest[1]))
			conf = pytesseract.image_to_data(temp, config='--psm 10 -c tessedit_char_whitelist=0123456789X').strip().split("\n")[-1].split("\t")[-2]
			text = pytesseract.image_to_string(temp, config='--psm 10 -c tessedit_char_whitelist=0123456789X')
			if abs(int(conf) - 20) <= 3:
				for x in range(greatest[0] - least[0]):
					original_data[least[1]][least[0] + x] = (255, 0, 0)
					original_data[greatest[1]][least[0] + x] = (255, 0, 0)
				for y in range(greatest[1] - least[1]):
					original_data[least[1] + y][least[0]] = (255, 0, 0)
					original_data[least[1] + y][greatest[0]] = (255, 0, 0)
				rect = patches.Rectangle((least[0],least[1]),greatest[0]-least[0],greatest[1]-least[1],linewidth=1,edgecolor='r',facecolor='none')
				ax.add_patch(rect)
				print text
				print conf
				print "*"*30

print "DONE"
im = Image.fromarray(original_data)
im.save("result.jpeg")


#plt.plot(neighborhood_sums)
plt.imshow(data)
plt.show()
