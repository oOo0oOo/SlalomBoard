import math
import random

class Point(object):
	def __init__(self, x, y):
		self.x = float(x)
		self.y = float(y)

	def __str__(self):
		return 'Point: ({}, {})'.format(self.x, self.y)

	def coordinates(self):
		'''Returns list: [x, y]'''
		return [float(self.x), float(self.y)]

	def transform(self, vector, ratio = 1):
		x = self.x + ratio * vector.x
		y = self.y + ratio * vector.y
		return Point(x, y)

	def copy(self):
		return Point(float(self.x), float(self.y))

class Vector(object):
	def __init__(self, p1, p2):
		self.p1 = p1.copy()
		self.p2 = p2.copy()
		self.vect = Point(self.p2.x - self.p1.x, self.p2.y - self.p1.y)

	def __str__(self):
		return 'Vector:\n{}\n{})'.format(self.p1, self.p2)

	def get(self):
		return self.vect.copy()

	def angle(self):
		if self.length():
			p1 = self.vect
			p2 = Point(1, 0)
			angle = math.acos( (p1.x * p2.x + p1.y * p2.y) / (math.sqrt(p1.x**2 + p1.y**2) * math.sqrt(p2.x**2 + p2.y**2)) )
			return math.degrees(angle)
		else:
			return 0

	def length(self):
		return math.sqrt((self.vect.x**2) + (self.vect.y**2))

	def scale_absolute(self, length):
		scale = float(length) / self.length()
		point = self.relative_point(scale)
		return Vector(self.p1, point)

	def scale_relative(self, ratio):
		return Vector(self.p1, self.relative_point(ratio))

	def transform(self, vector):
		p1 = self.p1.transform(vector)
		p2 = self.p2.transform(vector)
		return Vector(p1, p2)

	def relative_point(self, ratio):
		x = float(self.p1.x + ratio * self.vect.x)
		y = float(self.p1.y + ratio * self.vect.y)
		return Point(x, y)

	def normal_vector(self, scale = 1):
		# Calculate normal vector
		dx = self.p2.x - self.p1.x
		dy = self.p2.y - self.p1.y

		p = Point(-dy, dx)
		if scale != 1:
			p.x *= scale
			p.y *= scale

		return Vector(self.p1, p.transform(self.p1))

	def intersect(self, vector):
		'''
			Intersect another vector with this vector
		'''
		p3 = vector.p1
		p4 = vector.p2
		p1 = self.p1
		p2 = self.p2

		x = (p1.x*p2.y - p1.y*p2.x)*(p3.x - p4.x) - (p1.x - p2.x)*(p3.x*p4.y - p3.y*p4.x)
		x /= ((p1.x - p2.x)*(p3.y - p4.y) - (p1.y-p2.y)*(p3.x-p4.x))

		y = ((p1.x*p2.y - p1.y*p2.x)*(p3.y - p4.y)) - ((p1.y - p2.y)*(p3.x*p4.y - p3.y*p4.x))
		y /= ((p1.x - p2.x)*(p3.y - p4.y) - (p1.y-p2.y)*(p3.x-p4.x))

		return Point(x, y)

	def on_vector(self, point):
		'''
			Check if point is on vector. 
			point = p1 + u * vect
		'''
		uxx, uyy = True, True
		ux, uy = 0, 0
		if self.vect.x != 0:
			ux = (point.x - self.p1.x) / self.vect.x
		else:
			uxx = False

		if self.vect.y != 0:
			uy = (point.y - self.p1.y) / self.vect.y
		else:
			uyy = False

		if ux == uy and 0 <= ux <= 1 and uxx and uyy:
			return True
		elif uxx and 0 <= ux <= 1:
			return True
		elif uyy and 0 <= uy <= 1:
			return True
		else:
			return False

	def circle_collision(self, point, radius):
		minus = Point(self.p2.x - self.p1.x, self.p2.y - self.p1.y)
		diff = Point(self.p1.x - point.x, self.p1.y - point.y)

		a = minus.x **2 + minus.y **2
		b = 2 * ((minus.x * diff.x) + (minus.y * diff.y))
		c = (diff.x **2) + (diff.y **2) - (radius **2)
		delta = b **2 - (4 * a * c)
		
		points = []
		if delta < 0: # No intersection
			pass
		else:
			root = math.sqrt(delta)
			for i in [-1, 1]:
				t = (i * -b + root) / (2 * a)
				x = self.p1.x + (i * minus.x * t)
				y = self.p1.y + (i * minus.y * t)
				points.append(Point(x, y))

		return points

	def closest_point(self, point):
		u = ((point.x - self.p1.x) * (self.p2.x - self.p1.x)) + ((point.y - self.p1.y) * (self.p2.y - self.p1.y))
		u /= ((self.p2.x - self.p1.x) ** 2 + (self.p2.y - self.p1.y) ** 2)
		x = self.p1.x + (u * (self.p2.x - self.p1.x))
		y = self.p1.y + (u * (self.p2.y - self.p1.y))
		p = Point(x, y)
		if self.on_vector(p):
			return p
		else:
			l1 = Vector(self.p1, p).length()
			l2 = Vector(self.p2, p).length()
			if l1 < l2:
				return self.p1.copy()
			else:
				return self.p2.copy()