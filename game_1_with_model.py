from keras.models import Sequential
from keras.layers import Dense, InputLayer
from keras.optimizers import adam_v2
import numpy as np
import pygame
import random
import time

pygame.init()
pygame.font.init()
fps = 30
fpsClock = pygame.time.Clock()
font = pygame.font.SysFont("Comic Sans MS", 30) 

initial_gravity = 2.8

width, height = 1080, 720
ground = height * 0.8
screen = pygame.display.set_mode((width, height))

block_size = 64

dino_1 = pygame.image.load("assets/dino_1.png").convert_alpha()
dino_1 = pygame.transform.scale(dino_1, (block_size, block_size))
dino_2 = pygame.image.load("assets/dino_2.png").convert_alpha()
dino_2 = pygame.transform.scale(dino_2, (block_size, block_size))
dino_bend_1 = pygame.image.load("assets/dino_bend_1.png").convert_alpha()
dino_bend_1 = pygame.transform.scale(dino_bend_1, (block_size, block_size // 2))
dino_bend_2 = pygame.image.load("assets/dino_bend_2.png").convert_alpha()
dino_bend_2 = pygame.transform.scale(dino_bend_2, (block_size, block_size // 2))
pterodactyle_hands_up = pygame.image.load("assets/pterodactyle_hands_up.png").convert_alpha()
pterodactyle_hands_up = pygame.transform.scale(pterodactyle_hands_up, (block_size // 2, block_size // 2))
pterodactyle_hands_down = pygame.image.load("assets/pterodactyle_hands_down.png").convert_alpha()
pterodactyle_hands_down = pygame.transform.scale(pterodactyle_hands_down, (block_size // 2, block_size // 2))
cactus = pygame.image.load("assets/cactus.png").convert_alpha()
cactus = pygame.transform.scale(cactus, (block_size // 2, block_size))


def build_model(input_shape, output_shape):
    model = Sequential()
    model.add(InputLayer(batch_input_shape=(1, 3)))
    model.add(Dense(units=10, activation='relu'))
    model.add(Dense(units=3, activation='linear'))

    model.compile(
        loss='mse',
        optimizer=adam_v2.Adam(learning_rate=1),
        metrics=['mae'],
    )
    return model


class Dino(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = dino_1
        self.images_standing = [dino_1, dino_2]
        self.images_bend = [dino_bend_1, dino_bend_2]
        self.epsilon = 0.005
        self.epsilon_decrease = 0.9
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
        self.start_time_change_image = time.time()
        self.stop_time_change_image = time.time()
        self.current_image_standing_index = 0
        self.current_image_bend_index = 0
        self.is_flying = False
        self.has_landed = False
        self.model_predict = None
        self.model_target = None

    def update(self, state):
        # {0 : "jump", 1 : "do nothing", 2 : "bend"}
        action = self.choose_action(state)
        self.last_action = action
        gravity = initial_gravity
        self.v_speed += gravity
        if self.v_speed > 30:
            self.v_speed = 30
        if self.y >= height * 0.8:
            self.is_flying = False
            if time.time() - self.start_time_change_image > 0.1:
                if not self.is_bend:
                    self.image = self.images_standing[self.current_image_standing_index]
                    self.current_image_standing_index += 1
                    self.current_image_standing_index %= len(self.images_standing)
                else:
                    self.image = self.images_bend[self.current_image_bend_index]
                    self.current_image_bend_index += 1
                    self.current_image_bend_index %= len(self.images_bend)
                self.start_time_change_image = time.time()
            self.v_speed = 0
            if self.first_entrance == True:
                self.y = height * 0.8
                self.first_entrance = False
            if self.jump_is_allowed and action == 0:
                self.v_speed = -self.jump_height
                self.is_flying = True
                self.has_landed = True
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
                self.image = dino_1
                self.rect = self.image.get_rect()
                self.y = ground
                self.is_bend = False
                self.jump_is_allowed = True
        else:
            self.has_landed = False
        self.y += self.v_speed
        self.rect.y = self.y
        self.rect.x = self.x

    def learn(self, state, next_state, action_index, gamma, reward, done):
        q_predicted = np.array(self.model_predict(state))
        gamma = 0.9
        q_target = q_predicted.copy()
        q_next = np.array(self.model_target.predict(next_state))
        q_target[0][action_index] = reward + gamma * np.max(q_next[0]) * done
        print(q_target, q_predicted, action_index, reward)
        self.model_predict.fit(state, q_target, batch_size=1, verbose=0)

    def choose_action(self, state):
        # {0 : "jump", 1 : "do nothing", 2 : "bend"}
        is_random_action = np.random.random() < self.epsilon
        if is_random_action:
            print("IT IS RANDOOOOM")
            action = np.random.randint(0, 3)
        else:
            q_predicted_array = self.model_predict.predict(state)
            action = np.argmax(q_predicted_array)
        return action

    def update_model_target(self):
        weights_predict = self.model_predict.get_weights()
        self.model_target.set_weights(weights_predict)
        print("WEIGHTS ARE UPDATED!")

    def save_weights(self, name_predict, name_target):
        self.model_predict.save_weights(name_predict)
        self.model_target.save_weights(name_target)


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


def experience_replay(experience_list):
    random.shuffle(experience_list)
    for experience in experience_list:
        dino.learn(experience[0], experience[1], experience[2], experience[3], experience[4], experience[5])


def generate_obstacle(type, obstacle_width=1.2*width, on_earth=True):
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
    obstacle = Obstacle(obstacle_width, obstacle_height, image, is_animal, images)
    if obstacle.is_animal:
        obstacles_animal.add(obstacle)
    obstacles.add(obstacle)
    obstacles_queue.append(obstacle)
    obstacles_queue_front.append(obstacle)
    return obstacle


def nearest_obstacles_positions(n):
    positions = [[1400.0, 576.0] for i in range(n)]
    for i in range(min(n, len(obstacles_queue))):
        obstacle = obstacles_queue[i]
        position = [obstacle.rect.left, obstacle.rect.top]
        positions[i] = position
    return positions


def update_obstacles_queue():
    give_reward = False
    if obstacles_queue != [] and dino.rect.left > obstacles_queue[0].rect.right:
        obstacles_queue.pop(0)
        give_reward = True
    if obstacles_queue_front != [] and dino.rect.right > obstacles_queue_front[0].rect.left:
        obstacles_queue_front.pop(0)
    return give_reward
    

exit = False
episode = 0
max_time_alive = 0
random_lower_bound = -120
random_upper_bound = 120
true_ground = ground + block_size
model_predict = build_model(4, 3)
model_target = build_model(4, 3)
while not exit:
    episode += 1
    obstacles_h_speed = -13
    obstacles = pygame.sprite.Group()
    obstacles_animal = pygame.sprite.Group()
    obstacles_queue = []
    obstacles_queue_front = []
    experience_list = []
    done = True
    dino = Dino(10, ground)
    dino.model_predict = model_predict
    dino.model_target = model_target
    old_is_flying = dino.is_flying
    reward = -5
    old_reward = reward
    is_awarded = False
    reward_decrease = 0.1
    game_start_time = time.time()
    last_obstacle = generate_obstacle("cactus", obstacle_width=0.55*width + np.random.randint(random_lower_bound, random_upper_bound), on_earth=True)
    text_surface_episode = font.render(f"Episode: {episode}", False, (0, 0, 0))
    text_surface_record = font.render(f"Record: {round(max_time_alive, 0)}", False, (0, 0, 0))
    state_before_jumping = None
    minimum_distance_obstacles = 160 / 7 * obstacles_h_speed + 300
    too_close_to_obstacle = False
    while done:
        text_surface_score = font.render(f"Score: {round((time.time() - game_start_time), 0)}", False, (0, 0, 0))
        # reward += reward_decrease
        game_delta_time = time.time() - game_start_time
        obstacles_h_speed = obstacles_h_speed - 0.00001 * game_delta_time
        minimum_distance_obstacles = 160 / 7 * abs(obstacles_h_speed) + 300
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
                done = False
        random_number = random.randint(0, 1000)
        if random_number > 600 and (last_obstacle is None or abs(last_obstacle.x - 1.2 * width) > minimum_distance_obstacles):
            random_number_for_type = random.randint(0, 10)
            if random_number_for_type > 6:
                last_obstacle = generate_obstacle("pterodactyle", obstacle_width=1.2*width + np.random.randint(random_lower_bound, random_upper_bound), on_earth=False)
            else:
                last_obstacle = generate_obstacle("cactus", obstacle_width=1.2*width + np.random.randint(random_lower_bound, random_upper_bound), on_earth=True)
        obstacles_positions = nearest_obstacles_positions(1)
        state_list = [abs(dino.rect.right - obstacles_positions[0][0]), abs(true_ground - obstacles_positions[0][1]), abs(obstacles_h_speed)]
        state = np.array([state_list])
        state = np.reshape(state, (1, len(state_list)))
        old_is_flying = dino.is_flying
        dino.update(state)
        reward = 200 if dino.last_action == 1 else -5
        if (dino.is_flying == True and old_is_flying == False) or dino.has_landed:
            state_before_jumping = state
        obstacles.update()
        if (dino.is_flying == False and old_is_flying == False) and too_close_to_obstacle == False and abs(dino.rect.right - obstacles_positions[0][0]) < 20:
            action_before_collision = dino.last_action
            state_before_collision = state
            too_close_to_obstacle = True
        give_reward = update_obstacles_queue()
        if give_reward:
            is_awarded = True
        collided_obstacles = pygame.sprite.spritecollide(dino, obstacles, dokill=False)
        if collided_obstacles != []:
            reward = -50000
            done = False
        obstacles_positions = nearest_obstacles_positions(1)
        new_state_list = [abs(dino.rect.right - obstacles_positions[0][0]), abs(true_ground - obstacles_positions[0][1]), abs(obstacles_h_speed)]
        new_state = np.array([new_state_list])
        new_state = np.reshape(new_state, (1, len(new_state_list)))
        if obstacles_queue_front != []:
            first_obstacle = obstacles_queue_front[0]
        else:
            first_obstacle = -1
        if (dino.is_flying == False and old_is_flying == True) or (dino.is_flying and old_is_flying and dino.y >= ground):
            if is_awarded == True:
                reward = 1000
                is_awarded = False
            else:
                reward = -50000
            experience_list.append([state_before_jumping, new_state, 0, 0.4, reward, done])
        elif len(collided_obstacles) != 0 and dino.is_flying == False and old_is_flying == False and too_close_to_obstacle == True:
            experience_list.append([state_before_collision, new_state, action_before_collision, 0.4, reward, done])
        elif dino.is_flying == False and old_is_flying == False:
            experience_list.append([state, new_state, dino.last_action, 0.4, reward, done])
        elif len(collided_obstacles) != 0 and dino.is_flying == True and old_is_flying == True:
            experience_list.append([state_before_jumping, new_state, 0, 0.4, reward, done])
        if int(round((time.time() - game_start_time), 0)) % 30 == 0:
            dino.epsilon *= dino.epsilon_decrease
        pygame.draw.line(screen, (0, 0, 0), (0, height * 0.88), (width, height * 0.88))
        screen.blit(dino.image, (dino.x, dino.y))
        screen.blit(text_surface_episode, (3, 3))
        screen.blit(text_surface_score, (3, 40))
        screen.blit(text_surface_record, (3, 77))
        for obstacle in obstacles:
            screen.blit(obstacle.image, (obstacle.x, obstacle.y))
        pygame.display.flip()
        fpsClock.tick(fps)
    game_over_time = time.time()
    experience_replay(experience_list)
    if episode % 12 == 0:
        dino.update_model_target()
    if episode % 10 == 0:
        dino.save_weights("model_predict_weights_6.h5", "model_target_weights_6.h5")
    time_alive = game_over_time - game_start_time
    if time_alive > max_time_alive:
        with open("records.txt", "a") as fo:
            fo.write(f"{episode} ----- {time_alive}\n")
        max_time_alive = time_alive
        dino.save_weights("model_predict_weights_record.h5", "model_predict_weights_record.h5")

pygame.quit()