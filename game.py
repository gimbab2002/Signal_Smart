import pygame
import sys
import random
import numpy as np

# 1. 분리된 파일들을 import
from player import Player
from road import RoadSegment
from pose_detector import PoseDetector

class Game:
    # --- 게임 상태 정의 ---
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GRADING = 2 # 미션 판정 중 (일시정지 상태)
    STATE_RESULT_ANIM = 4 # 성공/실패 애니메이션
    STATE_GAMEOVER = 3
    
    MISSIONS = ["좌회전", "우회전", "정지"] 

    def __init__(self):
        # --- PyGame 초기화 ---
        pygame.init()
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 900
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("SignalSmart 2D 런너 게임 (v3 - 분리됨)")
        self.clock = pygame.time.Clock()
        
        # --- 색상 및 폰트 ---
        self.COLORS = {
            "dark_blue": (44, 62, 80), "white": (255, 255, 255),
            "green": (46, 204, 113), "red": (231, 76, 60),
            "yellow": (241, 196, 15), "blue": (52, 152, 219),
            "road_gray": (50, 50, 60) # 도로 배경색
        }
        self.font_large = pygame.font.SysFont("malgungothic", 60, bold=True)
        self.font_medium = pygame.font.SysFont("malgungothic", 36, bold=True)
        self.font_small = pygame.font.SysFont("malgungothic", 24)

        # --- ★★★ 모듈 조립 ★★★ ---
        self.pose_detector = PoseDetector() # 동작 인식 모듈 생성
        # ★★★ 수정: 앱 실행 즉시 카메라를 켭니다 (워밍업) ★★★
        print("Warming up camera...")
        if not self.pose_detector.start():
            print("Warning: Camera failed to start on launch.")
        self.player = Player(self)          # 플레이어 생성
        self.road_segments = pygame.sprite.Group() # 도로 그룹 생성
        
        # --- 게임 변수 ---
        self.game_state = self.STATE_MENU
        self.score = 0
        self.mistakes = 0
        self.current_speed = 8
        self.current_mission = ""
        self.result_text = ""
        self.pose_buffer = []
        self.last_state_change_time = 0
        self.last_segment_time = 0
        self.active_mission_segment = None

    def run(self):
        """메인 게임 루프"""
        running = True
        while running:
            # --- 1. 이벤트 처리 ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.game_state == self.STATE_MENU and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.start_game()
            
            # --- 2. 업데이트 ---
            self.pose_detector.update() # ★ 매 프레임 포즈 감지 업데이트
            
            if self.game_state == self.STATE_PLAYING:
                self.update_playing()
            elif self.game_state == self.STATE_GRADING:
                self.update_grading()
            elif self.game_state == self.STATE_RESULT_ANIM:
                self.update_result_animation()
            elif self.game_state == self.STATE_GAMEOVER:
                self.update_gameover()
                
            # --- 3. 그리기 ---
            self.draw()

            # --- 4. 화면 업데이트 ---
            pygame.display.flip()
            self.clock.tick(30) # 30 FPS

        # --- 종료 ---
        self.pose_detector.stop() # 카메라 해제
        pygame.quit()
        sys.exit()

    # --- 상태별 업데이트 함수 ---

    def update_playing(self):
        """(STATE_PLAYING) 도로 조각을 생성하고 움직입니다."""
        self.current_speed = 8
        self.road_segments.update() # 모든 도로 조각 아래로 이동
        
        now = pygame.time.get_ticks()
        if now > self.last_segment_time + 2000: # 2초마다 새 조각
            self.last_segment_time = now
            if random.random() < 0.4: # 40% 확률로 미션 생성
                seg_type = random.choice(['left_turn', 'right_turn', 'stop_signal'])
            else:
                seg_type = 'straight'
            new_segment = RoadSegment(self, seg_type)
            self.road_segments.add(new_segment)
            
        for segment in self.road_segments:
            if segment.mission_name and self.player.grading_zone.colliderect(segment.rect):
                self.start_grading(segment)
                break

    def update_grading(self):
        """(STATE_GRADING) 미션 판정 중. 1초 대기 후 3초간 포즈 수집."""
        self.current_speed = 0 # 도로가 멈춤
        
        now = pygame.time.get_ticks()
        
        # ★★★ 입력 지연(Lag) 보상 로직 ★★★
        
        # 1. 1초간 '반응 시간' (아무것도 수집하지 않음)
        if now < self.last_state_change_time + 1000:
            self.result_text = f"미션: {self.current_mission}!"
        
        # 2. 1초 ~ 3초 사이 (2초간) '판정 시간'
        elif now < self.last_state_change_time + 3000: # 1000ms -> 3000ms (2초간)
            current_pose = self.pose_detector.get_current_pose()
            self.pose_buffer.append(current_pose)
            
            # (시각적 피드백) 남은 시간 표시
            remaining_time = (self.last_state_change_time + 3000 - now) // 1000
            self.result_text = f"포즈 유지! ({remaining_time + 1})"
        
        # 3. 3초 경과
        else:
            self.finish_grading() # 판정 종료

    def update_result_animation(self):
        """(STATE_RESULT_ANIM) 성공/실패 애니메이션 재생"""
        self.current_speed = 0 # 멈춘 상태 유지
        self.player.update() # 플레이어 애니메이션(이동/흔들림) 실행
        
        if not self.player.is_animating:
            self.player.reset_position() 
            if self.mistakes >= 3:
                self.game_over()
            else:
                self.game_state = self.STATE_PLAYING
                self.result_text = ""

    def update_gameover(self):
        self.current_speed = 0
        now = pygame.time.get_ticks()
        if now > self.last_state_change_time + 3000:
            self.game_state = self.STATE_MENU

    # --- 그리기(Draw) 함수 ---
    def draw(self):
        self.screen.fill(self.COLORS["road_gray"]) 
        if self.game_state == self.STATE_MENU:
            self.draw_menu()
        else:
            self.draw_game()

    def draw_menu(self):
        self.screen.fill(self.COLORS["dark_blue"]) 
        self.draw_text("SignalSmart 2D", self.font_large, self.COLORS["white"], self.SCREEN_WIDTH // 2, 250)
        self.draw_text("자전거 수신호 게임 (v3)", self.font_large, self.COLORS["white"], self.SCREEN_WIDTH // 2, 320)
        self.draw_text("Press ENTER to Start", self.font_medium, self.COLORS["yellow"], self.SCREEN_WIDTH // 2, 450)

    def draw_game(self):
        self.road_segments.draw(self.screen)
        self.player.draw(self.screen)
        
        self.draw_text(f"점수: {self.score}", self.font_medium, self.COLORS["white"], 100, 30, "topleft")
        self.draw_text(f"실수: {self.mistakes} / 3", self.font_medium, self.COLORS["white"], self.SCREEN_WIDTH - 100, 30, "topright")
        
        if self.game_state == self.STATE_GRADING:
            self.draw_text(f"미션: {self.current_mission}!", self.font_large, self.COLORS["yellow"], self.SCREEN_WIDTH // 2, 100)
            self.draw_text(self.result_text, self.font_medium, self.COLORS["white"], self.SCREEN_WIDTH // 2, 160)
        elif self.game_state == self.STATE_RESULT_ANIM:
             color = self.COLORS["green"] if self.result_text != "BAD" else self.COLORS["red"]
             self.draw_text(self.result_text, self.font_large, color, self.SCREEN_WIDTH // 2, 100)
        elif self.game_state == self.STATE_GAMEOVER:
            self.draw_text("GAME OVER", self.font_large, self.COLORS["red"], self.SCREEN_WIDTH // 2, 300)
            self.draw_text(f"최종 점수: {self.score}", self.font_medium, self.COLORS["white"], self.SCREEN_WIDTH // 2, 380)

        self.draw_webcam_minimap()

    def draw_webcam_minimap(self):
        """pose_detector로부터 프레임을 가져와 미니맵을 그립니다."""
        frame_rgb = self.pose_detector.get_minimap_frame()
        if frame_rgb is None: 
            self.draw_text("CAM ERROR", self.font_small, self.COLORS["red"], 
                           self.SCREEN_WIDTH - 110, self.SCREEN_HEIGHT - 85)
            pygame.draw.rect(self.screen, self.COLORS["red"], 
                             (self.SCREEN_WIDTH - 210, self.SCREEN_HEIGHT - 160, 200, 150), 2)
            return
        
        try:
            # np.rot90(frame_rgb)는 이미지를 90도 회전시켜 거울 모드를 엉망으로 만듭니다.
            # (높이, 너비) 배열을 (너비, 높이) 배열로 바꾸려면 .swapaxes(0, 1)를 사용해야 합니다.
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            minimap_size = (200, 150)
            frame_surface = pygame.transform.scale(frame_surface, minimap_size)
            minimap_pos = (self.SCREEN_WIDTH - minimap_size[0] - 10, self.SCREEN_HEIGHT - minimap_size[1] - 10)
            self.screen.blit(frame_surface, minimap_pos)
            pygame.draw.rect(self.screen, self.COLORS["white"], (*minimap_pos, *minimap_size), 2)
        except Exception as e:
            print(f"Error drawing minimap: {e}")

    def draw_text(self, text, font, color, x, y, align="center"):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center": text_rect.center = (x, y)
        elif align == "topleft": text_rect.topleft = (x, y)
        elif align == "topright": text_rect.topright = (x, y)
        self.screen.blit(text_surface, text_rect)

    # --- 게임 로직 함수 ---
    def start_game(self):
        if not self.pose_detector.start():
            # 카메라 시작 실패 시
            self.game_state = self.STATE_GAMEOVER
            self.result_text = "카메라 연결 실패!"
            self.last_state_change_time = pygame.time.get_ticks()
            return
        self.score = 0
        self.mistakes = 0
        self.road_segments.empty()
        self.result_text = ""
        self.player.reset_position()
        self.game_state = self.STATE_PLAYING
        self.last_segment_time = pygame.time.get_ticks()

    def start_grading(self, segment):
        self.game_state = self.STATE_GRADING
        self.current_mission = segment.mission_name
        self.active_mission_segment = segment
        self.pose_buffer = []
        self.result_text = ""
        self.last_state_change_time = pygame.time.get_ticks()

    def finish_grading(self):
        correct_poses = 0
        if len(self.pose_buffer) > 0:
            for pose in self.pose_buffer:
                if pose == self.current_mission:
                    correct_poses += 1
            accuracy = correct_poses / len(self.pose_buffer)
        else:
            accuracy = 0

        if accuracy >= 0.4: # 40% 이상이면 성공
            if accuracy >= 0.9: self.result_text = "PERFECT!"
            elif accuracy >= 0.7: self.result_text = "GREAT"
            else: self.result_text = "GOOD"
            self.score += 70
            
            if self.current_mission == "정지":
                self.player.crash() # (임시) 제자리 흔들림 효과
            else:
                self.player.turn(self.current_mission) # 좌/우회전
        else: 
            self.result_text = "BAD"
            self.mistakes += 1
            self.player.crash()
            
        self.road_segments.remove(self.active_mission_segment)
        self.active_mission_segment = None
        self.game_state = self.STATE_RESULT_ANIM
        self.last_state_change_time = pygame.time.get_ticks()

    def game_over(self):
        print("Game Over")
        self.game_state = self.STATE_GAMEOVER
        self.result_text = f"최종 점수: {self.score}"
        self.last_state_change_time = pygame.time.get_ticks()