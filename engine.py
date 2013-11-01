import math
import pygame
import random
import time
from os import listdir
from pygame.locals import QUIT, KEYDOWN, K_LEFT, K_RIGHT, K_SPACE, K_DOWN
from geometry import Point, Vector

# Intialize pygame
pygame.init()

# All the images
bmps = {'potholes': {}, 'boards': {}, 'player': {}, 'signs': {}, 'cars': {}, 'boosts': {}}

for folder in bmps.keys():
	path = 'img/' + folder + '/' 
	files = [path + f for f in listdir(path)]
	for f in listdir(path):
		if f[-4:] in ('.png', '.jpg'):
			p = path + f
			bmps[folder][f[:-4] ] = pygame.image.load(p)


class SlalomBoard(object):
	def __init__(self, **parameters):

		self.start = parameters['start'].copy()
		self.position = self.start.copy()
		self.direction = parameters['direction']
		self.player = 0.0

		# Board Parameters: Leaning
		self.max_lean = parameters['max_lean']
		self.lean_vel = parameters['lean_vel']

		# Max speed
		self.max_speed = parameters['max_speed']
		self.jitter = parameters['jitter'] # How much is the player shaking, when max_speed is reached

		# Breaking 
		self.break_speed = parameters['break_speed']
		self.slowed = parameters['slowed']
		self.break_effect = parameters['break_effect']

		#Pumping
		self.max_pump = parameters['max_pump']
		self.optimal_velocity = parameters['optimal_velocity']
		self.sigma = parameters['sigma']

		# Calculate value at maximum (probagbilty density function, see pump())
		self.pump_scale = 1 / (math.sqrt(2*math.pi*self.sigma**2))

		self.pump_blocked = False


	def board_vector(self):
		pos = Point(self.position.x, self.start.y)
		board = Vector(pos, pos.transform(self.direction))
		return board

	def player_vector(self):
		scaled =  self.board_vector().scale_absolute(10)
		return scaled.normal_vector(-self.player)

	def speed(self):
		return self.board_vector().length()

	def break_board(self):
		scale = self.speed() - self.slowed
		self.direction = self.board_vector().scale_absolute(scale).vect

	def lean(self, left = True):
		l = self.lean_vel
		if left:
			if self.player-l >= -self.max_lean:
				if self.player > 0 and l > self.player:
					self.pump_blocked = False
				self.player -= l
			else:
				self.player = -self.max_lean
		else:
			if self.player+l <= self.max_lean:
				if self.player < 0 and l > abs(self.player):
					self.pump_blocked = False
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
		if not self.pump_blocked:
			self.pump_blocked = True

			dir_vect = Vector(Point(0,0), self.direction)
			velocity = dir_vect.length()

			pump = self.pump_efficiency() * self.max_pump

			self.direction = dir_vect.scale_absolute(velocity + pump).vect

	def on_tick(self):
		# Get the board vector
		board = self.board_vector().vect

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


class ConstantMoving(object):
	def __init__(self, position, moving = Point(0,0), rotation = 0):
		self.position = position
		self.moving = moving
		self.rotation = rotation

	def on_tick(self, speed):
		self.position = self.position.transform(self.moving)
		self.position.y -= speed


class Rectangular(ConstantMoving):
	def __init__(self, position, moving, rotation, image, size_x = False):
		ConstantMoving.__init__(self, position, moving, rotation)
		self.img = image
		self.size = image.get_size()
		if size_x:
			factor = float(size_x)/self.size[0]
			self.size = [s * factor for s in self.size]

	def on_tick(self, speed):
		super(Rectangular, self).on_tick(speed)

	def check_collision(self, point):
		h_x = float(self.size[0])/2
		h_y = float(self.size[1])/2
		pos = self.position
		if pos.x - h_x < point.x < pos.x + h_x and pos.y- h_y < point.y < pos.y + h_y:
			return True
		else:
			return False


class Boost(Rectangular):
	def __init__ (self, position, moving, rotation, image, size_x = False, speed = 0):
		Rectangular.__init__(self, position, moving, rotation, image, size_x)
		self.speed = speed


class CircularObstacle(object):
	def __init__(self, position, rotation, radius, image, speed = 0):
		self.radius = radius
		self.position = position
		self.img = image
		self.rotation = rotation
		self.speed = float(speed)

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
	def __init__(self, parameters):
		self.parameters = parameters
		self.general = parameters['general']
		self.size = self.general['street_size']

		self.start = Point(self.size[0] / 2, self.general['start_pos'])
		direction = Point(0, 10)

		# Add parameters to board dict and create an instance
		board_params = parameters['board']
		board_params.update({'direction': Point(0, 5), 'start': self.start})
		self.board = SlalomBoard(**board_params)

		self.obstacles = []
		self.texts = []
		self.markings = []
		self.trail = []

		self.last_random = 0
		self.last_milestone = 0
		self.speed_warning = 0

		# Setup checkpoint system
		self.dist_checkpoint = int(self.general['dist_checkpoint'])
		self.time_checkpoint = int(self.general['time_checkpoint'])
		self.delta_time = int(self.general['delta_time'])
		self.delta_dist = int(self.general['delta_dist'])
		self.num_checkpoint = 0

		self.next_checkpoint = int(self.dist_checkpoint)
		self.last_checkpoint = time.clock()

		self.setup_game()

	def setup_game(self):
		# Setup parameters (position 0 are initial parameters)
		self.set_parameters(self.parameters['elements'][0])
		# and remove parameters
		del self.parameters['elements'][0]
		if self.parameters['elements']:
			self.next_upd = min(self.parameters['elements'].keys())

	def set_parameters(self, parameters):
		self.step_size = parameters['step_size']
		self.obstacle_params = parameters['obstacles']

		self.boosts = parameters['boosts']

		self.forward_cars = parameters['forward_cars']
		self.backwards_cars = parameters['backwards_cars']
		self.backwards_cars.update({'forward': False})

		if parameters['message']:
			start = Point(self.start.x, self.size[1] - 50)
			text = FloatingText(parameters['message'], start, (245, 245, 245), 350, 100, 'helvetica', 60, Point(0, -2))
			self.texts.append(text)



	def board_vector(self):
		return self.board.board_vector()


	def player_vector(self):
		return self.board.player_vector()


	def random_boost(self, probability = 0.01, size = (40, 60), speed = (30, 40)):
		if random.random() < probability:
			y = self.size[1] + 500
			x = random.randrange(0, self.size[0])

			width = random.randrange(size[0], size[1])
			speed = random.randrange(speed[0], speed[1])
			rotation = 180

			key = random.choice(bmps['boosts'].keys())
			self.obstacles.append(Boost(Point(x, y), Point(0,0), rotation, bmps['boosts'][key], width, speed))


	def random_pothole(self, probability = 0.01, size = (3, 20), speed = (50, 80)):
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
			speed = random.randrange(speed[0], speed[1]+1)

			key = random.choice(bmps['potholes'].keys())
			self.obstacles.append(CircularObstacle(Point(x, y), rotation, radius, bmps['potholes'][key], speed))

	def random_car(self, probability = 0.01, size = (20, 25), moving = (10, 14), forward = True):
		if random.random() < probability:
			size_x = random.randrange(size[0], size[1])

			x = random.randrange(50, (self.size[0] / 2) - 50)

			forw_pos = self.size[1] + 300
			rev_pos = -200
			
			if forward:
				speed = Point(0, random.randrange(moving[0], moving[1]))

				if self.board.speed() > speed.y or random.random() < 0.5:
					position = Point(self.start.x - x, forw_pos)
				else:
					position = Point(self.start.x - x, rev_pos)
				rotation = 90

			else:
				position = Point(self.start.x + x, forw_pos)
				speed = Point(0, -random.randrange(moving[0], moving[1]))
				rotation = 270

			key = random.choice(bmps['cars'].keys())
			image = bmps['cars'][key]

			car = Rectangular(position, speed, rotation, image, random.randrange(size[0], size[1]))

			self.obstacles.append(car)


	def remove_obstacles(self):
		len_ob = len(self.obstacles)
		for i, o in enumerate(reversed(self.obstacles)):
			if o.position.y < - 500 or o.position.y > 2 * self.size[1]:
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
		vector = Vector(Point(0,0), self.board.direction)
		for ob in self.obstacles:
			if ob.check_collision(board.p1):
				if type(ob) == CircularObstacle:
					cur = self.board.speed()
					breaking = ob.speed / 100
					if cur * breaking > self.board.break_speed:
						self.board.direction = vector.scale_relative(breaking).vect
					break

				elif type(ob) == Boost:
					speed = float(ob.speed)/100
					if self.board.speed() + speed < self.board.max_speed * 1.08:
						self.board.direction = vector.scale_relative(1+speed).vect
					break

				elif type(ob) == Rectangular:
					self.board.direction = vector.scale_absolute(1).vect
					break

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

			# Potholes
			self.random_pothole(**self.obstacle_params)
			# Forward and backwards cars
			self.random_car(**self.forward_cars)
			self.random_car(**self.backwards_cars)
			# boosts
			self.random_boost(**self.boosts)

		# Check if player is over the next checkpoint
		if px > self.next_checkpoint:
			self.num_checkpoint += 1

			self.next_checkpoint = self.next_checkpoint + self.dist_checkpoint
			self.last_checkpoint = time.clock()

			# Change time and distance
			self.time_checkpoint += self.delta_time
			self.dist_checkpoint += self.delta_dist
			# Show message
			start = Point(self.start.x, self.size[1] - 50)
			text = FloatingText('CHECKPOINT ' + str(self.num_checkpoint), start, (245, 245, 245), 200, 100, 'helvetica', 80, Point(0, -2))
			self.texts.append(text)

		# Check if player has lost
		if time.clock() > self.last_checkpoint + self.time_checkpoint:
			start = Point(self.start.x, self.size[1] - 50)
			text = FloatingText('GAME OVER', start, (245, 20, 20), 500, 100, 'helvetica', 80, Point(0, -1))
			self.texts.append(text)
			self.last_checkpoint = time.clock()

		# Check if next map update is due
		if self.parameters['elements']:
			if px > self.next_upd:
				# Set new parameters
				self.set_parameters(self.parameters['elements'][self.next_upd])
				del self.parameters['elements'][self.next_upd]

				if self.parameters['elements']:
					self.next_upd = min(self.parameters['elements'].keys())


		# Display how far player is
		if px >= self.last_milestone + 10000:
			self.last_milestone = px
			start = Point(self.size[0], self.size[1] - 50)
			text = FloatingText('{}m'.format(px/100), start, (10, 10, 250), 150, 0, 'helvetica', 50, Point(-3, 0))
			self.texts.append(text)

		# Show speed warning
		if self.speed_warning:
			self.speed_warning -= 1

		if self.board_vector().length() > self.board.max_speed and not self.speed_warning:
			self.speed_warning = 50
			start = Point(self.start.x, self.size[1] - 50)
			text = FloatingText('Too Fast!', start, (245, 5, 5), 200, 50, 'helvetica', 50, Point(0, -2))
			self.texts.append(text)

		# Clean up obstacles & floating texts
		self.remove_obstacles()
		self.remove_texts()


## Setting up pygame and the main gameloop
# all the pygame stuff
def start_game(parameters):
	pygame.init()
	fpsClock = pygame.time.Clock()

	# The game size and the player start position
	general_params = parameters['general']
	game_size = parameters['general']['size']

	# board_size is minus the border
	general_params['street_size'] = (game_size[0] - 2 * general_params['border_size'], game_size[1])
	

	# transpose vector (because of border):
	t_vect = Point(general_params['border_size'], 0)

	middle = game_size[0] / 2
	start_pos = general_params['street_size'][1] / general_params['start_pos']
	general_params.update({'start_pos': start_pos})

	window = pygame.display.set_mode(game_size)
	pygame.display.set_caption('Slalom Boarding')

	# colors
	white = pygame.Color(245, 245, 245)
	brown = pygame.Color(133, 60, 8)
	black = pygame.Color(5, 8, 7)
	red = pygame.Color(255, 30, 30)
	green = pygame.Color(28, 100, 22)
	bright_green = pygame.Color(20, 245, 18)
	blue = pygame.Color(5, 10, 145)

	# Create the game instance
	game = Game(parameters)

	# Some drawing helpers
	def draw_image(bmp, point, rotation = 0, size_x = 10):
		scale = float(size_x) / bmp.get_size()[0]
		# Rotozoom image
		rotated = pygame.transform.rotozoom(bmp, rotation, scale)

		#get the rect of the rotated surf and set it's center to the oldCenter
		rotRect = rotated.get_rect()
		point = point.transform(t_vect)
		rotRect.center = (point.x, point.y)

		window.blit(rotated, rotRect)

	def draw_text(text, position, font = 'helvetica', size = 30, color = (250,240,245)):
		fontObj = pygame.font.SysFont(font, size)
		label = fontObj.render(text, 3, color)

		# Center on point
		rect = label.get_rect()
		# position = position.transform(t_vect)
		rect.center = (position.x, position.y)

		window.blit(label, rect)

	# The game loop
	while True:
		# Draw Street and Borders
		window.fill(black)
		b1 = pygame.Rect(0, 0, general_params['border_size'], game_size[1])
		b2 = pygame.Rect(game_size[0] - general_params['border_size'], 0, general_params['border_size'], game_size[1])
		pygame.draw.rect(window, green, b1)
		pygame.draw.rect(window, green, b2)

		# Draw road markings
		for m in game.markings:
			pygame.draw.line(window, white, (middle, m), (middle, m+80), 10)

		# Draw all the obstacles
		for o in game.obstacles:
			if type(o) in (Rectangular, Boost):
				size = o.size[0]
			elif type(o) == CircularObstacle:
				size = o.radius * 2

			if o.position.y < game_size[1]:
				draw_image(o.img, o.position, o.rotation, size)

			else:
				if type(o) == Boost:
					img = bmps['signs']['arrow_up_green']
				else:
					img = bmps['signs']['arrow_up']

				width = size - (size * (o.position.y - game_size[1]) / 500)
				pos = Point(o.position.x, game_size[1] - 30)
				draw_image(img, pos, 0, width)
				#pygame.draw.circle(window, white, [int(o.position.x), game_size[1] - 10], o.radius, 0)

		# Draw the checkpoint line
		dist_left = game.next_checkpoint - game.board.position.y
		if dist_left < game_size[1] - start_pos:
			y = start_pos + dist_left
			cp = pygame.Rect(general_params['border_size'], y, game_size[0] - general_params['border_size'], 5)
			pygame.draw.rect(window, blue, cp)
		
		# Show trail
		position = game.board.position
		for i, point in enumerate(reversed(game.trail)):
			point = point.transform(t_vect)
			y =  point.y - position.y + start_pos
			pygame.draw.circle(window, red, (int(point.x), int(y)), 1, 0)

		# Show board vector
		pos = game.board_vector().scale_absolute(20)# .transform(t_vect)	
		angle = game.board_vector().angle()
		draw_image(bmps['boards']['standard'], pos.p1, -angle, 75)

		# And player vector
		pl = game.player_vector().transform(t_vect)
		pygame.draw.line(window, blue, pl.p1.coordinates(), pl.relative_point(110).coordinates(), 10)

		# And the player
		# pl = game.player_vector().scale_relative(150)
		#if game.board.player > 0:
		#	img = bmps['player']['front']
		#else:
		#	img = bmps['player']['back']
		#angle = ((-pl.angle() + 90) % 360)

		#draw_image(img, pl.relative_point(0.5), angle, pl.length())

		# Show whether the player can push again
		if not game.board.pump_blocked:
			# A rectangle if pushing is possible
			pump = game.board.pump_efficiency()
			g = 20 + int(235 * pump)
			height = 10 + int(50 * pump)

			color = pygame.Color(10, g, 10)
			rect = pygame.Rect(general_params['border_size'] + 10, 10, 10, height)
			pygame.draw.rect(window, color, rect)
		else:
			pygame.draw.circle(window, red, (general_params['border_size'] + 20,20), 10, 0)

		# Show current speed and fps
		speed = game.board.speed()
		text = str(int(round(2 * speed)))
		if speed > game.board.max_speed:
			c = (245, 10, 10)
		else:
			c = (245, 245, 245)
		draw_text(text, Point(general_params['border_size'] + 55, 22), size = 30, color = c)

		fps = str(int(fpsClock.get_fps())) + ' fps'
		draw_text(fps, Point(game_size[0] - general_params['border_size'], 20), size = 25)

		# Overlay texts
		for t in game.texts:
			draw_text(t.text, t.position.transform(t_vect), t.font, t.size, t.get_color())

		# Show time and distance left
		time_left = round(game.time_checkpoint + game.last_checkpoint - time.clock(), 1)
		dist_left = round(float(game.next_checkpoint - game.board.position.y) / 100, 0)
		draw_text(str(time_left) + 's', Point(game_size[0] - general_params['border_size'], 40), 'helvetica', 25, white)
		draw_text(str(dist_left) + 'm', Point(game_size[0] - general_params['border_size'], 60), 'helvetica', 25, white)

		#Handle events (single press, not hold)
		quitted = False
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				quitted = True

			elif event.type == KEYDOWN and event.key == K_SPACE:
				game.board.pump()
		
		if quitted:
			break
		else:
			# Check for pressed leaning keys
			keys = pygame.key.get_pressed()
			if keys[K_LEFT]:
				game.board.lean(True)
			if keys[K_RIGHT]:
				game.board.lean(False)
			if keys[K_DOWN]:
				game.board.break_board()

			pygame.display.update()

			game.on_tick()

			fpsClock.tick(40)

if __name__ == '__main__':

	params = {	
				'general': {
					'size': (900, 650),
					'border_size': 75,
					'start_pos': 8.0,

					# The loop in the level
					'loop_start': 10000,
					'loop_stop': 20000,
					
					# The checkpoint parameters
					'dist_checkpoint': 5000,
					'time_checkpoint': 33.0,
					'delta_time': -1.0,
					'delta_dist': 2500
				},

				'elements': {0: {
					'message': 'First',
					'step_size': 20,
					'obstacles' : {'probability': 0.02, 'size': (30, 40), 'speed': (6, 6)},
					'boosts': {'probability': 0.0, 'size': (40, 50), 'speed': (20, 40)},
					'forward_cars': {'probability': 0.007, 'size': (50, 75), 'moving': (8, 14)},
					'backwards_cars': {'probability': 0.005, 'size': (50, 75), 'moving': (3, 8)},
					},
					10000: {
					'step_size': 20,
					'message': 'Second',
					'obstacles' : {'probability': 0.05, 'size': (30, 40), 'speed': (6, 6)},
					'boosts': {'probability': 0.1, 'size': (60, 80), 'speed': (20, 40)},
					'forward_cars': {'probability': 0.005, 'size': (80, 100), 'moving': (8, 14)},
					'backwards_cars': {'probability': 0.005, 'size': (80, 100), 'moving': (3, 8)}
					}
					},
				'board': {
					'max_lean': 0.026, 'lean_vel': 0.0015, 'max_speed': 24,
					'jitter': 0.025, 'break_speed': 1, 'slowed': 0.05,
					'break_effect': 1.5, 'max_pump': 4.5, 'optimal_velocity': 10,
					'sigma': 13
					}
				}

	start_game(params)