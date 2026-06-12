import pygame
import math

pygame.init()

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

x, y = 100, 100
target_x, target_y = 600, 400

speed = 200  # pixels per second

running = True
while running:
    dt = clock.tick(60) / 1000  # seconds since last frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dx = target_x - x
    dy = target_y - y
    distance = math.hypot(dx, dy)

    if distance > 1:
        x += (dx / distance) * speed * dt
        y += (dy / distance) * speed * dt

    screen.fill("black")
    pygame.draw.circle(screen, "white", (int(x), int(y)), 10)
    pygame.display.flip()

pygame.quit()