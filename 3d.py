import curses
from curses import wrapper
import math
#vertecies of the mesh
cube = []
#indecies pointing to veretecies of a triangle
tri = []

uvs = []

green = [17,23,29,35,41,47]
blue =  [17,18,19,20,21,22]
red = [17,53,125,161,197]
white = [239,243,247,251,255]
grey = [233,235,237,239,241]
colors = [green, blue, red, white, grey]

scale2d = 150

#distance scalar based on distance to camera point if true
#else to camera plane, should cause lens distortion
lens = True

resolution = [240, 116]
#image information is written onto here, then drawn separately
framebuffer = [[0] * resolution[0] for i in range(resolution[1])]

#ps1 style snapping of vertecies to integers
style = True

#mask of drawn triangles
mask = False

#camera position followed by rotation yaw, pitch and roll
camera = [0, 0, 80, [0, 0, 0]]

#dorection of the light, orthogonal
light_dir = [0, 1, 0]

#offset image by this value
offset = [int(resolution[0]/2), int(resolution[1]/2)]

#texture
tex = [
	[1,2,3,4,0],
	[2,3,4,0,1],
	[3,4,0,1,2],
	[4,0,1,2,3],
	[0,4,3,2,1]]

imatrix = [
		[-1, 0, 1],
		[1, -1, 0],
		[0, 1, 0]]

def matrix_mult(A, B):
	result = [
		[0, 0, 0],
		[0, 0, 0],
		[0, 0, 0]]
	for m in range(len(A)):
		for n in range(len(B[0])):
			for o in range(len(B)):
				result[m][n] += A[m][o] * B[o][n]
	return result

def get_transform(r, p):
	return []

def sumv3(a, b, i):
	return [a[0] + b[0] * i, a[1] + b[1] * i]

def Dot(a, b):
	return a[0] * b[0] + a[1] * b[1]

def get_barycentric(p, a, b, c):
	v0 = sumv3(b, a , -1)
	v1 = sumv3(c, a, -1)
	v2 = sumv3(p, a, -1)
	den = v0[0] * v1[1] - v1[0] * v0[1]
	v = (v2[0] * v1[1] - v1[0] * v2[1]) / den
	w = (v0[0] * v2[1] - v2[0] * v0[1]) / den
#	d00 = Dot(v0, v0)
#	d01 = Dot(v0, v1)
#	d11 = Dot(v1, v1)
#	d20 = Dot(v2, v0)
#	d21 = Dot(v2, v1)
#	denom = d00 * d11 - d01 * d01
#	v = (d11 * d20 - d01 * d21) / denom
#	w = (d00 * d21 - d01 * d20) / denom
	u = float(1) - v - w
	return [u, v, w]

def transform2d(T, P):
	M = [
		[P[0]],
		[P[1]],
		[1]]
	M = matrix_mult(T, M)
	return [M[0][0], M[1][0]]

def load_mesh(name):
	global cube
	global tri
	global uvs
	global tex
	cube = []
	tri = []
	uvs = []
	tex = []
	obj = open(name + ".obj", "r")
	for line in obj:
		if line.startswith("v "):
			clean = line.replace("v ", "")
			li = clean.split(" ")
			x = float(li[0]) * 20
			y = float(li[1]) * 20
			z = float(li[2]) * 20
			cube.append([x, y, z])
		if line.startswith("vt "):
			clean = line.replace("vt ", "")
			ls = clean.split(" ")
			x = float(ls[0])
			y = float(ls[1])
			uvs.append([x, y])
#			uvs = [[0,0], [0,1], [1,0]]
		elif line.startswith("f "):
			clean = line.replace("f ", "")
			ls = clean.split(" ")
			xvals = ls[0]
			yvals = ls[1]
			zvals = ls[2]
			xl = xvals.split("/")
			yl = yvals.split("/")
			zl = zvals.split("/")
			a = int(xl[0])
			auv = int(xl[1])
			b = int(yl[0])
			buv = int(yl[1])
			c = int(zl[0])
			cuv = int(zl[1])
#			tri.append([[a -1, c-1, b-1], [0, 1, 2]])
			tri.append([[a -1, c-1, b-1], [auv - 1, cuv -1, buv - 1]])
	indexes = open(name + ".i", "r")
	for line in list(reversed(list(indexes))):
		i = (line.split(" "))
		j = []
		#i.remove("\n")
		del i[-1]
		for k in i:
			j.append(int(k) -1)
		tex.append(j)
		
	for coord in cube:
		yaw(coord, 180)

#get angle between 2 vectors
def get_angle(a, b):
	la = vlength(a)
	lb = vlength(b)
	return math.acos((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / la / lb) / math.pi

#rotate around each axis
def yaw(p, a):
	try:
		a = math.radians(a)
		x = p[2]
		y = p[0]
		p[2] = x * math.cos(a) - y * math.sin(a)
		p[0] = x * math.sin(a) + y * math.cos(a)
	except:
		raise Exception(p)

def pitch(p, a):
	a = math.radians(a)
	x = p[1]
	y = p[2]
	p[1] = x * math.cos(a) - y * math.sin(a)
	p[2] = x * math.sin(a) + y * math.cos(a)

def roll(p, a):
	a = math.radians(a)
	x = p[0]
	y = p[1]
	p[0] = x * math.cos(a) - y * math.sin(a)
	p[1] = x * math.sin(a) + y * math.cos(a)

#rotate point p in order yaw, pitch, roll by angle values a
def rotate(p, a):
	yaw(p, a[0])
	pitch(p, a[1])
	roll(p, a[2])

#rotate inverse order by negative angle values a
def irotate(p, a):
	roll(p, -a[2])
	pitch(p, -a[1])
	yaw(p, -a[0])

#get length of vector v
def vlength(v):
	return math.sqrt(pow(v[0], 2) + pow(v[1], 2) + pow(v[2], 2))

#get normal of triangle
def get_normal(tri):
	global cube

	#points of triangle in 3d space as floats
	A = cube[tri[0]]
	B = cube[tri[1]]
	C = cube[tri[2]]

	v = [B[0] - A[0], B[1] - A[1], B[2] - A[2]]
	w = [C[0] - A[0], C[1] - A[1], C[2] - A[2]]

	#components of normal vector
	nx = v[1] * w[2] - v[2] * w[1]
	ny = v[2] * w[0] - v[0] * w[2]
	nz = v[0] * w[1] - v[1] * w[0]

	#normal vector length
	nl = vlength([nx, ny, nz])

	#should not happen, if it does somehow happen skip to next triangle
	if nl == 0:
		raise Exception("normal has no length, this is bad!")

	#normal vector of length 1
	normal = [nx / nl, ny / nl, nz / nl]

	return normal

#move the camera by vector v relative to rotation
def move(v):
	global camera

	#inverse rotation
	#a = [-camera[3][0], -camera[3][1], -camera[3][2]]

	#apply inverse rotation in opposite order
	irotate(v, camera[3])

	#apply rotated vector to camera position
	camera[0] += v[0]
	camera[1] += v[1]
	camera[2] += v[2]

#display framebuffer on screen
def write(stdscr):
	global framebuffer
	global resolution

	#clear screen
	stdscr.erase()

	for x in range(resolution[0]):
		for y in range(resolution[1]):
			try:
				stdscr.addstr(y, x * 2, "  ", curses.color_pair(framebuffer[y][x]))
			except:
				pass

#render triangles onto framebuffer
def render():

	global cube
	global light_dir
	global mask
	global tri
	global framebuffer
	global offset
	global camera
	global lens
	global scale2d
	global imatrix

	#empty framebuffer
	framebuffer = [[184] * resolution[0] for i in range(resolution[1])]

	#list of pints projected to 2d space
	arr = []

	#list for sorting
	sarr = []

	for coord in cube:
		#editable coords | rotating the originals ends up very bad, turns out
		a = coord[0] + camera[0]
		b = coord[1] + camera[1]
		c = coord[2] + camera[2]
		p = [a, b, c]

		#rotate relative to camera
		rotate(p, camera[3])

		sarr.append(p)


		#scalar based on distance to camera plane
		#val = math.sqrt(pow(p[0], 2) + pow(p[1], 2) + pow(p[2], 2))
		val = vlength(p)
		if p[2] >= 0.5 and not lens:
			scalar = -1/(p[2])
		#scalar based on distance to camera point
		elif val >= 0.5 and p[2] >= 0.5:
			scalar = -1/val
		#set scalar to false if vertex too close or behind camera
		else:
			scalar = False

		#orthogonal override | looks kinda buggy
		#scalar = -0.01

		#snap vertex to int
		if scalar:
			#cool vertex coordinates that snap to integers (ps1 style)
			if style:
				pos2d = [int(p[0])  * scale2d * scalar, int(p[1]) * scale2d * scalar]
			#boring normal vertex coordinates
			else:
				pos2d = [p[0]  * scale2d * scalar, p[1] * scale2d * scalar]
		else:
			pos2d = scalar
		arr.append(pos2d)

	#sort triangles by their colosest vertex relative to camera | not entirely sure if they are actually positive values, max works best
	tri.sort(key=lambda x: max(sarr[x[0][0]][2], sarr[x[0][1]][2], sarr[x[0][2]][2]), reverse=True)

	for set_ in tri:

		set = set_[0] #indecies of 3d space, and 2d space coordinates of ponits of triangle
		setuv = set_[1] #indecies of uv coordinates of points of triangle

		#if triangle points away from camera skip to next triangle TODO
		normal = get_normal(set)
		#A_dir = copy.deepcopy(cube[set[0]])
		#A_dir = [A_dir[0] - camera[0], A_dir[1] - camera[1], A_dir[2] - camera[2]]
		#irotate(A_dir, camera[3])
		#angle = get_angle(normal, A_dir)
		#if angle < 0:
		#	continue

		#if scalar is False skip to next triangle
		if not arr[set[0]] or not arr[set[1]] or not arr[set[2]]:
			continue

		#res for shorter lines
		res = resolution

		#true if vertex off screen
		aout = (arr[set[0]][0] < -res[0] or arr[set[0]][0] > res[0]) or (arr[set[0]][1] < -res[0] or arr[set[0]][1] > res[1])
		bout = (arr[set[1]][0] < -res[0] or arr[set[1]][0] > res[0]) or (arr[set[1]][1] < -res[0] or arr[set[1]][1] > res[1])
		cout = (arr[set[2]][0] < -res[0] or arr[set[2]][0] > res[0]) or (arr[set[2]][1] < -res[0] or arr[set[2]][1] > res[1])

		#if all verticies off screen skip to next triangle
		if aout and bout and cout:
			continue

		#points of the triangle on the screen as integers
		A = [int(arr[set[0]][0]), int(arr[set[0]][1])]
		B = [int(arr[set[1]][0]), int(arr[set[1]][1])]
		C = [int(arr[set[2]][0]), int(arr[set[2]][1])]


		#false is a vertical line | bool relevant for rendering of each pixel
		if A[0] == B[0]:
			mAB = False
		else:
			mAB = (A[1] - B[1]) / (A[0] - B[0])

		if C[0] == B[0]:
			mBC = False
		else:
			mBC = (B[1] - C[1]) / (B[0] - C[0])

		if C[0] == A[0]:
			mCA = False
		else:
			mCA = (C[1] - A[1]) / (C[0] - A[0])


		#corners of rectangle containing triangle

		#top left corner
		o1 = [min([A[0], B[0], C[0]]), min([A[1], B[1], C[1]])]

		#bottom right corner
		o2 = [max([A[0], B[0], C[0]]), max([A[1], B[1], C[1]])]


		#if points go counter clockwise skip to next triangle, else get upper bounds (ub) and lower bounds (lb)

		#if A on left bounds and B on right bounds points are clockwise if C below AB-line
		#skip to next triangle if counter-clockwise
		#
		#if A on right bounds and B on left bounds points are clockwise if C above AB-line
		#skip to next triangle if clockwise
		#
		#repeat for every other pair

		if A[0] == o1[0] and B[0] == o2[0]:
			y = mAB * (C[0] - A[0]) + A[1]
			if y > C[1]:
				continue
			ub = [[mAB, A]]
			lb = [[mBC, B], [mCA, C]]
		elif B[0] == o1[0] and A[0] == o2[0]:
			y = mAB * (C[0] - A[0]) + A[1]
			if y < C[1]:
				continue
			lb = [[mAB, A]]
			ub = [[mBC, B], [mCA, C]]
		elif B[0] == o1[0] and C[0] == o2[0]:
			y = mBC * (A[0] - B[0]) + B[1]
			if y > A[1]:
				continue
			ub = [[mBC, B]]
			lb = [[mCA, C], [mAB, A]]
		elif C[0] == o1[0] and B[0] == o2[0]:
			y = mBC * (A[0] - B[0]) + B[1]
			if y < A[1]:
				continue
			lb = [[mBC, B]]
			ub = [[mCA, C], [mAB, A]]
		elif C[0] == o1[0] and A[0] == o2[0]:
			y = mCA * (B[0] - C[0]) + C[1]
			if y > B[1]:
				continue
			ub = [[mCA, C]]
			lb = [[mAB, A], [mBC, B]]
		elif A[0] == o1[0] and C[0] == o2[0]:
			y = mCA * (B[0] - C[0]) + C[1]
			if y < B[1]:
				continue
			lb = [[mCA, C]]
			ub = [[mAB, A], [mBC, B]]


		#clap the corners to the size of the framebuffer
		if o1[0] < -resolution[0]/2:
			o1[0] = -resolution[0]/2
		if o1[1] < -resolution[1]/2:
			o1[1] = -resolution[1]/2
		if o2[0] > resolution[0]/2:
			o2[0] = resolution[0]/2
		if o2[1] > resolution[1]/2:
			o2[1] = resolution[1]/2

		#angle difference between normal and light dir
		light_angle = get_angle(normal, light_dir)

		#number of colors 1 to 22 (greyscale)
		c = 4

		#calculate color to display, grayscale in range 233 to 255
		light = int((int((light_angle) * c +0.5)))

		#display mask instead
		if mask:
			color = 23

		#for every pixel in rectangle exactly containing the triangle
		for y in range(int(o1[1]), int(o2[1])):
			for x in range(int(o1[0]), int(o2[0])):

				#assume the pixel is inside the triangle
				draw = True
				for m in lb:
					#if one line is vertical it is skipped here
					if m[0]:
						#if pixel above lb line, don't draw | lb and ub switched for some reason
						p = m[1]
						ylow = m[0] * (x - p[0]) + p[1]
						if  y >= ylow:
							draw = False
							break
				for m in ub:
					#if one line is vertical it is skipped here
					if m[0]:
						#if pixel below ub line, don't draw | lb and ub switched for some reason
						p = m[1]
						ylow = m[0] * (x - p[0]) + p[1]
						if  y < ylow:
							draw = False
							break
				#if draw was set to false go to next pixel
				if not draw:
					continue

				#draw the pixel onto the framebuffer, pass if out of frame
				if not mask:
					try:
						uv = get_barycentric([x, y], A, B, C)
					except:
						continue
					u = uv[0]
					v = uv[1]
					w = uv[2]

					uvA = uvs[set_[1][0]]
					uvB = uvs[set_[1][1]]
					uvC = uvs[set_[1][2]]

					uvx = u * uvA[0] + v * uvB[0] + w * uvC[0]
					uvy = u * uvA[1] + v * uvB[1] + w * uvC[1]

					uvheight = len(tex)
					uvwidth = len(tex[0])

					uvx = (round(uvx * uvheight))
					uvy = (round(uvy * uvwidth))

					if uvheight == uvy:
						uvy -=1
					if uvwidth == uvx:
						uvx -=1

					i = tex[uvy][uvx]
					try:
						color = colors[i][light]
					except:
						raise Exception(i, light)
				

				try:
					if y + offset[1] < 0 or x + offset[0] < 0:
						pass
					else:
						framebuffer[y + offset[1]][x + offset[0]] = color
				except:
					pass

def main(stdscr):

	global scale2d
	global offset
	global cube
	global tri
	global style
	global mask
	global camera
	global resolution
	global lens

	#set to false on game exit
	running = True

	#prepare screen and colors
	stdscr.clear()

	for i in range(0, curses.COLORS):
		curses.init_pair(i+1, 0, i)

	#disable cursor
	curses.curs_set(False)

	#resize screen
	stdscr.resize(resolution[1], resolution[0] * 2)

	#clear screen | must load model before anything is rendered
	stdscr.refresh()

	#main loop
	while running:

		#get user input
		key = stdscr.getch()

		#input handle
		match key:
			case 97: #A			# move camera
				move([-1, 0, 0])	#
			case 115: #S			#
				move([0, 0, 1])		#
			case 100: #D			#
				move([1, 0, 0])		#
			case 119: #W			#
				move([0, 0, -1])	#
			case 120: #X
				camera[1] += 1		# move camera up / down
			case 121: #y			#
				camera[1] -= 1		#
			case 113: #Q		exit
				break
			case 258: #down			# rotate camera
				camera[3][1] -= 1	#
			case 259: #up			#
				camera[3][1] += 1	#
			case 260: #left			#
				camera[3][0] -= 1	#
			case 261: #right		#
				camera[3][0] += 1	#
			case 114: #R 	switch lens
				lens = not lens
			case 111: #O 	switch between styles
				style = not style
			case 108: #L 	rotate light direction clockwise
				a = math.radians(5)
				x = light_dir[0]
				y = light_dir[1]
				light_dir[0] = x * math.cos(a) - y * math.sin(a)
				light_dir[1] = x * math.sin(a) + y * math.cos(a)
			case 107: #K	rotate light direction counter-clockwise
				a = math.radians(-5)
				x = light_dir[0]
				y = light_dir[1]
				light_dir[0] = x * math.cos(a) - y * math.sin(a)
				light_dir[1] = x * math.sin(a) + y * math.cos(a)
			case 106: #J 	switch mask
				mask = not mask
			case 49: #key 1
				load_mesh("1")
			case 50: #key 2
				load_mesh("2")
			case 51: #key 3
				load_mesh("3")
			case 52: #key 4
				load_mesh("1")
			case 53: #key 5
				load_mesh("1")
			case 54: #key 6
				load_mesh("1")
			case 55: #key 7
				load_mesh("1")
			case 56: #key 8
				scale2d -= 1
			case 57: #key 9
				scale2d +=1
			case _:
				pass

		#render and display on screen, pipeline goes here
		render()
		write(stdscr)
		curses.flushinp()
#		time.sleep(0.05)

#start
wrapper(main)

