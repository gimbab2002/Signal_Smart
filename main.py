import pygame
import sys
from game import Game

if __name__ == "__main__":
    try:
        game_instance = Game()
        game_instance.run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # 오류 발생 시 카메라 리소스 등을 안전하게 해제
        # 'hasattr'로 더 안전하게 확인
        if 'game_instance' in locals() and hasattr(game_instance, 'pose_detector') and game_instance.pose_detector:
            game_instance.pose_detector.stop()
        
        pygame.quit() 
        sys.exit()    