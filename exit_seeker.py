import pygame
import random
from pprint import pprint
 
pygame.init()

CLIFF_COLOR = (255, 50, 50)
NOT_CLIFF_COLOR = (100, 150, 255)
GAMER_COLOR = (0, 255, 0)
GOAL_COLOR = (255, 255, 0)

class State:
    def __init__(self, type, x, y, number_i, number_j):
        self.type = type
        self.x = x
        self.y = y
        self.right = None
        self.left = None
        self.up = None
        self.down = None
        self.color = None
        self.number_i = number_i
        self.number_j = number_j
        self.is_current_state = False
        self.assign_color()

    def assign_color(self):
        if self.type == "cliff":
            self.color = (255, 50, 50)
        elif self.type == "not_cliff":
            self.color = (100, 150, 255)
        elif self.type == "gamer":
            self.color = GAMER_COLOR


def get_max(array, directions):
    forbidden_indices = set()
    for i in range(len(directions)):
        direction = directions[i]
        if direction[0] < 0 or direction[0] > n - 1 or direction[1] < 0 or direction[1] > m - 1:
            forbidden_indices.add(i)
    max_value = -1e17
    max_value_indices = []
    for i in range(len(array)):
        if array[i] > max_value:
            max_value_indices = [i]
            max_value = array[i]
        elif array[i] == max_value:
            max_value_indices.append(i)
    random_index = random.randint(0, len(max_value_indices) - 1)
    return max_value_indices[random_index]


fps = 10
fpsClock = pygame.time.Clock()
 
width, height = 1080, 540
screen = pygame.display.set_mode((width, height))
start_position = (0, 0)
n = 10
m = 6
block_size_x = width // n
block_size_y = height // m
alpha = 0.9
gamma = 0.9
quit_game = False

x_divisions = [i * block_size_x for i in range(n)]
y_divisions = [i * block_size_y for i in range(m)]

states = {}
q_table = {}
cliff_coordinates = set()
for i in range(len(x_divisions)):
    for j in range(len(y_divisions)):
        if j == 0 and i > 0 and i < n - 1:
            block_type = "cliff"
            cliff_coordinates.add((i, j))
        else:
            block_type = "not_cliff"
        state = State(block_type, x_divisions[i], y_divisions[j], i, j)
        if i == n - 1 and j == 0:
            state.color = GOAL_COLOR
        states[(i, j)] = state
        q_table[(i, j)] = [0, 0, 0 ,0]

while not quit_game:
    done = False
    current_position = (0, 0)
    gamer = State("gamer", 0, 0, 0, 0)
    while not done:
        screen.fill((255, 255, 255))
        current_x = current_position[0]
        current_y = current_position[1]
        # [0, 0, 0, 0] = [U, D, L, R, ]
        up = (current_x, current_y - 1)
        down = (current_x, current_y + 1)
        left = (current_x - 1, current_y)
        right = (current_x + 1, current_y)
        directions = [up, down, left, right]
        for i in range(len(q_table[current_position])):
            direction = directions[i]
            if direction[0] >= 0 and direction[0] < n and direction[1] >= 0 and direction[1] < m:
                if direction in cliff_coordinates:
                    reward = -100
                elif direction == (n - 1, 0):
                    reward = 0
                else:
                    reward = -1
                q_table[current_position][i] = q_table[current_position][i] + alpha * (reward + gamma * max(q_table[direction]) - q_table[current_position][i])
            else:
                q_table[current_position][i] = -1e17
        max_value_index = get_max(q_table[current_position], directions)
        current_position = directions[max_value_index]
        gamer.x = current_x * block_size_x
        gamer.y = current_y * block_size_y
        if current_position in cliff_coordinates:
            done = True
        if current_position == (n - 1, 0):
            done = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                quit_game = True
        for i in range(n):
            grid_x = x_divisions[i]
            pygame.draw.line(screen, (0, 0, 0), (grid_x, 0), (grid_x, height))
        for i in range(m):
            grid_y = y_divisions[i]
            pygame.draw.line(screen, (0, 0, 0), (0, grid_y), (width, grid_y))
        for i in range(n):
            for j in range(m):
                state = states[(i, j)]
                pygame.draw.rect(screen, state.color, pygame.Rect(state.x + 1, state.y + 1, block_size_x - 1, block_size_y - 1))
        pygame.draw.rect(screen, gamer.color, pygame.Rect(gamer.x + 1, gamer.y + 1, block_size_x - 1, block_size_y - 1))
        pygame.display.flip()
        fpsClock.tick(fps)

pygame.quit()