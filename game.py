import pygame
import sys
import random
import numpy as np

from player import Player
from road import RoadSegment
from pose_detector import PoseDetector
from background import Background

class Game:
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GRADING = 2
    STATE_RESULT_ANIM = 4
    STATE_GAMEOVER = 3
    
    MISSIONS = ["좌회전", "우회전", "정지"] 

    def __init__(self):
        pygame.init()
        
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.screen.get_size()

        pygame.display.set_caption("SignalSmart 4방향 런너 (Full Screen)")
        
        self.clock = pygame.time.Clock()

        # 배경 이미지 로딩
        self.bg_main = pygame.image.load("assets/ui/main_bg.png").convert()
        self.bg_main = pygame.transform.scale(self.bg_main, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # 타이틀 이미지(투명 PNG)
        self.title_banner = pygame.image.load("assets/ui/title_banner.png").convert_alpha()

        # 타이틀 이미지 위치 설정
        self.title_banner_rect = self.title_banner.get_rect(center=(self.SCREEN_WIDTH // 2, 200))

        # 게임 시작 버튼 이미지 로딩
        self.btn_start = pygame.image.load("assets/ui/btn_start.png").convert_alpha()

        # 시작 버튼 위치 설정
        self.btn_start_rect = self.btn_start.get_rect(center=(self.SCREEN_WIDTH // 2, 540))

        # 랭킹 버튼 이미지 로딩
        self.btn_ranking = pygame.image.load("assets/ui/btn_ranking.png").convert_alpha()

        self.btn_ranking_rect = self.btn_ranking.get_rect(center=(self.SCREEN_WIDTH // 2, 680)) 
        
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
        
        self.background = Background(self)
        
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
        self.base_speed = 15 
        self.world_velocity = [0, -self.base_speed] 
        self.last_spawned_segment = None 
        self.tiles_to_spawn = 0 

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # ESC 종료
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # --- 메뉴 상태에서 버튼 클릭 감지
                if self.game_state == self.STATE_MENU:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()

            # 버튼 클릭 여부 체크
                        if self.btn_start_rect.collidepoint(mouse_pos):
                            self.start_game()

                        elif self.btn_ranking_rect.collidepoint(mouse_pos):
                            self.open_ranking()
            
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
        if self.player_direction == "UP": 
            self.world_velocity = [0, -self.base_speed]
        elif self.player_direction == "DOWN": 
            self.world_velocity = [0, self.base_speed]
        elif self.player_direction == "LEFT": 
            self.world_velocity = [-self.base_speed, 0]
        elif self.player_direction == "RIGHT": 
            self.world_velocity = [self.base_speed, 0]

        self.background.update()
        
        self.road_segments.update()
        
        if self.last_spawned_segment:
            lx, ly = self.last_spawned_segment.exit_point
            margin = 200
            in_view = (-margin < lx < self.SCREEN_WIDTH + margin) and (-margin < ly < self.SCREEN_HEIGHT + margin)
            if in_view:
                self.spawn_next_road()
        else:
            self.spawn_next_road()

        for segment in self.road_segments:
            if segment.mission_name and not segment.is_judged:
                dist = np.linalg.norm(np.array(self.player.rect.center) - np.array(segment.rect.center))
                if dist < 50: 
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
        
        # 1. 점수 및 결과 처리
        if acc >= 0.4: 
            self.result_text = "SUCCESS!"
            self.score += 100
        else: 
            self.result_text = "FAIL"
            self.mistakes += 1
            self.player.crash()
            
        # 2. ★★★ 방향 전환 (성공/실패 여부와 상관없이 무조건 실행) ★★★
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
        self.background.draw(self.screen)
        
        if self.game_state == self.STATE_MENU:
            self.draw_menu()
        else:
            self.draw_game()

    def draw_menu(self):
        self.screen.blit(self.bg_main, (0, 0))
    # TITLE 버튼 
        self.screen.blit(self.title_banner, self.title_banner_rect)
    # START 버튼 
        self.screen.blit(self.btn_start, self.btn_start_rect)
    # RANKING 버튼
        self.screen.blit(self.btn_ranking, self.btn_ranking_rect)

    def open_ranking(self):
        print(">>> RANKING PAGE OPENED (미구현)")
            # TODO : 추후 랭킹 UI 구현

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
        
        self.score = 0
        self.mistakes = 0
        self.road_segments.empty()
        self.player.reset_position()
        
        self.player_direction = "UP" 
        self.world_velocity = [0, -self.base_speed] 
        self.player.set_direction("UP") 
        
        self.last_spawned_segment = None
        self.active_mission_segment = None
        
        start_seg = RoadSegment(self, 'straight')
        start_seg.rect.center = self.player.rect.center
        self.road_segments.add(start_seg)
        self.last_spawned_segment = start_seg
        
        for _ in range(8): self.spawn_next_road()
        
        self.game_state = self.STATE_PLAYING

    def game_over(self):
        self.game_state = self.STATE_GAMEOVER
        self.last_state_change_time = pygame.time.get_ticks()