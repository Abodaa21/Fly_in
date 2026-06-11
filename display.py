import pygame
from parsing import DataValidator

class Visualization:
    def display(self, coords, zone_list, zone_data, connnect_list):
        size_zones = len(zone_list)
        # for x, y in coords:
            
        min_x = min(coords, key=lambda x: x[0])[0]
        max_x = max(coords, key=lambda x: x[0])[0]
        min_y = min(coords, key=lambda x: x[1])[1]
        max_y = max(coords, key=lambda x: x[1])[1]
        pygame.init()
        running = True
        # if max_x < 10:
        #     max_x = 10
        # if max_y < 10:
        #     max_y = 10
        max_width = max_x - min_x + 1
        max_height = max_y - min_y + 1
        surface = pygame.display.set_mode((2000, 1200))
        radius = int(min(2000 / max_width, 1200 / max_height, 100) / 2.5)
        stopsign = pygame.image.load("stopsign.png").convert_alpha()
        stopsign = pygame.transform.scale(stopsign, (32, 32))
        star = pygame.image.load("star.png").convert_alpha()
        star = pygame.transform.scale(star, (32, 32))
        blocked = pygame.image.load("blocked.png").convert_alpha()
        blocked = pygame.transform.scale(blocked, (32, 32))        
        while running:
            for event in pygame.event.get():
                if event == pygame.QUIT:
                    running = False
            surface.fill((0, 0, 0))
            # for zone in zone_list:
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

            # pygame.draw.circle(surface, (255, 255, 255), (900, 900), 50)
            pygame.display.update()
        pygame.quit()