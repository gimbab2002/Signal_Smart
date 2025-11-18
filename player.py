import pygame
import random

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        
        # TODO: "player_bicycle.png" 같은 이미지 파일로 교체
        self.original_image = pygame.Surface((50, 80))
        self.original_image.fill(self.game.COLORS["green"]) # 캐릭터 색상
        # 예: self.original_image = pygame.image.load("assets/player.png").convert_alpha()
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT - 100))
        
        # '판정 존' - 이 영역에 도로 조각이 닿으면 미션 시작
        self.grading_zone = self.rect.copy().inflate(0, 50)
        
        # 애니메이션용 변수
        self.is_animating = False
        self.animation_target_x = 0
        self.animation_speed = 15

    def update(self):
        """성공/실패 애니메이션을 처리합니다."""
        if not self.is_animating:
            return

        # 목표 X좌표로 이동
        if self.rect.centerx < self.animation_target_x:
            self.rect.centerx += self.animation_speed
            if self.rect.centerx >= self.animation_target_x: self.is_animating = False
        elif self.rect.centerx > self.animation_target_x:
            self.rect.centerx -= self.animation_speed
            if self.rect.centerx <= self.animation_target_x: self.is_animating = False
        
        # 'crash'의 경우 (target_x가 중앙) 흔들림 효과 추가
        if self.animation_target_x == self.game.SCREEN_WIDTH // 2: 
             self.rect.centerx += random.randint(-5, 5)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def turn(self, direction):
        """성공 시 턴 애니메이션 시작"""
        if direction == "좌회전":
            self.animation_target_x = -100 # 화면 왼쪽 밖
        elif direction == "우회전":
            self.animation_target_x = self.game.SCREEN_WIDTH + 100 # 화면 오른쪽 밖
        self.is_animating = True

    def crash(self):
        """실패 시 충돌 애니메이션"""
        self.animation_target_x = self.game.SCREEN_WIDTH // 2
        self.is_animating = True 
        # TODO: "쿵!" 하는 소리 재생

    def reset_position(self):
        """캐릭터를 중앙 하단으로 리셋"""
        self.is_animating = False
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT - 100))