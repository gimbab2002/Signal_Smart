import pygame
import random

class RoadSegment(pygame.sprite.Sprite):
    """(v3 - 갈림길 로직)"""
    def __init__(self, game, segment_type):
        super().__init__()
        self.game = game
        self.type = segment_type # 'straight', 'left_turn', 'right_turn', 'stop_signal'
        
        road_center_x = self.game.SCREEN_WIDTH // 2
        
        if self.type == 'left_turn':
            # 'T'자 갈림길 (왼쪽)
            # TODO: "junction_left.png" 같은 이미지로 교체
            self.image = pygame.Surface((self.game.SCREEN_WIDTH // 2, 80))
            self.image.fill(self.game.COLORS["yellow"])
            pygame.draw.rect(self.image, self.game.COLORS["road_gray"], (0, 40, self.game.SCREEN_WIDTH // 2, 40)) # T자 모양
            self.mission_name = "좌회전"
            self.rect = self.image.get_rect(midtop=(road_center_x // 2, -self.image.get_height()))
            
        elif self.type == 'right_turn':
            # 'T'자 갈림길 (오른쪽)
            # TODO: "junction_right.png" 같은 이미지로 교체
            self.image = pygame.Surface((self.game.SCREEN_WIDTH // 2, 80))
            self.image.fill(self.game.COLORS["blue"])
            pygame.draw.rect(self.image, self.game.COLORS["road_gray"], (self.game.SCREEN_WIDTH // 2, 40, self.game.SCREEN_WIDTH // 2, 40))
            self.mission_name = "우회전"
            self.rect = self.image.get_rect(midtop=(road_center_x + road_center_x // 2, -self.image.get_height()))

        elif self.type == 'stop_signal':
            # 정지 신호 (정지선)
            # TODO: "stop_line.png" 같은 이미지로 교체
            self.image = pygame.Surface((self.game.SCREEN_WIDTH // 2, 40)) # 횡단보도 느낌
            self.image.fill(self.game.COLORS["red"])
            self.mission_name = "정지"
            self.rect = self.image.get_rect(center=(road_center_x, -self.image.get_height()))
            
        else: # 'straight' (일반 도로 - 중앙선)
             self.image = pygame.Surface((20, 40)) # 얇은 중앙선
             self.image.fill(self.game.COLORS["white"])
             self.mission_name = None
             self.rect = self.image.get_rect(center=(road_center_x, -self.image.get_height()))

    def update(self):
        self.rect.y += self.game.current_speed
        if self.rect.top > self.game.SCREEN_HEIGHT:
            self.kill() # 스프라이트 그룹에서 스스로 제거

    def draw(self, screen):
        screen.blit(self.image, self.rect)