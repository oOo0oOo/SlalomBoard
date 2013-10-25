import sys
import math
import pygame
import random
from os import listdir
from pygame.locals import QUIT, KEYDOWN, K_LEFT, K_RIGHT, K_SPACE, K_DOWN
from geometry import Point, Vector


class SlalomBoard(object):
	def __init__(self, position, direction):
		self.start = position.copy()
		self.position = position
		self.direction = direction
		self.player = 0.0

		# Board Parameters: Leaning
		self.max_lean = 0.026
		self.lean_vel = 0.0015

		# Constant breaking & max speed
		self.max_speed = 20
		self.break_speed = 1
		self.slowed = 0.05
		self.jitter = 0.025 # How much is the player shaking, when max_speed is reached

		#Pumping
		self.max_pump = 5.5
		self.pump_delay = 25 # in ticks @ 40ms
		self.optimal_velocity = 8
		self.sigma = 13

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

	def speed(self):
		return self.board_vector().length()

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

	def pump_efficiency(self):
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

		return leaning * speed # * verticality

	def pump(self):
		if self.last_pump >= self.pump_delay:
			self.last_pump = 0

			dir_vect = Vector(Point(0,0), self.direction)
			velocity = dir_vect.length()

			pump = self.pump_efficiency() * self.max_pump

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
		if vector.length() > self.break_speed:
			scale = float(vector.length()) - self.slowed
			new_dir = vector.scale_absolute(scale).vect

		if vector.length() > self.max_speed:
			# Jitter player
			change = random.uniform(-self.jitter, self.jitter) # * vector.length() / self.max_speed
			if abs(self.player + change) < self.max_lean:
				self.player += change


		new_pos = self.position.transform(new_dir)

		self.direction = new_dir
		self.position = new_pos



class CircularObstacle(object):
	def __init__(self, position, rotation, radius, image):
		self.radius = radius
		self.position = position
		self.img = image
		self.rotation = rotation

	def on_tick(self, speed_y):
		self.position.y -= speed_y

	def check_collision(self, point):
		if Vector(point, self.position).length() < self.radius:
			return True
		else:
			return False



class FloatingText(object):
	def __init__(self, text, position, color = (245, 245, 245), stay = 100, fading = 20, font = 'helvetica', size = 50, movement = Point(0, 0)):
		'''
			stay indicates the number of frames the text stays.
			fading sets the number of frames it should fade, such that it is gone after stay.
			Movement is a Point instance of the step that should be taken each frame.
		'''
		self.position = position
		self.text = text
		self.color = color
		self.size = size
		self.frames_left = stay
		self.fading = fading
		self.movement = movement
		self.font = font

		# used for fading
		self.intensity = 1.0

	def on_tick(self):
		if self.frames_left:
			self.frames_left -= 1
			self.position = self.position.transform(self.movement)

			# Check if font is faded
			if self.fading and self.frames_left <= self.fading:
				self.intensity = round(float(self.frames_left) / self.fading, 3)

	def get_color(self):
		# Scale color according to the intensity
		color = [int(c * self.intensity) for c in self.color]
		return tuple(color)



class Game(object):
	def __init__(self, size, start):
		self.size = size

		self.start = Point(size[0] / 2, start)
		direction = Point(0, 10)

		self.board = SlalomBoard(self.start, direction)

		self.obstacles = []
		self.texts = []
		self.markings = []
		self.trail = []

		# The create obstacle parameters
		self.obstacle_prob = 0.04
		self.obstacle_size = (15, 40)
		self.step_size = 10

		self.last_random = 0
		self.last_milestone = 0

		self.setup_game()

	def setup_game(self):
		# Show player message
		start = Point(self.start.x, self.size[1] - 50)
		text = FloatingText('GO!!', start, (245, 10, 10), 350, 100, 'helvetica', 60, Point(0, -1))
		self.texts.append(text)


	def board_vector(self):
		return self.board.board_vector()


	def player_vector(self):
		return self.board.player_vector()


	def random_obstacle(self, probability = 0.01, size = (3, 20)):
		if random.random() < probability:
			# Create a random circular obstacle (with pothole image)
			y = self.size[1] + 500

			# Do not set obstacles in the middle or too far outside
			x = random.randrange(30, (self.size[0] / 2) - 20)
			if random.random()>0.5:
				x = self.start.x - x
			else:
				x = self.start.x + x

			radius = random.randrange(size[0], size[1]+1)
			rotation = random.randrange(0, 360)

			key = random.choice(bmps['potholes'].keys())
			self.obstacles.append(CircularObstacle(Point(x, y), rotation, radius, bmps['potholes'][key]))


	def remove_obstacles(self):
		len_ob = len(self.obstacles)
		for i, o in enumerate(reversed(self.obstacles)):
			if o.position.y < - 50:
				self.obstacles.pop(len_ob - i -1)


	def remove_texts(self):
		len_texts = len(self.texts)
		for i, t in enumerate(reversed(self.texts)):
			if t.frames_left == 0:
				self.texts.pop(len_texts - i -1)


	def update_markings(self):
		self.markings = []

		pos = int(self.board.position.y)
		lower = int(self.start.y)
		upper = int(self.size[1])

		for i in range(pos - lower, pos + upper):
			if not i % 220:
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

		#Advance Floating texts
		[t.on_tick() for t in self.texts]

		self.check_collision()
		self.update_markings()

		self.trail.append(self.board.position)
		if len(self.trail) > self.start.y/2:
			self.trail.pop(0)

		# Create new obstacles
		px = int(self.board.position.y)
		if px > self.last_random + self.step_size:
			self.last_random = px

			self.random_obstacle(self.obstacle_prob, self.obstacle_size)

		# Display how far player is
		if px >= self.last_milestone + 10000:
			self.last_milestone = px
			start = Point(self.size[0], self.size[1] - 50)
			text = FloatingText('{}m'.format(px/100), start, (10, 10, 250), 150, 0, 'helvetica', 50, Point(-3, 0))
			self.texts.append(text)

		# Clean up obstacles & floating texts
		self.remove_obstacles()
		self.remove_texts()


## Setting up pygame and the main gameloop
# all the pygame stuff
pygame.init()
fpsClock = pygame.time.Clock()

game_size = (1100, 710)
middle = game_size[0]/2
start_pos = game_size[1] / 8

window = pygame.display.set_mode(game_size)
pygame.display.set_caption('Slalom Boarding')

# speed_font = pygame.font.SysFont("helvetica", 30)


# colors
white = pygame.Color(245, 245, 245)
brown = pygame.Color(133, 60, 8)
black = pygame.Color(5, 8, 7)
red = pygame.Color(255, 30, 30)
green = pygame.Color(20, 245, 18)
blue = pygame.Color(5, 10, 145)

# The slalom board
game = Game(game_size, start_pos)

# All the images
bmps = {'potholes': {}, 'boards': {}, 'player': {}, 'signs': {}}

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

def draw_text(text, position, font = 'helvetica', size = 30, color = (250,240,245)):
	fontObj = pygame.font.SysFont(font, size)
	label = fontObj.render(text, 3, color)

	# Center on point
	rect = label.get_rect()
	d1, d2 = rect.size
	#p.transform(Point(d1/2.0, d2/2.0))
	rect.center = (position.x, position.y)

	window.blit(label, rect)

# The game loop
while True:
	window.fill(black)

	# Draw road markings
	for m in game.markings:
		pygame.draw.line(window, white, (middle, m), (middle, m+80), 10)

	# Draw all the obstacles
	for o in game.obstacles:
		if o.position.y < game_size[1]:
			# pygame.draw.circle(window, white, [int(p) for p in o.position.coordinates()], o.radius, 0)
			draw_image(o.img, o.position, o.rotation, o.radius * 2)
		else:
			max_size = (o.radius * 2)
			width = max_size - (max_size * (o.position.y - game_size[1]) / 500)
			pos = Point(o.position.x, game_size[1] - 30)
			draw_image(bmps['signs']['arrow_up.png'], pos, 0, width)
			#pygame.draw.circle(window, white, [int(o.position.x), game_size[1] - 10], o.radius, 0)
	
	# Show trail
	position = game.board.position
	for i, point in enumerate(reversed(game.trail)):
		y =  point.y - position.y + start_pos
		pygame.draw.circle(window, red, (int(point.x), int(y)), 1, 0)

	# Show board vector
	pos = game.board_vector().scale_absolute(20)	
	angle = game.board_vector().angle()
	draw_image(bmps['boards']['standard.png'], pos.p1, -angle, 75)

	# And player vector
	pl = game.player_vector()
	pygame.draw.line(window, blue, pl.p1.coordinates(), pl.relative_point(110).coordinates(), 10)

	# And the player
	# pl = game.player_vector().scale_relative(150)
	#if game.board.player > 0:
	#	img = bmps['player']['front.png']
	#else:
	#	img = bmps['player']['back.png']
	#angle = ((-pl.angle() + 90) % 360)

	#draw_image(img, pl.relative_point(0.5), angle, pl.length())

	# Show whether the player can push again
	if game.board.last_pump > game.board.pump_delay:
		# A rectangle if pushing is possible
		pump = game.board.pump_efficiency()
		g = 20 + int(235 * pump)
		height = 10 + int(50 * pump)

		color = pygame.Color(10, g, 10)
		rect = pygame.Rect(10, 10, 10, height)
		pygame.draw.rect(window, color, rect)
	else:
		pygame.draw.circle(window, red, (20,20), 10, 0)

	# Show current speed and fps
	speed = game.board.speed()
	text = str(int(round(speed)))

	if speed > game.board.max_speed:
		c = (245, 10, 10)
	else:
		c = (245, 245, 245)

	draw_text(text, Point(55, 22), size = 30, color = c)
	fps = str(int(fpsClock.get_fps())) + ' fps'
	draw_text(fps, Point(game_size[0] - 50, 20), size = 25)

	# Overlay texts
	for t in game.texts:
		draw_text(t.text, t.position, t.font, t.size, t.get_color())

	#Handle events (single press, not hold)
	for event in pygame.event.get():
		if event.type == QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == KEYDOWN and event.key in [K_SPACE, K_DOWN]:
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