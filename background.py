import pygame

class Background:
    def __init__(self, game):
        self.game = game
        try:
            # 업로드하신 이미지 로드
            self.image = pygame.image.load("assets/background_grass.png").convert()
        except:
            # 이미지가 없으면 기본 초록색으로 대체
            self.image = pygame.Surface((200, 200))
            self.image.fill((100, 200, 100))
            # 격자 무늬 추가 (임시)
            pygame.draw.rect(self.image, (80, 180, 80), (0, 0, 200, 200), 1)
            
        self.w = self.image.get_width()
        self.h = self.image.get_height()
        
        self.x_shift = 0
        self.y_shift = 0

    def update(self):
        # 게임 속도(world_velocity)의 반대 방향으로 배경을 이동시킵니다.
        self.x_shift -= self.game.world_velocity[0]
        self.y_shift -= self.game.world_velocity[1]
        
        # 무한 스크롤을 위해 좌표가 이미지 크기를 넘어가면 0으로 리셋 (나머지 연산)
        self.x_shift %= self.w
        self.y_shift %= self.h

    def draw(self, screen):
        # 화면 전체를 덮을 때까지 타일을 반복해서 그립니다.
        
        # 필요한 타일 개수 계산 (화면 크기보다 넉넉하게)
        cols = (self.game.SCREEN_WIDTH // self.w) + 2
        rows = (self.game.SCREEN_HEIGHT // self.h) + 2
        
        # 그리기 시작 위치 (화면 왼쪽/위쪽 바깥에서 시작해야 끊기지 않음)
        # x_shift, y_shift는 0~w, 0~h 사이의 값이므로, 여기서 w, h를 빼서 시작점을 잡습니다.
        start_x = self.x_shift - self.w
        start_y = self.y_shift - self.h
        
        for c in range(cols):
            for r in range(rows):
                draw_x = start_x + c * self.w
                draw_y = start_y + r * self.h
                screen.blit(self.image, (draw_x, draw_y))