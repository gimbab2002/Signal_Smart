import pygame

# 방향 상수 (game.py와 통일)
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

class RoadSegment(pygame.sprite.Sprite):
    TILE_SIZE = 400 

    def __init__(self, game, segment_type, prev_segment=None):
        super().__init__()
        self.game = game
        self.type = segment_type
        self.is_judged = False 

        # --- 위치 및 방향 결정 ---
        if prev_segment:
            self.in_direction = prev_segment.out_direction
            start_pos = prev_segment.exit_point
        else:
            self.in_direction = DIR_UP
            # 첫 도로 위치
            start_pos = (self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT + 100)

        self.out_direction = self.in_direction 
        self.mission_name = None

        if self.type == 'left_turn':
            self.mission_name = "좌회전"
            if self.in_direction == DIR_UP: self.out_direction = DIR_LEFT
            elif self.in_direction == DIR_LEFT: self.out_direction = DIR_DOWN
            elif self.in_direction == DIR_DOWN: self.out_direction = DIR_RIGHT
            elif self.in_direction == DIR_RIGHT: self.out_direction = DIR_UP
            
        elif self.type == 'right_turn':
            self.mission_name = "우회전"
            if self.in_direction == DIR_UP: self.out_direction = DIR_RIGHT
            elif self.in_direction == DIR_RIGHT: self.out_direction = DIR_DOWN
            elif self.in_direction == DIR_DOWN: self.out_direction = DIR_LEFT
            elif self.in_direction == DIR_LEFT: self.out_direction = DIR_UP
            
        elif self.type == 'stop_signal':
            self.mission_name = "정지"

        # 이미지 로드
        self.image = self.load_and_rotate_image()
        self.rect = self.image.get_rect()
        
        # 위치 잡기
        if self.in_direction == DIR_UP: self.rect.midbottom = start_pos
        elif self.in_direction == DIR_DOWN: self.rect.midtop = start_pos
        elif self.in_direction == DIR_LEFT: self.rect.midright = start_pos
        elif self.in_direction == DIR_RIGHT: self.rect.midleft = start_pos

    @property
    def exit_point(self):
        if self.out_direction == DIR_UP: return self.rect.midtop
        elif self.out_direction == DIR_DOWN: return self.rect.midbottom
        elif self.out_direction == DIR_LEFT: return self.rect.midleft
        elif self.out_direction == DIR_RIGHT: return self.rect.midright
        return self.rect.center

    def load_and_rotate_image(self):
        try:
            if self.type == 'left_turn':
                img = pygame.image.load("assets/road_corner_left1.png").convert_alpha()
            elif self.type == 'right_turn':
                img = pygame.image.load("assets/road_corner_right1.png").convert_alpha()
            else: 
                img = pygame.image.load("assets/road_straight.png").convert_alpha()

            img = pygame.transform.scale(img, (self.TILE_SIZE, self.TILE_SIZE))
            
            # ★★★ 횡단보도 그리기 ★★★
            if self.type == 'stop_signal':
                # 횡단보도 그리기 설정
                stripe_width = 40 # 흰색 줄 너비
                stripe_height = 300 # 흰색 줄 높이 (세로 길이)
                gap = 30 # 줄 사이 간격
                y_pos = (self.TILE_SIZE - stripe_height) // 2 # 도로 중앙 y좌표

                # 도로 너비만큼 반복해서 그리기
                for x in range(0, self.TILE_SIZE, stripe_width + gap):
                    pygame.draw.rect(img, self.game.COLORS["white"], (x, y_pos, stripe_width, stripe_height))

        except Exception as e:
            img = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE))
            img.fill((100, 100, 100))

        angle = 0
        if self.in_direction == DIR_LEFT: angle = 90
        elif self.in_direction == DIR_DOWN: angle = 180
        elif self.in_direction == DIR_RIGHT: angle = -90
        
        return pygame.transform.rotate(img, angle)

    def update(self):
        self.rect.x -= self.game.world_velocity[0]
        self.rect.y -= self.game.world_velocity[1]
        # 삭제는 game.py의 cleanup_segments가 담당

    def draw(self, screen):
        screen.blit(self.image, self.rect)