import pygame
import sys
import random
import numpy as np

from player import Player
# road.py에서 방향 상수 import
from road import RoadSegment, DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT 
from pose_detector import PoseDetector
from background import Background

class Game:
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GRADING = 2
    STATE_RESULT_ANIM = 4
    STATE_GAMEOVER = 3
    STATE_HELP = 5
    STATE_RANKING = 6
    
    MISSIONS = ["좌회전", "우회전", "정지"] 

    def __init__(self):
        pygame.init()
        info = pygame.display.Info()     
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.screen.get_size()

        
        pygame.display.set_caption("SignalSmart Final Count (v21)")
        self.clock = pygame.time.Clock()

        # 배경 이미지 로딩
        original_image = pygame.image.load("assets/ui/main_bg.png").convert()
        self.bg_main = pygame.transform.scale(original_image, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

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
        # 랭킹 버튼 위치 설정
        self.btn_ranking_rect = self.btn_ranking.get_rect(center=(self.SCREEN_WIDTH // 1.5, 680)) 

        # 랭킹 배경 이미지 로딩
        self.ranking_bg = pygame.image.load("assets/ui/ranking_bg.png").convert_alpha()
        # 랭킹 배경 확장
        self.ranking_bg = pygame.transform.scale(self.ranking_bg, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        
        # 랭킹 목록 이미지 로딩
        self.ranking_table = pygame.image.load("assets/ui/ranking_table.png").convert_alpha()
        # 화면 너비의 70% 크기로 스케일
        new_width = int(self.SCREEN_WIDTH * 0.76)

        # 테이블 원본 비율 유지
        orig_w, orig_h = self.ranking_table.get_size()
        new_height = int(orig_h * (new_width / orig_w))

        self.ranking_table = pygame.transform.scale(self.ranking_table, (new_width, new_height))

        self.ranking_table_rect = self.ranking_table.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT * 0.42))

        # 수신호 교육 버튼 이미지 로딩
        self.btn_tutorial = pygame.image.load("assets/ui/btn_tutorial.png").convert_alpha()
        # 수신호 교육 버튼 위치 설정
        self.btn_tutorial_rect = self.btn_tutorial.get_rect(center=(self.SCREEN_WIDTH // 3.14, 680))

        # 수신호 팝업 이미지 로딩
        self.help_img = pygame.image.load("assets/ui/help_popup.png").convert_alpha()
        self.help_img_rect = self.help_img.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        
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
        self.pose_detector.start()
        
        self.background = Background(self)
        self.player = Player(self)
        self.road_segments = pygame.sprite.Group()
        
        # ★★★ 추가: 생성된 도로 순서 관리용 리스트 ★★★
        self.generated_roads = []
        
        # --- 큐 변수 ---
        self.map_queue = [] 
        self.logical_direction = DIR_UP 
        
        self.game_state = self.STATE_MENU
        self.score = 0
        self.mistakes = 0
        self.current_mission = ""
        self.result_text = ""
        self.pose_buffer = []
        self.last_state_change_time = 0
        self.active_mission_segment = None
        self.player_direction = DIR_UP 
        self.base_speed = 15 
        self.world_velocity = [0, -self.base_speed] 
        self.last_spawned_segment = None 

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

                # HELP 팝업 상태 처리
                if self.game_state == self.STATE_HELP:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.game_state = self.STATE_MENU
                    continue



            # --- 메뉴 상태에서 버튼 클릭 감지
                if self.game_state == self.STATE_MENU:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()

                        # START 버튼 클릭
                        if self.btn_start_rect.collidepoint(mouse_pos):
                            self.start_game()

                        # RANKING 버튼 클릭
                        elif self.btn_ranking_rect.collidepoint(mouse_pos):
                            self.game_state = self.STATE_RANKING

                        # TUTORIAL 버튼 클릭
                        elif self.btn_tutorial_rect.collidepoint(mouse_pos):
                            self.game_state = self.STATE_HELP
            
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

    def fill_map_queue(self):
        while len(self.map_queue) < 20:
            count = random.randint(3, 6) 
            for _ in range(count):
                self.map_queue.append('straight')
            
            mission = random.choice(['left_turn', 'right_turn', 'stop_signal'])
            self.map_queue.append(mission)
            
            if mission == 'left_turn':
                if self.logical_direction == DIR_UP: self.logical_direction = DIR_LEFT
                elif self.logical_direction == DIR_LEFT: self.logical_direction = DIR_DOWN
                elif self.logical_direction == DIR_DOWN: self.logical_direction = DIR_RIGHT
                elif self.logical_direction == DIR_RIGHT: self.logical_direction = DIR_UP
            elif mission == 'right_turn':
                if self.logical_direction == DIR_UP: self.logical_direction = DIR_RIGHT
                elif self.logical_direction == DIR_RIGHT: self.logical_direction = DIR_DOWN
                elif self.logical_direction == DIR_DOWN: self.logical_direction = DIR_LEFT
                elif self.logical_direction == DIR_LEFT: self.logical_direction = DIR_UP

    def spawn_from_queue(self):
        if not self.map_queue: return

        segment_type = self.map_queue.pop(0)
        new_segment = RoadSegment(self, segment_type, self.last_spawned_segment)
        
        self.road_segments.add(new_segment)
        # ★★★ 리스트에도 추가 (순서 관리용) ★★★
        self.generated_roads.append(new_segment)
        
        self.last_spawned_segment = new_segment

    def cleanup_segments(self):
        """★ 수정됨: 리스트 개수 기반으로 정확하게 삭제 ★"""
        # 도로가 20개를 넘으면 가장 오래된 것(리스트의 0번째)을 삭제
        while len(self.generated_roads) > 20:
            old_segment = self.generated_roads.pop(0) # 리스트에서 제거
            old_segment.kill() # 스프라이트 그룹에서 제거 (화면에서 사라짐)

    def update_playing(self):
        if self.player_direction == DIR_UP: self.world_velocity = [0, -self.base_speed]
        elif self.player_direction == DIR_DOWN: self.world_velocity = [0, self.base_speed]
        elif self.player_direction == DIR_LEFT: self.world_velocity = [-self.base_speed, 0]
        elif self.player_direction == DIR_RIGHT: self.world_velocity = [self.base_speed, 0]
        
        self.fill_map_queue()
        
        # ★★★ 생성 조건: 선두 거리 체크 (앞이 비면 채움) ★★★
        if self.last_spawned_segment:
            player_pos = np.array(self.player.rect.center)
            # 안전하게 반복 생성
            while True:
                exit_pos = np.array(self.last_spawned_segment.exit_point)
                dist_to_head = np.linalg.norm(exit_pos - player_pos)
                
                # 화면 밖(2000px)까지 도로가 꽉 차있지 않으면 계속 생성
                if dist_to_head < 2000:
                    self.spawn_from_queue()
                else:
                    break
        else:
            self.spawn_from_queue()
            
        # ★★★ 삭제 조건: 개수 체크 (뒤를 자름) ★★★
        self.cleanup_segments()

        self.background.update()
        self.road_segments.update()
        
        for segment in self.road_segments:
            if segment.mission_name and not segment.is_judged:
                dist = np.linalg.norm(np.array(self.player.rect.center) - np.array(segment.rect.center))
                
                threshold = 50 # 기본 거리 (좌/우회전은 가까이서)
                
                if segment.mission_name == "정지":
                    threshold = 250 # 정지는 150px 앞에서 미리 멈춤
                
                if dist < threshold: 
                    self.start_grading(segment)
                    break

    # ... (start_grading, update_grading 등은 기존 유지) ...
    
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
        
        if acc >= 0.4: 
            self.result_text = "SUCCESS!"
            self.score += 100
            
            if self.current_mission == "좌회전":
                if self.player_direction == DIR_UP: self.player_direction = DIR_LEFT
                elif self.player_direction == DIR_LEFT: self.player_direction = DIR_DOWN
                elif self.player_direction == DIR_DOWN: self.player_direction = DIR_RIGHT
                elif self.player_direction == DIR_RIGHT: self.player_direction = DIR_UP
            elif self.current_mission == "우회전":
                if self.player_direction == DIR_UP: self.player_direction = DIR_RIGHT
                elif self.player_direction == DIR_RIGHT: self.player_direction = DIR_DOWN
                elif self.player_direction == DIR_DOWN: self.player_direction = DIR_LEFT
                elif self.player_direction == DIR_LEFT: self.player_direction = DIR_UP
            
            dir_str = "UP"
            if self.player_direction == DIR_LEFT: dir_str = "LEFT"
            elif self.player_direction == DIR_RIGHT: dir_str = "RIGHT"
            elif self.player_direction == DIR_DOWN: dir_str = "DOWN"
            self.player.set_direction(dir_str)
            
        else: 
            self.result_text = "FAIL"
            self.mistakes += 1
            self.player.crash()
            
            # 실패 시에도 방향 전환
            if self.current_mission == "좌회전":
                if self.player_direction == DIR_UP: self.player_direction = DIR_LEFT
                elif self.player_direction == DIR_LEFT: self.player_direction = DIR_DOWN
                elif self.player_direction == DIR_DOWN: self.player_direction = DIR_RIGHT
                elif self.player_direction == DIR_RIGHT: self.player_direction = DIR_UP
            elif self.current_mission == "우회전":
                if self.player_direction == DIR_UP: self.player_direction = DIR_RIGHT
                elif self.player_direction == DIR_RIGHT: self.player_direction = DIR_DOWN
                elif self.player_direction == DIR_DOWN: self.player_direction = DIR_LEFT
                elif self.player_direction == DIR_LEFT: self.player_direction = DIR_UP
            
            dir_str = "UP"
            if self.player_direction == DIR_LEFT: dir_str = "LEFT"
            elif self.player_direction == DIR_RIGHT: dir_str = "RIGHT"
            elif self.player_direction == DIR_DOWN: dir_str = "DOWN"
            self.player.set_direction(dir_str)
        
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
        elif self.game_state == self.STATE_HELP:
            self.draw_help_popup()
        elif self.game_state == self.STATE_RANKING:
            self.draw_ranking()
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
    # TUTORIAL 버튼
        self.screen.blit(self.btn_tutorial, self.btn_tutorial_rect)

    def draw_help_popup(self):
        self.screen.blit(self.bg_main, (0, 0))
        
        # 도움말 이미지 표시
        self.screen.blit(self.help_img, self.help_img_rect)

    def draw_ranking(self):
        # 배경
        self.screen.blit(self.ranking_bg, (0,0))
        # 랭킹 목록
        self.screen.blit(self.ranking_table, self.ranking_table_rect)

        # 임시, 나중에 가져와야함
        sample_ranking = {
            ("1위", "홍길동", "987"),
            ("2위", "전우치", "876"),
            ("3위", "임꺽정", "765"),
            ("4위", "장길산", "654"),
            ("5위", "일지매", "543"),
        }

        n = len(sample_ranking)

        table_left  = self.ranking_table_rect.left
        table_right = self.ranking_table_rect.right
        table_top   = self.ranking_table_rect.top
        table_width = self.ranking_table_rect.width
        table_height = self.ranking_table_rect.height

        for idx, (rank, name, score) in enumerate(sample_ranking):
            # 세로 위치 비율 (균등 배치)
            t = (idx + 1) / (n + 1)
            y = table_top + table_height * t

            # 가로 위치 비율 (여기서 핵심!)
            x_rank  = table_left + table_width * 0.09   # rank는 왼쪽 9% 지점
            x_name  = table_left + table_width * 0.35   # name은 왼쪽 35%
            x_score = table_left + table_width * 0.50   # score는 중앙 50%

            # 텍스트 출력
            self.draw_text(rank,  self.font_medium, self.COLORS["dark_blue"], x_rank,  y, "center")
            self.draw_text(name,  self.font_medium, self.COLORS["dark_blue"], x_name,  y, "center")
            self.draw_text(str(score), self.font_medium, self.COLORS["dark_blue"], x_score, y, "center")

        # 내 점수 표시
        my_score_text = f"내 점수: {self.score}"
        self.draw_text(
            my_score_text,
            self.font_large,
            self.COLORS["white"],
            self.SCREEN_WIDTH // 2,
            self.SCREEN_HEIGHT - 200   # 주황색 바 중앙쯤이 되도록 조절
        )

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
        self.generated_roads = [] # ★ 리스트도 초기화
        self.player.reset_position()
        
        self.player_direction = DIR_UP 
        self.world_velocity = [0, -self.base_speed] 
        self.player.set_direction("UP") 
        
        self.active_mission_segment = None
        self.pose_buffer = []
        
        # 큐 초기화
        self.map_queue = []
        self.logical_direction = DIR_UP
        
        self.last_spawned_segment = None
        
        # 초기 도로 생성 (직진)
        start_seg = RoadSegment(self, 'straight')
        start_seg.rect.center = self.player.rect.center
        
        self.road_segments.add(start_seg)
        self.generated_roads.append(start_seg) # ★ 리스트에 추가
        self.last_spawned_segment = start_seg
        
        # 초기 화면 채우기 (거리 기반 함수 사용)
        # 여기서 update_playing을 한번 돌려주거나 루프를 돔
        # 안전하게 15개 채우기
        self.fill_map_queue()
        for _ in range(15):
            self.spawn_from_queue()
        
        self.game_state = self.STATE_PLAYING

    def game_over(self):
        self.game_state = self.STATE_GAMEOVER
        self.last_state_change_time = pygame.time.get_ticks()