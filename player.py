import pygame
import random

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        
        # --- 이미지 로드 ---
        self.images = {}
        try:
            # 정면 (직진/UP)
            img_straight = pygame.image.load("assets/player_straight.png").convert_alpha()
            self.images["UP"] = pygame.transform.scale(img_straight, (60, 100))
            
            # 좌회전 (LEFT)
            img_left = pygame.image.load("assets/player_left_turn.png").convert_alpha()
            self.images["LEFT"] = pygame.transform.scale(img_left, (100, 80)) 
            
            # 우회전 (RIGHT)
            img_right = pygame.image.load("assets/player_right_turn.png").convert_alpha()
            self.images["RIGHT"] = pygame.transform.scale(img_right, (100, 80))
            
            # ★★★ 추가: 후진 (DOWN) 이미지 ★★★
            img_back = pygame.image.load("assets/player_backward.png").convert_alpha()
            self.images["DOWN"] = pygame.transform.scale(img_back, (60, 100))
            
        except Exception as e:
            print(f"이미지 로드 실패: {e}")
            # 이미지가 없을 경우 색상 박스로 대체 (오류 방지)
            self.images["UP"] = pygame.Surface((50, 80))
            self.images["UP"].fill(self.game.COLORS["green"])
            self.images["LEFT"] = pygame.Surface((80, 50))
            self.images["LEFT"].fill(self.game.COLORS["blue"])
            self.images["RIGHT"] = pygame.Surface((80, 50))
            self.images["RIGHT"].fill(self.game.COLORS["yellow"])
            # DOWN fallback
            self.images["DOWN"] = pygame.Surface((50, 80))
            self.images["DOWN"].fill(self.game.COLORS["red"])

        # 기본 방향 설정
        self.current_direction = "UP"
        self.image = self.images["UP"]
        self.rect = self.image.get_rect(center=(self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT // 2 + 100))
        
        # 판정 존
        self.grading_zone = pygame.Rect(0, 0, 20, 20)
        self.grading_zone.center = self.rect.center
        
        self.is_animating = False

    def update(self):
        self.grading_zone.center = self.rect.center
        
        # 충돌(Crash) 애니메이션 (흔들림)
        if self.is_animating:
             self.rect.centerx += random.randint(-5, 5)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def turn(self, direction):
        """game.py에서 호출하는 방향 전환 함수 (애니메이션용)"""
        # direction 문자열: "좌회전", "우회전"
        if direction == "좌회전":
            self.set_direction("LEFT")
        elif direction == "우회전":
            self.set_direction("RIGHT")
        else:
            self.set_direction("UP")

    def set_direction(self, direction):
        """실제 이미지와 방향을 변경하는 함수"""
        if direction in self.images:
            self.current_direction = direction
            self.image = self.images[direction]
            # 이미지 크기가 달라질 수 있으므로 중심점 유지하며 rect 재설정
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)

    def crash(self):
        """충돌 효과"""
        self.is_animating = True 

    def reset_position(self):
        self.is_animating = False
        self.set_direction("UP")
        self.rect.center = (self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT // 2 + 100)