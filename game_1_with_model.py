from keras.models import Sequential
from keras.layers import Dense
import numpy as np
import pygame
import random
import time

pygame.init()
fps = 30
fpsClock = pygame.time.Clock()

initial_gravity = 2.8

width, height = 1080, 720
ground = height * 0.8
screen = pygame.display.set_mode((width, height))
minimum_distance_obstacles = 230
obstacles_h_speed = -8

block_size = 64

dino_right = pygame.image.load("assets/dino_right.png").convert_alpha()
dino_right = pygame.transform.scale(dino_right, (block_size, block_size))
dino_bend_1 = pygame.image.load("assets/dino_bend_1.png").convert_alpha()
dino_bend_1 = pygame.transform.scale(dino_bend_1, (block_size, block_size // 2))
pterodactyle_hands_up = pygame.image.load("assets/pterodactyle_hands_up.png").convert_alpha()
pterodactyle_hands_up = pygame.transform.scale(pterodactyle_hands_up, (block_size // 2, block_size // 2))
pterodactyle_hands_down = pygame.image.load("assets/pterodactyle_hands_down.png").convert_alpha()
pterodactyle_hands_down = pygame.transform.scale(pterodactyle_hands_down, (block_size // 2, block_size // 2))
cactus = pygame.image.load("assets/cactus.png").convert_alpha()
cactus = pygame.transform.scale(cactus, (block_size // 2, block_size))



def build_model(input_shape, output_shape):
    model = Sequential()
    model.add(Dense(units=16, activation='relu', input_shape=(4, )))
    # model.add(Dense(units=64, activation='relu'))
    model.add(Dense(units=8, activation='relu'))
    model.add(Dense(units=3, activation='relu'))

    model.compile(
        loss='mse',
        optimizer='adam',
        # metrics=['accuracy'],
    )
    return model


class Dino(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = dino_right
        self.is_bend = False
        self.v_speed = 0
        self.rect = self.image.get_rect()
        self.x = 0.3 * width
        self.y = y - 12
        self.rect.x = self.x
        self.rect.y = self.y
        self.dino_standing_bottom = self.rect.bottom
        self.jump_is_allowed = True
        self.jump_height = 32
        self.first_entrance = True
        self.y_acceleration = 1
        self.last_action = None
        self.model_predict = build_model(4, 3)
        self.model_target = build_model(4, 3)

    def update(self, state):
        # {0 : "jump", 1 : "do nothing", 2 : "bend"}
        action = self.choose_action(state)
        self.last_action = action
        if action == 0 and self.v_speed < 0:
            gravity = initial_gravity * 0.7
        else:
            gravity = initial_gravity
        self.v_speed += gravity
        if self.v_speed > 30:
            self.v_speed = 30
        if self.y > height * 0.8:
            self.v_speed = 0
            if self.first_entrance == True:
                self.y = height * 0.8
                self.first_entrance = False
            if self.jump_is_allowed and action == 0:
                self.v_speed = -self.jump_height
                self.first_entrance = True
            if self.is_bend == False and action == 2:
                self.image = dino_bend_1
                old_bottom = self.rect.bottom
                self.rect = self.image.get_rect()
                # self.delta_y = old_bottom - self.rect.bottom
                self.y = height * 0.8 + block_size // 2
                self.is_bend = True
                self.jump_is_allowed = False
            elif self.is_bend and action != 2:
                self.image = dino_right
                self.rect = self.image.get_rect()
                self.y = ground
                self.is_bend = False
                self.jump_is_allowed = True
        self.y += self.v_speed
        self.rect.y = self.y
        self.rect.x = self.x

    def learn(self, state, next_state, action_index, gamma, reward):
        q_predicted = np.array(self.model_predict(state))
        # print(q_predicted)
        q_target = q_predicted.copy()
        q_next = np.array(self.model_target.predict(next_state)) # here can be mistake (maybe self.model_predict instead of self.model_target)
        q_target[0][action_index] = reward + gamma * np.max(q_next[0])
        self.model_predict.fit(state, q_target, batch_size=1, verbose=0)

    def choose_action(self, state):
        # {0 : "jump", 1 : "do nothing", 2 : "bend"}
        # print(state)
        q_predicted_array = self.model_predict.predict(state)
        action = np.argmax(q_predicted_array)
        return action

    def update_model_target(self):
        weights_predict = self.model_predict.get_weights()
        self.model_target.set_weights(weights_predict)


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, image, is_animal=False, images=[]):
        pygame.sprite.Sprite.__init__(self)
        self.is_animal = is_animal
        self.image = image
        self.h_speed = obstacles_h_speed
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x
        self.rect.y = self.y
        self.start_time_change_image = time.time()
        self.stop_time_change_image = time.time()
        if is_animal:
            self.images = images
            self.current_image_number = 0

    def update(self):
        self.stop_time_change_image = time.time()
        self.x += obstacles_h_speed
        self.rect.x = self.x
        self.rect.y = self.y
        if self.stop_time_change_image - self.start_time_change_image > 0.3:
            if self.is_animal:
                self.current_image_number += 1
                self.current_image_number %= 2
                self.image = self.images[self.current_image_number]
            else:
                pass
            self.start_time_change_image = time.time()
        if self.x < -50:
            self.kill()


def generate_obstacle(type, on_earth=True):
    if type == "pterodactyle":
        image = pterodactyle_hands_up
        is_animal = True
        images = [pterodactyle_hands_up, pterodactyle_hands_down]
    elif type == "cactus":
        image = cactus
        is_animal = False
        images = []
    if on_earth:
        obstacle_height = ground
    else:
        random_number_for_height_type = random.randint(0, 2)
        if random_number_for_height_type == 0:
            obstacle_height = ground - block_size // 2
        elif random_number_for_height_type == 1:
            obstacle_height = ground - block_size // 8
        elif random_number_for_height_type == 2:
            obstacle_height = ground + block_size // 4
    obstacle_width = 1.2 * width
    obstacle = Obstacle(obstacle_width, obstacle_height, image, is_animal, images)
    if obstacle.is_animal:
        obstacles_animal.add(obstacle)
    obstacles.add(obstacle)
    return obstacle


def nearest_obstacles_positions(n):
    positions = []
    obstacles_list = list(obstacles)
    for i in range(min(n, len(obstacles_list))):
        obstacle = obstacles_list[i]
        position = [obstacle.x, obstacle.y]
        positions.append(position)
    return positions

exit = False

counter = 0
while not exit:
    obstacles = pygame.sprite.Group()
    obstacles_animal = pygame.sprite.Group()
    done = True
    dino = Dino(10, ground)
    reward = -5
    reward_decrease = 0.00000001
    game_start_time = time.time()
    last_obstacle = generate_obstacle("cactus", on_earth=True)
    while done:
        counter += 1
        reward += reward_decrease
        game_delta_time = time.time() - game_start_time
        obstacles_h_speed = obstacles_h_speed - 0.00001 * game_delta_time
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
                done = False
        random_number = random.randint(0, 1000)
        if random_number > 980 and (last_obstacle is None or abs(last_obstacle.x - 1.2 * width) > minimum_distance_obstacles):
            random_number_for_type = random.randint(0, 10)
            if random_number_for_type > 9:
                last_obstacle = generate_obstacle("pterodactyle", on_earth=False)
            else:
                last_obstacle = generate_obstacle("cactus", on_earth=True)
        obstacles_positions = nearest_obstacles_positions(1)
        state = np.array([[dino.x, dino.y, obstacles_positions[0][0], obstacles_positions[0][1]]])
        state = np.reshape(state, (1, 4))
        dino.update(state)
        obstacles.update()
        collided_obstacles = pygame.sprite.spritecollide(dino, obstacles, dokill=False)
        if collided_obstacles != []:
            reward = -10
            done = False
        obstacles_positions = nearest_obstacles_positions(1)
        # print(state, "I AM HEREEEEE")
        new_state = np.array([[dino.x, dino.y, obstacles_positions[0][0], obstacles_positions[0][1]]])
        new_state = np.reshape(new_state, (1, 4))
        dino.learn(state, new_state, dino.last_action, 0.9, reward)
        if counter == 50:
            dino.update_model_target()
            counter = 0
        pygame.draw.line(screen, (0, 0, 0), (0, height * 0.88), (width, height * 0.88))
        screen.blit(dino.image, (dino.x, dino.y))
        for obstacle in obstacles:
            screen.blit(obstacle.image, (obstacle.x, obstacle.y))
        pygame.display.flip()
        fpsClock.tick(fps)

pygame.quit()