import pygame
import racegame
import random
import copy
import sys
from micrograd.engine import Value
from micrograd.nn import MLP


population = 60
mutate_rate=0.1
mutate_amount = 0.5

def mutate(brain,rate,amount):
  new_brain = copy.deepcopy(brain)

  for p in new_brain.parameters():
    if random.random()<rate:
      p.data += random.uniform(-amount,amount)

  return new_brain

def draw_dashboard(screen, font, generation, alive, best_dist):
    panel = pygame.Surface((220, 90))
    panel.set_alpha(180) 
    panel.fill((0, 0, 0))
    screen.blit(panel, (10, 10))

    white = (255, 255, 255)
    green = (0, 255, 0)
    yellow = (255, 255, 0)
    
    txt_gen = font.render(f"Gen: {generation}", True, white)
    txt_alive = font.render(f"Alive: {alive}/{population}", True, green)
    txt_fit = font.render(f"Best Dist: {int(best_dist)}", True, yellow)

    screen.blit(txt_gen, (20, 15))
    screen.blit(txt_alive, (20, 40))
    screen.blit(txt_fit, (20, 65))

class SuperCar(racegame.Car):
    def __init__(self,x,y,brain=None):
        super().__init__(x,y)

        self.speed=5

        if brain:
            self.brain=brain
        else:
            self.brain = MLP(5,[16,16,1])

        self.time_alive=0
    
    def train(self):
      
      tracker = self.get_data()

      inputs = [Value(x) for x in tracker]

      output = self.brain(inputs)
      move = output.data
      
      if move > 0.5:
        self.angle +=5
      elif move <-0.5:
        self.angle -=5
    
    def update(self,map_surface):
      if not self.alive:
        return
      
      self.time_alive+=1

      if self.time_alive>200 and self.current_checkpoint<2:
        self.alive=False


      self.train()
      super().update(map_surface)
      
def run_simulation():
      pygame.init()
      pygame.font.init()
    
      screen = pygame.display.set_mode((racegame.WIDTH, racegame.HEIGHT))
      clock = pygame.time.Clock()
      stat_font = pygame.font.SysFont("Arial", 18, bold=True)
    
      map_surface = pygame.Surface((racegame.WIDTH, racegame.HEIGHT))
      racegame.draw_track(map_surface)

      cars = []

      for _ in range(population):
        new_car = SuperCar(racegame.START_X,racegame.START_Y)
        cars.append(new_car)
      
      generation=1
      running=True

      while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()

        screen.blit(map_surface, (0, 0))

        alivecnt=0
        curr_best_distance=0
        for car in cars:
            if car.alive:
              alivecnt += 1
            car.update(map_surface)
            car.draw(screen)

            if car.fitness > curr_best_distance:
              curr_best_distance = car.fitness
        
        draw_dashboard(screen, stat_font, generation, alivecnt,curr_best_distance)
        if alivecnt==0:
          
          cars.sort(key=lambda c: c.fitness, reverse=True)
          best_car=cars[0]

          new_cars = []
          did_win = best_car.current_checkpoint >= len(racegame.CHECKPOINTS)
          
          if did_win:
            champion_brain = copy.deepcopy(best_car.brain)
            champion = SuperCar(racegame.START_X,racegame.START_Y,brain=champion_brain)
            new_cars.append(champion)

            while(len(new_cars)<population):
              child_brain=mutate(champion_brain,rate=0.05,amount=0.1)
              new_car = SuperCar(racegame.START_X, racegame.START_Y, brain=child_brain)
              new_cars.append(new_car)
          
          else:
            champion_brain = copy.deepcopy(best_car.brain)
            champion = SuperCar(racegame.START_X,racegame.START_Y,brain=champion_brain)
            new_cars.append(champion)

            elites = cars[:5]
            weights = [0.50,0.25,0.10,0.10,0.05]

            while(len(new_cars)<population):
              parent = random.choices(elites,weights,k=1)[0]
              child_brain = mutate(parent.brain,mutate_rate,mutate_amount)
              
              new_cars.append(SuperCar(racegame.START_X,racegame.START_Y,brain = child_brain))
            
          cars=new_cars
          generation+=1
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
  run_simulation()
