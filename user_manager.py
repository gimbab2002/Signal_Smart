import json
import os
import hashlib
import re

class UserManager:
    def __init__(self, filepath="users.json"):
        self.filepath = filepath

        # 파일 없으면 자동 생성
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({}, f)

        self.users = self.load_users()

    def load_users(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_users(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)

    # 비밀번호 해싱(SHA256)
    def hash_pw(self, pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    # 이메일 형식 검사
    def is_valid_email(self, email):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None

    def register(self, email, password):
        # 이메일 형식 확인
        if not self.is_valid_email(email):
            return False, "이메일 형식이 아닙니다."

        # 중복 이메일 체크
        if email in self.users:
            return False, "이미 존재하는 이메일입니다."

        # 비밀번호 조건 체크
        if len(password) < 8:
            return False, "비밀번호는 8자리 이상이어야 합니다."

        # 회원가입 처리
        self.users[email] = {"password": self.hash_pw(password)}
        self.save_users()
        return True, "회원가입 성공!"

    def login(self, email, password):
        if email not in self.users:
            return False, "존재하지 않는 이메일입니다."

        hashed = self.hash_pw(password)
        if self.users[email]["password"] != hashed:
            return False, "비밀번호가 일치하지 않습니다."

        return True, "로그인 성공!"
    
    def save_score(self, email, score):
        """해당 사용자의 최고 점수를 갱신"""
        if email not in self.users:
            return False

        prev = self.users[email].get("best_score", 0)
        if score > prev:
            self.users[email]["best_score"] = score
            self.save_users()

        return True
    
    def get_ranking(self, top_n=10):
        """전체 사용자 중 best_score 순위 리스트 반환"""
        ranking_list = []

        for email, data in self.users.items():
            best_score = data.get("best_score", 0)
            ranking_list.append((email, best_score))

        ranking_list.sort(key=lambda x: x[1], reverse=True)

        return ranking_list[:top_n]