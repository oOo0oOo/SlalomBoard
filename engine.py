import sys
import math
import pygame
import random
from os import listdir
from pygame.locals import QUIT, KEYDOWN, K_LEFT, K_RIGHT, K_DOWN
from geometry import Point, Vector


class SlalomBoard(object):
	def __init__(self, position, direction):
		self.start = position.copy()
		self.position = position
		self.direction = direction
		self.player = 0.0

		# Board Parameters: Leaning
		self.max_lean = 0.025
		self.lean_vel = 0.0025

		# Constant breaking & max speed
		self.max_speed = 25
		self.break_speed = 3
		self.slowed = 0.05

		#Pumping
		self.max_pump = 7.5
		self.pump_delay = 15 # in ticks @ 40ms
		self.optimal_velocity = 10
		self.sigma = 8

		# Calculate value at maximum (probagbilty density function, see pump())
		self.pump_scale = 1 / (math.sqrt(2*math.pi*self.sigma**2))

		self.last_pump = self.pump_delay


	def board_vector(self):
		pos = Point(self.position.x, self.start.y)
		board = Vector(pos, pos.transform(self.direction))
		return board

	def player_vector(self):
		scaled =  self.board_vector().scale_absolute(10)
		return scaled.normal_vector(-self.player)

	def lean(self, left = True):
		l = self.lean_vel
		if left:
			if self.player-l >= -self.max_lean:
				self.player -= l
			else:
				self.player = -self.max_lean
		else:
			if self.player+l <= self.max_lean:
				self.player += l
			else:
				self.player = self.max_lean

	def pump(self):
		if self.last_pump >= self.pump_delay:
			self.last_pump = 0

			dir_vect = Vector(Point(0,0), self.direction)
			velocity = dir_vect.length()

			# Scale pumping (best pumping in curve at optimal pumping speed)

			# check how vertical board is & scale to 0-1
			verticality = 1 - ( abs(self.direction.x) / velocity )

			# Check how much the player is leaning outwards scaled 0-1
			leaning = abs(self.player) / self.max_lean

			# Check the speed (is scaled according to normal distributed 
			# around an optimal speed )
			# This is achieved using the probability density function of the normal distribution
			expo = (velocity - self.optimal_velocity)**2 / (2 * self.sigma**2)
			speed = 1 / (math.sqrt(2 * math.pi * self.sigma**2))
			speed *= math.exp(-expo)

			# Scale the speed (value = 1 @ optimal velocity):
			speed /= self.pump_scale

			pump = verticality * leaning * speed * self.max_pump

			print 'PUMP: {}!!!!!'.format(pump)
			self.direction = dir_vect.scale_absolute(velocity + pump).vect

	def on_tick(self):
		# update last pump
		self.last_pump += 1

		# Scale the board according to 
		board = self.board_vector()
		#speed_scale = 1.5 *  board.length() * (1 - (board.length() / self.max_speed + 0.0001 ))
		# print speed_scale
		# board = board.scale_absolute(speed_scale).vect

		board = board.vect

		# Calculate the new direction
		player = self.player_vector().vect
		new_dir = board.transform(player)

		#You can not go backwards
		if new_dir.y < 0:
			new_dir.y = 0

		# You can only go a certain speed
		# and you are slowed down if above a certain speed
		vector = Vector(Point(0,0), new_dir)

		#scale = -1
		#if vector.length() > self.max_speed:
		#	scale = self.max_speed - self.slowed
		if vector.length() > self.break_speed:
			scale = float(vector.length()) - self.slowed
			new_dir = vector.scale_absolute(scale).vect
			
		#if scale != -1:
		#	new_dir = vector.scale_absolute(scale).vect

		new_pos = self.position.transform(new_dir)

		self.direction = new_dir
		self.position = new_pos

class CircularObstacle(object):
	def __init__(self, position, radius, image):
		self.radius = radius
		self.position = position
		self.img = image
		self.rotation = random.randrange(0, 360)

	def on_tick(self, speed_y):
		self.position.y -= speed_y

	def check_collision(self, point):
		if Vector(point, self.position).length() < self.radius:
			return True
		else:
			return False


class Game(object):
	def __init__(self, size, start):
		self.size = size

		self.start = Point(size[0] / 2, start)
		direction = Point(0, 10)

		self.board = SlalomBoard(self.start, direction)

		self.obstacles = []
		self.markings = []
		self.trail = []

		# The create obstacle parameters
		self.step_size = 10

		self.last_random = 0


	def board_vector(self):
		return self.board.board_vector()


	def player_vector(self):
		return self.board.player_vector()


	def random_obstacle(self, probability = 0.01, size = (3, 20)):
		if random.random() < probability:
			# Create a random circular obstacle (with pothole image)
			y = self.size[1] + 50
			x = random.randrange(0, self.size[1])
			radius = random.randrange(size[0], size[1]+1)
			key = random.choice(bmps['potholes'].keys())
			self.obstacles.append(CircularObstacle(Point(x, y), radius, bmps['potholes'][key]))

	def remove_obstacles(self):
		# lower = self.board.position.y - self.start.y - 50
		len_ob = len(self.obstacles)
		for i, o in enumerate(reversed(self.obstacles)):
			if o.position.y < - 50:
				self.obstacles.pop(len_ob - i -1)


	def update_markings(self):
		self.markings = []

		pos = int(self.board.position.y)
		lower = int(self.start.y)
		upper = int(self.size[1])

		for i in range(pos - lower, pos + upper):
			if not i % 150:
				self.markings.append(i - pos)


	def check_collision(self):
		board = self.board_vector()

		# Check collision of board with wall
		found = False
		if board.p1.x < 0:
			self.board.position.x = 0
			found = True
		elif board.p1.x > self.size[0]:
			self.board.position.x = self.size[0]
			found = True

		if found:
			vector = Vector(Point(0,0), self.board.direction)
			self.board.direction = vector.scale_absolute(3).vect
			return

		# Check collision of board with any obstacle
		found = False
		for ob in self.obstacles:
			if ob.check_collision(board.p1):
				found = True
				break

		if found:
			vector = Vector(Point(0,0), self.board.direction)
			self.board.direction = vector.scale_absolute(5).vect

	def on_tick(self):
		# Advance board
		self.board.on_tick()

		# Advance obstacles
		speed_y = self.board.direction.y
		[o.on_tick(speed_y) for o in self.obstacles]

		self.check_collision()
		self.update_markings()

		self.trail.append(self.board.position)
		if len(self.trail) > self.start.y/2:
			self.trail.pop(0)

		# Create new obstacles
		px = int(self.board.position.y)
		if px > self.last_random + self.step_size:
			self.last_random = px
			self.random_obstacle(0.1, (10, 25))

		# Clean up obstacles
		self.remove_obstacles()


## Setting up pygame and the main gameloop
# all the pygame stuff
pygame.init()
fpsClock = pygame.time.Clock()

game_size = (420, 650)
middle = game_size[0]/2
start_pos = game_size[1] / 4

window = pygame.display.set_mode(game_size)
pygame.display.set_caption('Slalom Boarding')

# colors
white = pygame.Color(255, 255, 255)
brown = pygame.Color(133, 60, 8)
black = pygame.Color(0, 0, 0)
red = pygame.Color(255, 0, 0)
blue = pygame.Color(0, 0, 255)

# The slalom board
game = Game(game_size, start_pos)

# All the images
bmps = {'potholes': {}}
for folder in bmps.keys():
	path = 'img/' + folder + '/'
	files = [path + f for f in listdir(path)]
	for f in listdir(path):
		p = path + f
		bmps[folder][f] = pygame.image.load(p)

# Some drawing helpers
def draw_image(bmp, point, rotation = 0, size_x = 10):
	scale = float(size_x) / bmp.get_size()[0]
	# Rotozoom image
	rotated = pygame.transform.rotozoom(bmp, rotation, scale)

	#get the rect of the rotated surf and set it's center to the oldCenter
	rotRect = rotated.get_rect()
	d1, d2 = rotRect.size
	rotRect.center = (point.x, point.y)

	window.blit(rotated, rotRect)

# The game loop
while True:
	window.fill(black)

	# Draw road markings
	for m in game.markings:
		pygame.draw.line(window, white, (middle, m), (middle, m+50), 8)

	# Draw all the obstacles
	for o in game.obstacles:

		# pygame.draw.circle(window, white, [int(p) for p in o.position.coordinates()], o.radius, 0)

		draw_image(o.img, o.position, o.rotation, o.radius * 2)

	# Show board vector
	pos = game.board_vector().scale_absolute(20)

	p1 = pos.p1.coordinates()
	p2 = pos.p2.coordinates()
	p3 = pos.relative_point(-1).coordinates()

	# pygame.draw.circle(window, , [int(p) for p in p1], 5, 0)
	pygame.draw.line(window, brown, p1, p2, 5)
	pygame.draw.line(window, brown, p1, p3, 4)

	# And player vector
	pl = game.player_vector().relative_point(100)
	pygame.draw.line(window, blue, p1, pl.coordinates(), 10)

	# Show trail
	position = game.board.position
	for i, point in enumerate(reversed(game.trail)):
		y =  point.y - position.y + start_pos
		pygame.draw.circle(window, red, (int(point.x), int(y)), 1, 0)

	#Handle events (single press, not hold)
	for event in pygame.event.get():
		if event.type == QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == KEYDOWN and event.key == K_DOWN:
			game.board.pump()
	
	# Check for pressed leaning keys
	keys = pygame.key.get_pressed()
	if keys[K_LEFT]:
		game.board.lean(True)
	if keys[K_RIGHT]:
		game.board.lean(False)

	pygame.display.update()

	game.on_tick()

	fpsClock.tick(40)