import pygame

class RoadSegment(pygame.sprite.Sprite):
    TILE_SIZE = 400 

    def __init__(self, game, segment_type, prev_segment=None):
        super().__init__()
        self.game = game
        self.type = segment_type
        
        # 핵심 수정: 중복 판정 방지용 꼬리표
        self.is_judged = False 

        if prev_segment:
            self.in_direction = prev_segment.out_direction
            start_pos = prev_segment.exit_point
        else:
            self.in_direction = "UP"
            start_pos = (self.game.SCREEN_WIDTH // 2, self.game.SCREEN_HEIGHT + self.TILE_SIZE)

        # 1. 방향 결정
        self.out_direction = self.in_direction
        if self.type == 'left_turn':
            if self.in_direction == "UP": self.out_direction = "LEFT"
            elif self.in_direction == "LEFT": self.out_direction = "DOWN"
            elif self.in_direction == "DOWN": self.out_direction = "RIGHT"
            elif self.in_direction == "RIGHT": self.out_direction = "UP"
            self.mission_name = "좌회전"
        elif self.type == 'right_turn':
            if self.in_direction == "UP": self.out_direction = "RIGHT"
            elif self.in_direction == "RIGHT": self.out_direction = "DOWN"
            elif self.in_direction == "DOWN": self.out_direction = "LEFT"
            elif self.in_direction == "LEFT": self.out_direction = "UP"
            self.mission_name = "우회전"
        elif self.type == 'stop_signal':
            self.mission_name = "정지"
        else:
            self.mission_name = None

        # 2. 이미지 로드
        self.image = self.load_and_rotate_image()
        self.rect = self.image.get_rect()
        
        # 3. 위치 잡기
        if self.in_direction == "UP": self.rect.midbottom = start_pos
        elif self.in_direction == "DOWN": self.rect.midtop = start_pos
        elif self.in_direction == "LEFT": self.rect.midright = start_pos
        elif self.in_direction == "RIGHT": self.rect.midleft = start_pos

        # 4. 출구 계산
        if self.out_direction == "UP": self.exit_point = self.rect.midtop
        elif self.out_direction == "DOWN": self.exit_point = self.rect.midbottom
        elif self.out_direction == "LEFT": self.exit_point = self.rect.midleft
        elif self.out_direction == "RIGHT": self.exit_point = self.rect.midright

    def load_and_rotate_image(self):
        try:
            # ★★★ 파일명 정확하게 수정 ★★★
            if self.type == 'left_turn':
                img = pygame.image.load("assets/road_corner_left1.png").convert_alpha()
            elif self.type == 'right_turn':
                img = pygame.image.load("assets/road_corner_right1.png").convert_alpha()
            else: 
                # straight와 stop_signal은 기본 직진 도로 사용
                img = pygame.image.load("assets/road_straight.png").convert_alpha()

            # 크기 조정
            img = pygame.transform.scale(img, (self.TILE_SIZE, self.TILE_SIZE))
            
            # ★★★ 정지선 그리기 ★★★
            if self.type == 'stop_signal':
                # 도로 위에 빨간색 선을 덧그림 (너비 전체, 높이 40)
                # y좌표 180은 타일의 중간쯤
                pygame.draw.rect(img, self.game.COLORS["red"], (0, 180, self.TILE_SIZE, 40))
                # 흰색 테두리로 잘 보이게
                pygame.draw.rect(img, self.game.COLORS["white"], (0, 180, self.TILE_SIZE, 40), 3)

        except Exception as e:
            print(f"도로 이미지 로드 실패: {e}")
            img = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE))
            img.fill((100, 100, 100))

        # 회전
        angle = 0
        if self.in_direction == "LEFT": angle = 90
        elif self.in_direction == "DOWN": angle = 180
        elif self.in_direction == "RIGHT": angle = -90
        
        return pygame.transform.rotate(img, angle)

    def update(self):
        self.rect.x -= self.game.world_velocity[0]
        self.rect.y -= self.game.world_velocity[1]
        self.exit_point = (self.exit_point[0] - self.game.world_velocity[0],
                           self.exit_point[1] - self.game.world_velocity[1])
        
        cx, cy = self.game.SCREEN_WIDTH//2, self.game.SCREEN_HEIGHT//2
        if abs(self.rect.centerx - cx) > 1500 or abs(self.rect.centery - cy) > 1500:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.rect)