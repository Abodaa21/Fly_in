import pygame
from parsing import DataValidator

class Visualization:
    def display(self, coords, zone_list, zone_data, connnect_list, solution):
        min_x = min(coords, key=lambda x: x[0])[0]
        max_x = max(coords, key=lambda x: x[0])[0]
        min_y = min(coords, key=lambda x: x[1])[1]
        max_y = max(coords, key=lambda x: x[1])[1]
        pygame.init()
        pygame.mixer.init()
    
        tum_tum_sound = pygame.mixer.Sound("sounds/tum_tum.mp3")
        sound = pygame.mixer.Sound("sounds/screaming.mp3")
        bri_bri_sound = pygame.mixer.Sound("sounds/bri_bri.mp3")
        bananini_sound = pygame.mixer.Sound("sounds/bananini.mp3")
        start_time = pygame.time.get_ticks()
        delay = 1000
        delay_1 = 6000 + delay
        delay_2 = 8000 + delay_1
        running = True
        max_width = max_x - min_x + 1
        max_height = max_y - min_y + 1
        surface = pygame.display.set_mode((2000, 1200))
        radius = int(min(2000 / max_width, 1200 / max_height, 100) / 2.5)
        stopsign = pygame.image.load("images/stopsign.png").convert_alpha()
        stopsign = pygame.transform.scale(stopsign, (32, 32))
        star = pygame.image.load("images/star.png").convert_alpha()
        star = pygame.transform.scale(star, (32, 32))
        tum_tum = pygame.image.load("images/drone.png").convert_alpha()
        bananini = pygame.image.load("images/bananini.png").convert_alpha()
        bri_bri = pygame.image.load("images/bri_bri.png").convert_alpha()
        background = pygame.transform.scale(tum_tum, (2000, 1200))
        blocked = pygame.image.load("images/blocked.png").convert_alpha()
        blocked = pygame.transform.scale(blocked, (32, 32))
        background2 = pygame.transform.scale(bananini, (1000, 1000))
        background3 = pygame.transform.scale(bri_bri, (700, 1000))
        turn = 0
        restricted = []
        first_time = 0
        screaming_sound = True
        while running:
            for event in pygame.event.get():
                if event == pygame.QUIT:
                    running = False
            
            current_time = pygame.time.get_ticks()
            if not first_time and current_time - start_time > delay :
                bananini_sound.play()
                first_time = 1
            elif first_time == 1 and current_time - start_time > delay_1:
                bri_bri_sound.play()
                first_time = 2
            elif first_time == 2 and current_time - start_time > delay_2:
                tum_tum_sound.play()
                start_time = 0
                first_time = 3
            surface.fill((0, 0, 0))
            surface.blit(background3, (1300, 0))
            surface.blit(background2, (-100, 0))
            surface.blit(background, (0, 0))
            for zone1, zone2 in connnect_list.keys():
                pygame.draw.line(surface, "yellow", (((2000 / max_width) * (zone_data[zone1]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone1]["coords"][1]) + 600), (((2000 / max_width) * (zone_data[zone2]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone2]["coords"][1]) + 600), 10)
            for zone in zone_data:
                pygame.draw.circle(surface, "white", (((2000 / max_width) * (zone_data[zone]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone]["coords"][1]) + 600), max(radius - 10, 10) + 3)
                pygame.draw.circle(surface, zone_data[zone]["color"], (((2000 / max_width) * (zone_data[zone]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone]["coords"][1]) + 600), max(radius - 10, 10))
                if zone_data[zone]["zone"] == "restricted":
                    surface.blit(stopsign, (((2000 / max_width) * (zone_data[zone]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone]["coords"][1]) + 600 - radius))
                elif zone_data[zone]["zone"] == "priority":
                    surface.blit(star, (((2000 / max_width) * (zone_data[zone]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone]["coords"][1]) + 600 - radius))
                elif zone_data[zone]["zone"] == "blocked":
                    surface.blit(blocked, (((2000 / max_width) * (zone_data[zone]["coords"][0] - min_x) + radius), (600 / max_height) * (zone_data[zone]["coords"][1]) + 600 - radius))
                count = 0
                agent_count = 0
                for agent, path in solution.items():
                    agent_count += 1
                    if agent_count % 3 == 0:
                        drone = pygame.transform.scale(tum_tum, (80, 80))
                    elif agent_count % 2 == 0:
                        drone = pygame.transform.scale(bri_bri, (80, 80))
                    else:
                        drone = pygame.transform.scale(bananini, (80, 80))
                    if turn >= len(path):
                        surface.blit(drone, (((2000 / max_width) * (zone_data[path[-1]]["coords"][0] - min_x) + radius  / 2 - 24), (600 / max_height) * (zone_data[path[-1]]["coords"][1]) + 600 - radius  / 2 - 16))
                    elif zone_data[path[turn]]["zone"] == "restricted" and (agent, zone_data[path[turn]]["zone"]) not in (restricted, path[0]):
                        surface.blit(drone, (((((2000 / max_width) * (zone_data[path[turn]]["coords"][0] - min_x) + radius  / 2) + ((2000 / max_width) * (zone_data[path[turn - 1]]["coords"][0] - min_x) + radius / 2))  / 2 - 24), (((600 / max_height) * (zone_data[path[turn]]["coords"][1]) + 600 - radius  / 2) + ((600 / max_height) * (zone_data[path[turn - 1]]["coords"][1]) + 600 - radius / 2)) / 2 - 16))
                        restricted.append((agent, zone_data[path[turn]]["zone"]))
                        count += 1
                    else:
                        surface.blit(drone, (((2000 / max_width) * (zone_data[path[turn]]["coords"][0] - min_x) + radius / 2 - 24), (600 / max_height) * (zone_data[path[turn]]["coords"][1]) + 600 - radius / 2 - 16))
                        count += 1
                if count == 0 and screaming_sound:
                    tum_tum_sound.stop()
                    sound.play(1)
                    screaming_sound = False
            turn += 1

            pygame.time.delay(1000)
            pygame.display.update()
        pygame.quit()