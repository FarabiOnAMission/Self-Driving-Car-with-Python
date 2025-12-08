import pygame
import math
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1920, 1080 
ROAD_COLOR = (100, 100, 100)
GRASS_COLOR = (0, 100, 0)
CAR_COLOR = (255, 0, 0)
RAY_COLOR = (0, 255, 255)
BORDER_COLOR = (255, 255, 255)
CHECKPOINT_COLOR = (255, 0, 0) # Color for visible debug gates

# START: Top Left, safely on the road, facing Right
START_X, START_Y = 150, 200
START_ANGLE = 0

# --- DEFINE CHECKPOINTS (GATES) ---
# I placed these roughly where your track points are.
# Format: pygame.Rect(x, y, width, height)
# You might need to tweak the sizes slightly to cover the full road width.
CHECKPOINTS = [
    pygame.Rect(100, 150, 100, 100),   # 0: Start
    pygame.Rect(500, 150, 100, 100),   # 1: First Straight
    pygame.Rect(900, 350, 100, 100),   # 2: The Dip
    pygame.Rect(1400, 100, 100, 100),  # 3: The Climb
    pygame.Rect(1750, 250, 100, 100),  # 4: The Dive Top
    pygame.Rect(1550, 550, 100, 100),  # 5: Technical Entry
    pygame.Rect(1350, 850, 100, 100),  # 6: Technical Mid
    pygame.Rect(950, 650, 100, 100),   # 7: The Hairpin Top
    pygame.Rect(750, 850, 100, 100),   # 8: Hairpin Exit
    pygame.Rect(250, 650, 100, 100),   # 9: Back Stretch
    pygame.Rect(100, 350, 100, 100)    # 10: Final Turn (near start)
]

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = START_ANGLE
        self.speed = 5
        self.radars = []
        self.width = 40
        self.height = 20
        self.center = [self.x, self.y]
        self.alive = True
        
        # --- NEW FITNESS VARIABLES ---
        self.current_checkpoint = 1 # Start by looking for index 1 (since we spawn at 0)
        self.fitness = 0
        self.time_alive = 0 # Optional: To kill idle cars

    def draw(self, screen):
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        car_surface.fill(CAR_COLOR)
        rotated_car = pygame.transform.rotate(car_surface, -self.angle)
        rect = rotated_car.get_rect(center=self.center)
        screen.blit(rotated_car, rect.topleft)
        
        if self.alive:
            for dist, end_pos in self.radars:
                pygame.draw.line(screen, RAY_COLOR, self.center, end_pos, 1)
                pygame.draw.circle(screen, RAY_COLOR, end_pos, 3)

    def update(self, map_surface):
        if not self.alive: return

        # 1. Move
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed
        self.center = [int(self.x), int(self.y)]

        # 2. Collision Check (Grass)
        if (0 < self.x < WIDTH and 0 < self.y < HEIGHT):
            current_color = map_surface.get_at((int(self.x), int(self.y)))
            if current_color != ROAD_COLOR and current_color != CHECKPOINT_COLOR: 
                # Note: We check != Checkpoint color so the debug lines don't kill us
                self.alive = False
        else:
            self.alive = False

        # --- 3. CHECKPOINT LOGIC (FIX FOR BACKWARDS DRIVING) ---
        
        # A. Check if we hit the NEXT checkpoint
        if CHECKPOINTS[self.current_checkpoint].collidepoint(self.x, self.y):
            self.fitness += 1000  # Big reward for progress
            self.current_checkpoint += 1
            print(f"Checkpoint {self.current_checkpoint-1} Reached! Fitness: {self.fitness}")
            
            # If we finished the lap (index out of range)
            if self.current_checkpoint >= len(CHECKPOINTS):
                self.current_checkpoint = 0 # Loop back to start (or end game)
                self.fitness += 5000 # Lap bonus

        # B. Check if we went BACKWARD (Hit the previous-previous checkpoint)
        # We look 2 steps back. If I'm aiming for Gate 2, and I hit Gate 0, I went backward.
        elif self.current_checkpoint > 1:
            prev_cp_index = self.current_checkpoint - 2
            if CHECKPOINTS[prev_cp_index].collidepoint(self.x, self.y):
                print("WENT BACKWARDS! KILLED.")
                self.fitness -= 500 # Punishment
                self.alive = False

        # 4. Cast Rays
        self.radars.clear()
        for angle_offset in [-75, -45, 0, 45, 75]:
            self.cast_ray(angle_offset, map_surface)

    def cast_ray(self, angle_offset, map_surface):
        length = 0
        max_len = 65 
        ray_angle = math.radians(self.angle + angle_offset)
        
        while length < max_len:
            length += 5
            check_x = int(self.center[0] + math.cos(ray_angle) * length)
            check_y = int(self.center[1] + math.sin(ray_angle) * length)
            
            if (0 < check_x < WIDTH and 0 < check_y < HEIGHT):
                pixel_color = map_surface.get_at((check_x, check_y))
                # Ignore road AND our red checkpoint markers
                if pixel_color != ROAD_COLOR and pixel_color != CHECKPOINT_COLOR:
                    break
            else:
                break
                
        self.radars.append((length, (check_x, check_y)))

    def get_data(self):
        return [int(r[0]) for r in self.radars]

# --- THE "DEEP LEARNING TRIBUTE" TRACK ---
def draw_track(screen):
    screen.fill(GRASS_COLOR)
    
    # This shape mimics the organic, non-grid style of Samuel Arzt's track
    points = [
        (150, 200), (500, 200), (900, 400), (1100, 400),
        (1400, 150), (1700, 150), (1800, 300), (1800, 500),
        (1600, 600), (1600, 800), (1400, 900), (1100, 900),
        (1000, 700), (900, 700), (800, 900), (500, 900),
        (300, 700), (300, 500), (150, 400), (150, 200) 
    ]
    
    pygame.draw.lines(screen, BORDER_COLOR, True, points, 140) 
    pygame.draw.lines(screen, ROAD_COLOR, True, points, 120)

    # --- DRAW DEBUG CHECKPOINTS ---
    # We draw these so you can see where they are. 
    # They are just outlines.
    for i, rect in enumerate(CHECKPOINTS):
        pygame.draw.rect(screen, CHECKPOINT_COLOR, rect, 2)
        # Optional: Label them if you want
        # font = pygame.font.SysFont("Arial", 12)
        # screen.blit(font.render(str(i), True, (255,255,255)), (rect.x, rect.y))


# --- MAIN LOOP ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Car Training - HARD Track")
    clock = pygame.time.Clock()
    
    map_surface = pygame.Surface((WIDTH, HEIGHT))
    draw_track(map_surface)
    
    car = Car(START_X, START_Y)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- CONTROLS ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            car.angle -= 6
        if keys[pygame.K_RIGHT]:
            car.angle += 6
        
        car.speed = 5
        car.update(map_surface)

        screen.blit(map_surface, (0, 0))
        car.draw(screen)
        
        if not car.alive:
            # Reset
            car.alive = True
            car.x, car.y = START_X, START_Y
            car.angle = START_ANGLE 
            car.current_checkpoint = 1 # Reset checkpoint progress
            car.fitness = 0            # Reset fitness
            print("Car Died. Resetting...")
            
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()