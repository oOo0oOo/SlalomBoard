import sys
import pygame
from pygame.locals import QUIT, KEYDOWN, K_LEFT, K_RIGHT, K_DOWN
from geometry import Point, Vector

class SlalomBoard(object):
	def __init__(self, position, direction):
		self.start = position.copy()
		self.position = position
		self.direction = direction
		self.player = 0.0

	def board_vector(self):
		pos = Point(self.position.x, self.start.y)
		board = Vector(pos, pos.transform(self.direction))
		return board

	def player_vector(self):
		scaled =  self.board_vector().scale_absolute(10)
		return scaled.normal_vector(-self.player)

	def lean(self, left = True):
		l = 0.003
		if self.player != 0.0:
			l /= 0.8 * (abs(self.player) / l)

		if l<0.0001:
			l = 0.0001

		max_lean = 0.02

		l = 0.003
		if left:
			if self.player-l >= -max_lean:
				self.player -= l
			else:
				self.player = -max_lean
		else:
			if self.player+l <= max_lean:
				self.player += l
			else:
				self.player = max_lean

	def pump(self):
		vector = Vector(Point(0,0), self.direction)
		self.direction = vector.scale_absolute(vector.length() + 1).vect

	def on_tick(self):
		# Calculate the new direction
		board = self.board_vector().vect
		player = self.player_vector().vect
		new_dir = board.transform(player)

		#You can not go backwards
		if new_dir.y < 0:
			new_dir.y = 0

		# You can only go a certain speed
		# and you are slowed down 
		max_speed = 25
		break_speed = 3
		slowed = 0.05

		vector = Vector(Point(0,0), new_dir)
		if vector.length() > max_speed:
			new_dir = vector.scale_absolute(max_speed - slowed).vect
		elif vector.length() > break_speed:
			new_dir = vector.scale_absolute(float(vector.length()) - slowed).vect

		new_pos = self.position.transform(new_dir)
		self.direction = new_dir
		self.position = new_pos


class Game(object):
	def __init__(self, size, start):
		self.size = size

		self.start = Point(size[0] / 2, start)
		direction = Point(0, 10)

		self.board = SlalomBoard(self.start, direction)

		self.markings = []
		self.trail = []

	def lean(self, left = True):
		self.board.lean(left)

	def board_vector(self):
		return self.board.board_vector()

	def player_vector(self):
		return self.board.player_vector()

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
		found = False

		if board.p1.x < 0:
			self.board.position.x = 0
			found = True
		elif board.p1.x > self.size[0]:
			self.board.position.x = self.size[0]
			found = True

		if found:
			vector = Vector(Point(0,0), self.board.direction)
			self.board.direction = vector.scale_absolute(5).vect

	def on_tick(self):
		self.board.on_tick()
		self.check_collision()
		self.update_markings()

		self.trail.append(self.board.position)
		if len(self.trail) > self.start.y/2:
			self.trail.pop(0)



def main():
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
	black = pygame.Color(0, 0, 0)
	red = pygame.Color(255, 0, 0)
	# The slalom board
	game = Game(game_size, start_pos)

	# The game loop
	while True:
		window.fill(black)

		# Show board vector
		pos = game.board_vector().scale_absolute(15)

		p1 = pos.p1.coordinates()
		p2 = pos.p2.coordinates()
		p3 = pos.relative_point(-1).coordinates()

		# pygame.draw.circle(window, , [int(p) for p in p1], 5, 0)
		pygame.draw.line(window, white, p1, p2, 3)
		pygame.draw.line(window, white, p1, p3, 2)

		# And player vector
		pl = game.player_vector().relative_point(50)
		pygame.draw.line(window, red, p1, pl.coordinates(), 2)

		# And all road markings
		for m in game.markings:
			pygame.draw.line(window, white, (middle, m), (middle, m+50), 8)

		# Show trail
		position = game.board.position
		for i, point in enumerate(reversed(game.trail)):
			y =  point.y - position.y + start_pos
			pygame.draw.circle(window, red, (int(point.x), int(y)), 1, 0)

		#Handle events
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
		
		# Movement events
		keys = pygame.key.get_pressed()
		if keys[K_LEFT]:
			game.lean(True)
		if keys[K_RIGHT]:
			game.lean(False)
		if keys[K_DOWN]:
			game.board.pump()


		pygame.display.update()

		game.on_tick()

		fpsClock.tick(40)

if __name__ == '__main__':
	main()

