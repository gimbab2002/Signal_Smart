import pygame
import sys
import random
import numpy as np

from player import Player
from road import RoadSegment
from pose_detector import PoseDetector

class Game:
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GRADING = 2
    STATE_RESULT_ANIM = 4
    STATE_GAMEOVER = 3
    
    MISSIONS = ["좌회전", "우회전", "정지"] 

    def __init__(self):
        pygame.init()
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 900
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("SignalSmart 4방향 런너 (v8 - 방향전환 수정)")
        self.clock = pygame.time.Clock()
        
        self.COLORS = {
            "dark_blue": (44, 62, 80), "white": (255, 255, 255),
            "green": (46, 204, 113), "red": (231, 76, 60),
            "yellow": (241, 196, 15), "blue": (52, 152, 219),
            "road_gray": (50, 50, 60)
        }
        self.font_large = pygame.font.SysFont("malgungothic", 60, bold=True)
        self.font_medium = pygame.font.SysFont("malgungothic", 36, bold=True)
        self.font_small = pygame.font.SysFont("malgungothic", 24)

        self.pose_detector = PoseDetector() 
        print("Warming up camera...")
        self.pose_detector.start()
            
        self.player = Player(self)
        self.road_segments = pygame.sprite.Group()
        
        self.game_state = self.STATE_MENU
        self.score = 0
        self.mistakes = 0
        self.current_mission = ""
        self.result_text = ""
        self.pose_buffer = []
        self.last_state_change_time = 0
        self.active_mission_segment = None
        
        self.player_direction = "UP" 
        self.base_speed = 10
        self.world_velocity = [0, -self.base_speed] 
        self.last_spawned_segment = None 
        self.tiles_to_spawn = 0 

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if self.game_state == self.STATE_MENU and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: self.start_game()
            
            self.pose_detector.update()
            
            if self.game_state == self.STATE_PLAYING:
                self.update_playing()
            elif self.game_state == self.STATE_GRADING:
                self.update_grading()
            elif self.game_state == self.STATE_RESULT_ANIM:
                self.update_result_animation()
            elif self.game_state == self.STATE_GAMEOVER:
                self.update_gameover()
                
            self.draw()
            pygame.display.flip()
            self.clock.tick(30) 

        self.pose_detector.stop()
        pygame.quit()
        sys.exit()

    def update_playing(self):
        # 1. 속도 설정 (방향에 따라) - ★★★ 속도 방향 수정 ★★★
        # 플레이어가 오른쪽으로 가면, 배경은 왼쪽(-X)으로 가야 함
        if self.player_direction == "UP": 
            self.world_velocity = [0, -self.base_speed]
        elif self.player_direction == "DOWN": 
            self.world_velocity = [0, self.base_speed]
        elif self.player_direction == "LEFT": 
            self.world_velocity = [-self.base_speed, 0] # 배경은 오른쪽(+X)으로 이동 (X -= -10 => X += 10)
        elif self.player_direction == "RIGHT": 
            self.world_velocity = [self.base_speed, 0]  # 배경은 왼쪽(-X)으로 이동 (X -= 10)

        self.road_segments.update()
        
        if self.last_spawned_segment:
            lx, ly = self.last_spawned_segment.exit_point
            margin = 100
            in_view = (-margin < lx < self.SCREEN_WIDTH + margin) and (-margin < ly < self.SCREEN_HEIGHT + margin)
            
            if in_view:
                self.spawn_next_road()
        else:
            self.spawn_next_road()

        for segment in self.road_segments:
            # ★★★ 핵심 수정: 이미 판정한 도로(segment.is_judged)는 무시 ★★★
            if segment.mission_name and not segment.is_judged:
                dist = np.linalg.norm(np.array(self.player.rect.center) - np.array(segment.rect.center))
                # 판정 거리 내에 들어오면
                if dist < 30: 
                    self.start_grading(segment)
                    break

    def spawn_next_road(self):
        if self.tiles_to_spawn > 0:
            seg_type = 'straight'
            self.tiles_to_spawn -= 1
        else:
            if random.random() < 0.4:
                seg_type = random.choice(['left_turn', 'right_turn', 'stop_signal'])
                self.tiles_to_spawn = 3 
            else:
                seg_type = 'straight'
        
        new_segment = RoadSegment(self, seg_type, self.last_spawned_segment)
        self.road_segments.add(new_segment)
        self.last_spawned_segment = new_segment

    def start_grading(self, segment):
        # ★★★ 핵심 수정: 미션 시작 시 바로 '판정됨' 처리 ★★★
        segment.is_judged = True
        
        self.game_state = self.STATE_GRADING
        self.current_mission = segment.mission_name
        self.active_mission_segment = segment
        self.pose_buffer = []
        self.result_text = ""
        self.last_state_change_time = pygame.time.get_ticks()
        self.world_velocity = [0, 0] 

    def update_grading(self):
        now = pygame.time.get_ticks()
        LAG_TIME = 1500
        GRADING_TIME = 2000
        
        start = self.last_state_change_time
        if now < start + LAG_TIME:
            self.result_text = f"미션: {self.current_mission}!"
        elif now < start + LAG_TIME + GRADING_TIME:
            current_pose = self.pose_detector.get_current_pose()
            self.pose_buffer.append(current_pose)
            self.result_text = "포즈 유지!"
        else:
            self.finish_grading()

    def finish_grading(self):
        correct = 0
        if self.pose_buffer:
            for p in self.pose_buffer:
                if p == self.current_mission: correct += 1
            acc = correct / len(self.pose_buffer)
        else: acc = 0
        
        if acc >= 0.4: 
            self.result_text = "SUCCESS!"
            self.score += 100
        else: 
            self.result_text = "FAIL"
            self.mistakes += 1
            self.player.crash()
            
        # 핵심 수정: 실제 이동 방향 변경 로직 복구 
        if self.current_mission == "좌회전":
            if self.player_direction == "UP": self.player_direction = "LEFT"
            elif self.player_direction == "LEFT": self.player_direction = "DOWN"
            elif self.player_direction == "DOWN": self.player_direction = "RIGHT"
            elif self.player_direction == "RIGHT": self.player_direction = "UP"
            
        elif self.current_mission == "우회전":
            if self.player_direction == "UP": self.player_direction = "RIGHT"
            elif self.player_direction == "RIGHT": self.player_direction = "DOWN"
            elif self.player_direction == "DOWN": self.player_direction = "LEFT"
            elif self.player_direction == "LEFT": self.player_direction = "UP"
        
        self.player.set_direction(self.player_direction)
        
        self.active_mission_segment = None
        self.game_state = self.STATE_RESULT_ANIM
        self.last_state_change_time = pygame.time.get_ticks()

    def update_result_animation(self):
        if pygame.time.get_ticks() > self.last_state_change_time + 1000:
            if self.mistakes >= 3:
                self.game_over()
            else:
                self.game_state = self.STATE_PLAYING
                self.result_text = ""

    def update_gameover(self):
        self.world_velocity = [0, 0]
        now = pygame.time.get_ticks()
        if now > self.last_state_change_time + 3000:
            self.game_state = self.STATE_MENU

    def draw(self):
        self.screen.fill(self.COLORS["road_gray"]) 
        if self.game_state == self.STATE_MENU:
            self.draw_menu()
        else:
            self.draw_game()

    def draw_menu(self):
        self.screen.fill(self.COLORS["dark_blue"]) 
        self.draw_text("SignalSmart 4-Way", self.font_large, self.COLORS["white"], self.SCREEN_WIDTH // 2, 250)
        self.draw_text("Press ENTER", self.font_medium, self.COLORS["yellow"], self.SCREEN_WIDTH // 2, 450)
        self.draw_webcam_minimap()

    def draw_game(self):
        self.road_segments.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_text(f"점수: {self.score}", self.font_medium, self.COLORS["white"], 100, 30, "topleft")
        self.draw_text(f"실수: {self.mistakes}/3", self.font_medium, self.COLORS["white"], self.SCREEN_WIDTH-150, 30, "topleft")
        
        if self.game_state == self.STATE_GRADING or self.game_state == self.STATE_RESULT_ANIM:
             self.draw_text(self.result_text, self.font_large, self.COLORS["yellow"], self.SCREEN_WIDTH//2, 150)

        if self.game_state == self.STATE_GAMEOVER:
            self.draw_text("GAME OVER", self.font_large, self.COLORS["red"], self.SCREEN_WIDTH//2, 300)

        self.draw_webcam_minimap()

    def draw_webcam_minimap(self):
        frame = self.pose_detector.get_minimap_frame()
        if frame is not None:
            try:
                surf = pygame.surfarray.make_surface(frame.swapaxes(0,1))
                surf = pygame.transform.scale(surf, (200, 150))
                self.screen.blit(surf, (self.SCREEN_WIDTH-210, self.SCREEN_HEIGHT-160))
            except: pass

    def draw_text(self, text, font, color, x, y, align="center"):
        s = font.render(text, True, color)
        r = s.get_rect()
        if align == "center": r.center = (x, y)
        elif align == "topleft": r.topleft = (x, y)
        elif align == "topright": r.topright = (x, y)
        self.screen.blit(s, r)

    def start_game(self):
        if self.pose_detector.cap is None: self.pose_detector.start()
        
        # ★★★ 핵심 수정: 게임 변수 완벽 초기화 ★★★
        self.score = 0
        self.mistakes = 0
        self.road_segments.empty()
        self.player.reset_position()
        
        self.player_direction = "UP" # 방향도 초기화
        self.world_velocity = [0, -self.base_speed] # 속도 벡터 초기화
        self.player.set_direction("UP") # 이미지 회전 초기화
        
        self.last_spawned_segment = None
        self.active_mission_segment = None # 활성 미션 초기화
        
        # 초기 도로 생성
        start_seg = RoadSegment(self, 'straight')
        start_seg.rect.center = self.player.rect.center
        self.road_segments.add(start_seg)
        self.last_spawned_segment = start_seg
        
        for _ in range(5): self.spawn_next_road()
        
        self.game_state = self.STATE_PLAYING

    def game_over(self):
        self.game_state = self.STATE_GAMEOVER
        self.last_state_change_time = pygame.time.get_ticks()