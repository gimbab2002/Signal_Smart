import cv2
import mediapipe as mp
import numpy as np

# --- 1. 관절 각도 계산 함수 (이 파일로 이동) ---
def calculate_angle(a, b, c):
    """세 점 a, b, c 사이의 각도를 계산합니다. (b가 중심점)"""
    a = np.array(a) # 첫 번째 점 (예: 어깨)
    b = np.array(b) # 중심점 (예: 팔꿈치)
    c = np.array(c) # 세 번째 점 (예: 손목)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

class PoseDetector:
    """MediaPipe와 OpenCV를 관리하고 포즈를 판정하는 클래스"""
    def __init__(self):
        # --- MediaPipe & OpenCV 초기화 ---
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils
        
        # ★★★ 수정: __init__에서는 카메라를 켜지 않습니다. ★★★
        self.cap = None 
        # try:
        #     self.cap = cv2.VideoCapture(0)
        # ... (이하 7줄 삭제)

        # --- 현재 상태 저장 변수 ---
        self.current_pose_name = "대기중"
        self.latest_frame_rgb = None # 미니맵용
        self.latest_landmarks = None # 아바타 그리기용 (v3에서는 사용 안함)

    # ★★★ 추가: 카메라를 시작하는 함수 ★★★
    def start(self):
        """게임 시작 시 카메라를 켭니다."""
        if self.cap is None:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    print("Error: Camera 0 could not be opened.")
                    self.cap = None
                    return False
                print("Camera started successfully.")
                return True
            except Exception as e:
                print(f"Error initializing camera: {e}")
                self.cap = None
                return False
        return True # 이미 켜져 있으면 True 반환

    def update(self):
        """매 프레임 호출되어야 하는 함수. 포즈를 감지하고 상태를 업데이트합니다."""
        if not self.cap:
            self.current_pose_name = "카메라 없음"
            return

        success, frame = self.cap.read()
        if not success:
            self.current_pose_name = "프레임 없음"
            return

        # 1. OpenCV 프레임 처리 (거울 모드)
        frame = cv2.flip(frame, 1) 
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 2. 미니맵용 프레임 저장 (game.py가 가져갈 데이터)
        self.latest_frame_rgb = frame_rgb 
        
        # 3. MediaPipe 포즈 감지
        results = self.pose.process(frame_rgb)

        # 4. 포즈 판정 로직
        self.current_pose_name = "대기중" # 기본 상태
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            try:
                # --- ★★★ 사용자님의 포즈 판정 로직 (그대로 복사) ★★★ ---
                shoulder_R = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow_R = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist_R = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                hip_R = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                right_elbow_angle = calculate_angle(shoulder_R, elbow_R, wrist_R)
                right_arm_angle = calculate_angle(elbow_R, shoulder_R, hip_R)
                shoulder_wrist_y_diff = abs(shoulder_R[1] - wrist_R[1])
                shoulder_elbow_y_diff = abs(shoulder_R[1] - elbow_R[1])
                is_left_turn_gesture = (right_elbow_angle > 150) and (shoulder_wrist_y_diff < 0.15)  and (wrist_R[0] < shoulder_R[0]) and ( 75 < right_arm_angle < 105)
                is_right_turn_gesture = (75 < right_elbow_angle < 105) and (wrist_R[1] < elbow_R[1]) and (shoulder_elbow_y_diff < 0.15) and (wrist_R[0] < shoulder_R[0]) and ( 75 < right_arm_angle < 105)
                is_stop_gesture = (right_elbow_angle > 165) and (wrist_R[1] > shoulder_R[1] + 0.15) and (30 < right_arm_angle < 80) and (wrist_R[0] < shoulder_R[0])

                if is_left_turn_gesture: self.current_pose_name = "좌회전"
                elif is_right_turn_gesture: self.current_pose_name = "우회전"
                elif is_stop_gesture: self.current_pose_name = "정지"
            except Exception as e:
                self.current_pose_name = "인식 불가"
        
        # 5. 스켈레톤 그리기 (미니맵용 프레임에 덮어쓰기)
        #    (game.py가 이 프레임을 가져가서 미니맵으로 사용)
        if results.pose_landmarks:
            frame_to_draw = cv2.cvtColor(self.latest_frame_rgb, cv2.COLOR_RGB2BGR)
            self.mp_drawing.draw_landmarks(
                frame_to_draw,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS)
            self.latest_frame_rgb = cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB)

    def get_current_pose(self):
        """game.py가 호출할 함수: 현재 판정된 포즈 이름 반환"""
        return self.current_pose_name

    def get_minimap_frame(self):
        """game.py가 호출할 함수: 미니맵에 그릴 프레임 반환"""
        return self.latest_frame_rgb

    def stop(self):
        """카메라 리소스 해제"""
        if self.cap:
            self.cap.release()
            self.cap = None # ★★★ 추가: cap을 None으로 리셋
            print("Camera released.")