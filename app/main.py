#!/usr/bin/env python3
"""
VisionRPSHand Web版 - 状态机猜拳游戏
Flask + SocketIO + MediaPipe + OpenCV + AmazingHand

游戏流程:
- monitoring: 监控手势，等待OK开始
- countdown: 321倒计时
- result: 显示结果
- paused: 回合间暂停
- game_over: 游戏结束(收到thumb或连续3次无效)
"""
import cv2
import numpy as np
import random
import json
import time
from datetime import datetime
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

# ==================== AmazingHand 灵巧手控制 ====================
AMAZINGHAND_PORT = "/dev/ttyACM0"
HAND_AVAILABLE = False

try:
    from rustypot import Scs0009PyController

    FINGERS = {
        "index": {"ids": [1, 2], "middle": [0.0, 0.0], "close_offset": [-30, 30], "open_offset": [90, -90]},
        "middle": {"ids": [3, 4], "middle": [0.0, 0.0], "close_offset": [-120, 120], "open_offset": [30, -30]},
        "ring": {"ids": [5, 6], "middle": [0.0, 0.0], "close_offset": [-110, 110], "open_offset": [20, -20]},
        "thumb": {"ids": [7, 8], "middle": [0.0, 0.0], "close_offset": [-110, 110], "open_offset": [20, -20]},
    }

    # [index_open, middle_open, ring_open, thumb_open]
    HAND_GESTURES = {
        'rock': [0, 0, 0, 0],      # 全闭合
        'scissors': [1, 1, 0, 0],  # 食指中指张开
        'paper': [1, 1, 1, 1],     # 全张开
        'thumb': [0, 0, 0, 1],    # 仅拇指张开
        'ok': [0, 0, 0, 0],       # 拇指食指OK (特殊处理)
    }

    HAND_AVAILABLE = True
    print("✅ rustypot 可用")
except ImportError:
    print("⚠️ rustypot 未安装，灵巧手功能将不可用")
    FINGERS = None
    HAND_GESTURES = None


app = Flask(__name__)
app.config['SECRET_KEY'] = 'rps-game-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=False)


# 高分文件路径
HIGH_SCORE_FILE = '/home/nvidia/VisionRPSHand/web_rps_game/high_scores.json'


class HighScoreManager:
    """高分管理器"""

    def __init__(self):
        self.scores = self.load_scores()

    def load_scores(self):
        """加载高分记录"""
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_scores(self):
        """保存高分记录"""
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except Exception as e:
            print(f"保存高分失败: {e}")

    def add_score(self, user_score, machine_score):
        """添加新分数"""
        record = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_score': user_score,
            'machine_score': machine_score,
            'difference': user_score - machine_score
        }
        self.scores.append(record)
        # 只保留前10名
        self.scores.sort(key=lambda x: x['difference'], reverse=True)
        self.scores = self.scores[:10]
        self.save_scores()
        return self.scores

    def get_top_score(self):
        """获取最高分"""
        if self.scores:
            return self.scores[0]
        return {'user_score': 0, 'machine_score': 0, 'difference': 0}


class RPSGameEngine:
    """猜拳游戏引擎 - 状态机"""

    # 手势ID映射 (根据gesture_train.csv的标签)
    # thumb暂时移除，等待重新录制更好的数据
    GESTURES = {0: 'rock', 5: 'paper', 9: 'scissors', 10: 'ok'}
    GESTURE_NAMES = {'rock': '石头', 'paper': '布', 'scissors': '剪刀', 'ok': 'OK'}
    EMOJI = {'rock': '✊', 'paper': '✋', 'scissors': '✌️', 'ok': '👌'}

    # 游戏手势 (用于猜拳)
    GAME_GESTURES = ['rock', 'paper', 'scissors']

    # 用于结束游戏的手势（暂时禁用thumb）
    END_GESTURES = []  # 空表示暂时不用手势结束游戏

    WIN_RULES = {
        ('rock', 'scissors'): '石头砸剪刀',
        ('scissors', 'paper'): '剪刀剪布',
        ('paper', 'rock'): '布包石头'
    }

    def __init__(self):
        self.mp_hands = None
        self.knn = None
        self.mp_drawing = None
        self.camera = None
        self.hand_connected = False
        self.hand_controller = None

        # 游戏状态
        self.current_score = {'user': 0, 'machine': 0}
        self.consecutive_invalid = 0  # 连续无效手势次数

        # 手势锁 - 防止同时执行多个手势动作
        self.gesture_busy = False

    def initialize(self):
        """初始化模型和摄像头"""
        try:
            import mediapipe as mp
            print("导入 MediaPipe...")
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils

            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("MediaPipe Hands 初始化成功")

            # 加载KNN模型
            data_path = '/home/nvidia/VisionRPSHand/gesture/data/gesture_train.csv'
            print(f"加载训练数据: {data_path}")
            file = np.genfromtxt(data_path, delimiter=',')
            angle = file[:, :-1].astype(np.float32)
            label = file[:, -1].astype(np.float32)
            self.knn = cv2.ml.KNearest_create()
            self.knn.train(angle, cv2.ml.ROW_SAMPLE, label)
            print(f"KNN模型加载成功: {angle.shape[0]} 个样本")

            # 打开摄像头
            print("打开摄像头...")
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("无法打开摄像头")
                return False
            print(f"摄像头打开成功: {self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

            # 初始化灵巧手
            self.dexterous_hand_init()

            print("初始化成功")
            return True
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def recognize_gesture(self, landmarks):
        """识别手势"""
        if self.knn is None or landmarks is None:
            return None

        joint = np.zeros((21, 3))
        for j, lm in enumerate(landmarks):
            joint[j] = [lm.x, lm.y, lm.z]

        v1 = joint[[0,1,2,3,0,5,6,7,0,9,10,11,0,13,14,15,0,17,18,19], :]
        v2 = joint[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20], :]
        v = v2 - v1
        v = v / np.linalg.norm(v, axis=1)[:, np.newaxis]

        angle = np.arccos(np.einsum('nt,nt->n',
            v[[0,1,2,4,5,6,8,9,10,12,13,14,16,17,18], :],
            v[[1,2,3,5,6,7,9,10,11,13,14,15,17,18,19], :]))
        angle = np.degrees(angle)

        data = np.array([angle], dtype=np.float32)
        ret, results, neighbours, dist = self.knn.findNearest(data, 3)
        idx = int(results[0][0])

        if idx in self.GESTURES:
            return self.GESTURES[idx]
        return None

    def get_machine_gesture(self):
        """机器随机出拳"""
        return random.choice(self.GAME_GESTURES)

    def determine_winner(self, user_gesture, machine_gesture):
        """判断胜负"""
        if user_gesture == machine_gesture:
            return 'tie', '平局'
        elif (user_gesture, machine_gesture) in self.WIN_RULES:
            return 'user', f'你赢了! {self.WIN_RULES[(user_gesture, machine_gesture)]}'
        else:
            return 'machine', f'机器赢了! {self.WIN_RULES[(machine_gesture, user_gesture)]}'

    def process_frame(self, show_overlay=True):
        """处理一帧图像，返回 (frame, hand_landmarks, detected_gesture)

        Args:
            show_overlay: 是否在帧上绘制关键点和手势结果（默认True）
        """
        if not self.camera or not self.camera.isOpened():
            return None, None, None

        ret, frame = self.camera.read()
        if not ret:
            return None, None, None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb)
        hand_landmarks = None
        detected_gesture = None

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                hand_landmarks = res.landmark

                if show_overlay:
                    # 在帧上绘制关键点（frame是BGR格式）
                    self.mp_drawing.draw_landmarks(
                        frame, res, self.mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                        connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )

                # 识别手势
                detected_gesture = self.recognize_gesture(hand_landmarks)

                if show_overlay and detected_gesture:
                    # 使用英文手势名称
                    gesture_name = detected_gesture.upper()

                    # 计算手部位置
                    h, w = frame.shape[:2]
                    hand_x = int(hand_landmarks[0].x * w)
                    hand_y = int(hand_landmarks[0].y * h)

                    # 绘制半透明背景
                    overlay = frame.copy()
                    text_size = cv2.getTextSize(gesture_name, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    cv2.rectangle(overlay, (hand_x - 10, hand_y - 40), (hand_x + text_size[0] + 20, hand_y + 10), (0, 255, 0), -1)
                    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

                    # 显示手势名称
                    cv2.putText(frame, gesture_name, (hand_x, hand_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

                break  # 只处理第一只手

        # frame已经是BGR格式，不需要再转换
        return frame, hand_landmarks, detected_gesture

    def frame_to_bytes(self, frame):
        """将frame转换为jpeg bytes"""
        if frame is None:
            return None
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes() if ret else None

    # ==================== 灵巧手接口 ====================
    def dexterous_hand_init(self):
        """初始化灵巧手"""
        if not HAND_AVAILABLE:
            print("[灵巧手] rustypot 不可用，跳过初始化")
            return False

        try:
            print(f"[灵巧手] 尝试连接串口 {AMAZINGHAND_PORT}...")
            self.hand_controller = Scs0009PyController(
                serial_port=AMAZINGHAND_PORT,
                baudrate=1000000,
                timeout=0.5,
            )

            for sid in range(1, 9):
                self.hand_controller.write_torque_enable(sid, 1)

            time.sleep(0.2)
            self.hand_connected = True
            print("[灵巧手] ✅ 初始化成功")
            return True
        except Exception as e:
            print(f"[灵巧手] ❌ 初始化失败: {e}")
            self.hand_connected = False
            return False

    def dexterous_hand_make_gesture(self, gesture):
        """控制灵巧手做出手势"""
        if not self.hand_connected or not HAND_AVAILABLE:
            return

        try:
            gesture_config = HAND_GESTURES.get(gesture, [0, 0, 0, 0])
            finger_names = ["index", "middle", "ring", "thumb"]

            for i, finger_name in enumerate(finger_names):
                cfg = FINGERS[finger_name]
                ids = cfg["ids"]
                mid = cfg["middle"]

                if gesture_config[i]:
                    off = cfg["open_offset"]
                else:
                    off = cfg["close_offset"]

                self.hand_controller.write_goal_speed(ids[0], 6)
                self.hand_controller.write_goal_speed(ids[1], 6)
                pos1 = np.deg2rad(mid[0] + off[0])
                pos2 = np.deg2rad(mid[1] + off[1])
                self.hand_controller.write_goal_position(ids[0], pos1)
                self.hand_controller.write_goal_position(ids[1], pos2)

            emoji = self.EMOJI.get(gesture, gesture)
            print(f"[灵巧手] ✅ 做出手势: {emoji}")

        except Exception as e:
            print(f"[灵巧手] ❌ 做手势失败: {e}")

    def dexterous_hand_wave_hello(self, cycles=2):
        """打招呼动画 - 波浪"""
        if not self.hand_connected or not HAND_AVAILABLE:
            return

        try:
            import math
            finger_order = ["index", "middle", "ring"]
            STEP = 0.15

            # 先张开所有手指
            for name in FINGERS:
                cfg = FINGERS[name]
                self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
            time.sleep(0.5)

            for cycle in range(cycles):
                for name in finger_order:
                    cfg = FINGERS[name]
                    self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                    self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                    pos1 = np.deg2rad(cfg["middle"][0] + cfg["close_offset"][0])
                    pos2 = np.deg2rad(cfg["middle"][1] + cfg["close_offset"][1])
                    self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                    self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
                    time.sleep(STEP)

                for name in finger_order:
                    cfg = FINGERS[name]
                    self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                    self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                    pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                    pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                    self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                    self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
                    time.sleep(STEP)

            # 回到张开状态
            for name in FINGERS:
                cfg = FINGERS[name]
                self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
            time.sleep(0.3)

            print("[灵巧手] ✅ 波浪动画完成")

        except Exception as e:
            print(f"[灵巧手] ❌ 波浪动画失败: {e}")

    def dexterous_hand_index_sway(self, duration=2.0, freq=0.8):
        """食指摆动动画"""
        if not self.hand_connected or not HAND_AVAILABLE:
            return

        try:
            import math
            # 收起中指、无名指、拇指
            for name in ["middle", "ring", "thumb"]:
                cfg = FINGERS[name]
                self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                pos1 = np.deg2rad(cfg["middle"][0] + cfg["close_offset"][0])
                pos2 = np.deg2rad(cfg["middle"][1] + cfg["close_offset"][1])
                self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
            time.sleep(0.3)

            # 食指摆动参数
            LEFT_1, LEFT_2 = 60, -150
            RIGHT_1, RIGHT_2 = 150, -60
            CENTER_1 = (LEFT_1 + RIGHT_1) / 2
            AMP_1 = (RIGHT_1 - LEFT_1) / 2
            CENTER_2 = (LEFT_2 + RIGHT_2) / 2
            AMP_2 = (RIGHT_2 - LEFT_2) / 2

            t0 = time.time()
            update_interval = 0.03

            while time.time() - t0 < duration:
                t = time.time() - t0
                phase = 2 * math.pi * freq * t
                a1 = CENTER_1 + AMP_1 * math.sin(phase)
                a2 = CENTER_2 + AMP_2 * math.sin(phase)

                self.hand_controller.write_goal_speed(1, 7)
                self.hand_controller.write_goal_speed(2, 7)
                self.hand_controller.write_goal_position(1, np.deg2rad(a1))
                self.hand_controller.write_goal_position(2, np.deg2rad(a2))
                time.sleep(update_interval)

            print("[灵巧手] ✅ 食指摆动完成")

        except Exception as e:
            print(f"[灵巧手] ❌ 食指摆动失败: {e}")

    def dexterous_hand_bye_bye(self, cycles=3):
        """再见动画 - 食指中指无名指挥手，拇指保持张开不动"""
        if not self.hand_connected or not HAND_AVAILABLE:
            return

        try:
            # 先张开所有手指
            for name in FINGERS:
                cfg = FINGERS[name]
                self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
            time.sleep(0.5)

            # 拇指保持张开，其他手指挥手
            waving_fingers = ["index", "middle", "ring"]
            for cycle in range(cycles):
                # 闭合
                for name in waving_fingers:
                    cfg = FINGERS[name]
                    self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                    self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                    pos1 = np.deg2rad(cfg["middle"][0] + cfg["close_offset"][0])
                    pos2 = np.deg2rad(cfg["middle"][1] + cfg["close_offset"][1])
                    self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                    self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
                time.sleep(0.3)

                # 张开
                for name in waving_fingers:
                    cfg = FINGERS[name]
                    self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                    self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                    pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                    pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                    self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                    self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
                time.sleep(0.3)

            # 最后张开所有手指（除拇指外）
            for name in waving_fingers:
                cfg = FINGERS[name]
                self.hand_controller.write_goal_speed(cfg["ids"][0], 7)
                self.hand_controller.write_goal_speed(cfg["ids"][1], 7)
                pos1 = np.deg2rad(cfg["middle"][0] + cfg["open_offset"][0])
                pos2 = np.deg2rad(cfg["middle"][1] + cfg["open_offset"][1])
                self.hand_controller.write_goal_position(cfg["ids"][0], pos1)
                self.hand_controller.write_goal_position(cfg["ids"][1], pos2)
            time.sleep(0.3)

            print("[灵巧手] ✅ 再见动画完成")

        except Exception as e:
            print(f"[灵巧手] ❌ 再见动画失败: {e}")


# ==================== 全局变量 ====================
import os
game = RPSGameEngine()
high_score_mgr = HighScoreManager()

# 游戏状态: monitoring, countdown, result, paused, game_over
game_state = {
    'state': 'monitoring',
    'countdown': 0,
    'user_gesture': None,
    'machine_gesture': None,
    'current_score': {'user': 0, 'machine': 0},
    'detected_gesture': None,  # 当前检测到的手势
    'ok_cooldown_until': 0,  # OK冷却时间戳（防止刚结束就重新开始）
}


# ==================== Flask 路由 ====================
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connected', {'data': '连接成功'})
    emit('hand_status', {'connected': game.hand_connected})
    emit('high_scores', high_score_mgr.scores)


@socketio.on('get_high_scores')
def handle_get_high_scores():
    """获取高分记录"""
    emit('high_scores', high_score_mgr.scores)


# ==================== 状态机 ====================
def change_state(new_state, **kwargs):
    """状态切换"""
    game_state['state'] = new_state
    socketio.emit('game_state', {'state': new_state, **kwargs})
    print(f"[状态切换] {new_state}")


def with_gesture_lock(func):
    """手势动作锁装饰器 - 确保同一时间只有一个手势动作在执行"""
    def wrapper(*args, **kwargs):
        if game.gesture_busy:
            print("[手势锁] 另一个手势动作正在进行中，跳过")
            return
        game.gesture_busy = True
        try:
            return func(*args, **kwargs)
        finally:
            game.gesture_busy = False
    return wrapper


def wave_hello_animation():
    """波浪打招呼动画"""
    if not game.gesture_busy:
        game.gesture_busy = True
        game.dexterous_hand_wave_hello(cycles=2)
        game.gesture_busy = False
    time.sleep(0.5)
    # 波浪完成后开始倒计时
    socketio.start_background_task(countdown_task)


def countdown_task():
    """倒计时任务 - 3→2→1→0"""
    # 清空用户手势（每轮重新记录）
    game_state['user_gesture'] = None

    # 复原到石头(握拳)状态
    game.dexterous_hand_make_gesture('rock')
    time.sleep(0.3)

    # T-3: 显示 "3"
    if game_state['state'] != 'countdown':
        return
    socketio.emit('countdown', {'countdown': 3})
    socketio.sleep(1)

    # T-2: 显示 "2"
    if game_state['state'] != 'countdown':
        return
    socketio.emit('countdown', {'countdown': 2})
    socketio.sleep(1)

    # T-1: 显示 "1"
    if game_state['state'] != 'countdown':
        return
    socketio.emit('countdown', {'countdown': 1})
    socketio.sleep(0.8)  # 等待0.8秒

    # T-0.2: 机器开始出拳（非阻塞）
    if game_state['state'] != 'countdown':
        return
    machine_gesture = game.get_machine_gesture()
    game_state['machine_gesture'] = machine_gesture
    game.dexterous_hand_make_gesture(machine_gesture)  # 非阻塞，立即返回
    socketio.sleep(0.2)  # 再等待0.2秒

    # T=0: 倒计时结束（显示 "0"）
    if game_state['state'] != 'countdown':
        return
    socketio.emit('countdown', {'countdown': 0})

    # T+0.2: 识别用户手势（只识别一次）
    socketio.sleep(0.2)

    if game_state['state'] != 'countdown':
        return

    # 识别用户手势（5帧取最常见）
    user_gesture = None
    try:
        # 获取几帧来稳定识别
        gestures = []
        for _ in range(5):
            frame, landmarks, detected = game.process_frame()
            if landmarks and detected:
                gestures.append(detected)
            socketio.sleep(0.05)

        # 取出现次数最多的手势
        if gestures:
            from collections import Counter
            user_gesture = Counter(gestures).most_common(1)[0][0]
    except Exception as e:
        print(f"[倒计时0] 识别手势出错: {e}")

    # 如果识别到OK，结束游戏（不算分）
    if user_gesture == 'ok':
        print("[倒计时0] 用户出OK，结束游戏（不算分）")
        socketio.sleep(0.5)  # 让用户看到机器手势
        if not game.gesture_busy:
            game.gesture_busy = True
            game.dexterous_hand_bye_bye()
            game.gesture_busy = False
        end_game("玩家主动结束")
        return

    # 记录用户手势
    game_state['user_gesture'] = user_gesture

    # 停留1秒让用户看清楚手势
    socketio.sleep(1)

    # 显示结果
    if game_state['state'] == 'countdown':
        show_result()


def show_result():
    """显示结果"""
    change_state('result')

    # 获取机器手势（已在countdown时出拳）
    machine_gesture = game_state.get('machine_gesture')
    # 获取用户手势 (在倒计时期间记录)
    user_gesture = game_state.get('user_gesture')

    # 判断胜负
    machine_won = False
    if user_gesture in game.GAME_GESTURES:
        game.consecutive_invalid = 0  # 重置无效计数

        winner, reason = game.determine_winner(user_gesture, machine_gesture)
        if winner == 'user':
            result = f"你赢了! {reason}"
            color = "#27ae60"
            game.current_score['user'] += 1
        elif winner == 'machine':
            result = f"机器赢了! {reason}"
            color = "#e74c3c"
            game.current_score['machine'] += 1
            machine_won = True
        else:
            result = "平局!"
            color = "#f39c12"
    else:
        # 无效手势
        game.consecutive_invalid += 1
        if user_gesture:
            result = f"无效手势 ({game.GESTURE_NAMES.get(user_gesture, user_gesture)})"
        else:
            result = "未识别手势"
        color = "#e74c3c"
        game.current_score['machine'] += 1

    # 检查是否连续3次无效
    if game.consecutive_invalid >= 3:
        game_state['current_score'] = game.current_score.copy()
        socketio.emit('result', {'text': result, 'color': color})
        socketio.emit('gestures', {'user': user_gesture, 'machine': machine_gesture})
        socketio.emit('scores', game.current_score)
        socketio.sleep(2)
        # 连续3次无效，做bye bye手势后结束游戏
        if not game.gesture_busy:
            game.gesture_busy = True
            game.dexterous_hand_bye_bye()
            game.gesture_busy = False
        end_game("连续3次无效手势")
        return

    # 发送结果
    game_state['current_score'] = game.current_score.copy()
    socketio.emit('result', {'text': result, 'color': color})
    socketio.emit('gestures', {'user': user_gesture, 'machine': machine_gesture})
    socketio.emit('scores', game.current_score)

    # 显示结果后，如果机器赢了，做嘲讽手势
    if machine_won:
        socketio.sleep(0.5)  # 先让用户看清结果
        # 使用手势锁
        if not game.gesture_busy:
            game.gesture_busy = True
            game.dexterous_hand_index_sway(duration=2.0, freq=0.8)
            game.gesture_busy = False
        socketio.sleep(0.5)  # 等待动画完成
    else:
        socketio.sleep(2)  # 不是机器赢，停留2秒

    # 暂停后下一轮
    change_state('paused')
    socketio.sleep(1.5)  # 暂停1.5秒

    # 下一轮
    if game_state['state'] == 'paused':
        change_state('countdown')
        socketio.start_background_task(countdown_task)


def end_game(reason):
    """结束游戏"""
    print(f"[游戏结束] {reason}")
    change_state('game_over', reason=reason)

    # 保存高分
    scores = high_score_mgr.add_score(
        game.current_score['user'],
        game.current_score['machine']
    )
    socketio.emit('high_scores', scores)

    # 3秒后返回监控状态
    socketio.sleep(3)
    if game_state['state'] == 'game_over':
        # 设置OK冷却时间（3秒），防止立即重新检测
        import time
        game_state['ok_cooldown_until'] = time.time() + 3
        change_state('monitoring')


def video_stream():
    """视频流生成器 - 同时处理手势监控"""
    frame_count = 0
    last_gesture = None
    gesture_stable_frames = 0

    # 每轮开始时重置OK检测（防止开始时的OK被误识别为结束）
    ok_check_enabled = False

    while True:
        try:
            frame, landmarks, detected_gesture = game.process_frame()
            if frame is None:
                socketio.sleep(0.01)
                continue

            frame_count += 1

            # 状态变化时重置手势检测
            current_state = game_state['state']
            if not hasattr(video_stream, 'last_state'):
                video_stream.last_state = current_state
            if video_stream.last_state != current_state:
                gesture_stable_frames = 0
                last_gesture = None
                video_stream.last_state = current_state

            # 在画面左上角显示游戏状态
            status_text = f"State: {game_state['state']}"
            cv2.putText(frame, status_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # ========== 实时显示检测到的手势（所有状态）==========
            if landmarks and detected_gesture:
                emoji = game.EMOJI.get(detected_gesture, '')
                name = game.GESTURE_NAMES.get(detected_gesture, detected_gesture)
                socketio.emit('detected_gesture', {'gesture': detected_gesture, 'emoji': emoji, 'name': name})

            # ========== 手势监控（集成在视频流中）==========
            if current_state == 'monitoring' and landmarks:
                gesture = detected_gesture  # 使用process_frame中已识别的手势

                # 手势稳定性检测
                if gesture == last_gesture and gesture is not None:
                    gesture_stable_frames += 1
                else:
                    gesture_stable_frames = 0
                    last_gesture = gesture

                # 显示稳定性指示器
                stable_threshold = 3  # 所有手势统一3帧稳定
                stable_color = (0, 255, 0) if gesture_stable_frames >= stable_threshold else (0, 165, 255)
                cv2.putText(frame, f"Stable: {gesture_stable_frames}/{stable_threshold}",
                           (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, stable_color, 2)

                if gesture_stable_frames >= stable_threshold:
                    # 检测到OK手势 - 开始游戏
                    if gesture == 'ok':
                        # 检查冷却时间
                        import time
                        if time.time() < game_state.get('ok_cooldown_until', 0):
                            print("[监控状态] OK冷却中，忽略")
                            continue

                        print("[监控状态] 检测到OK手势，开始游戏")
                        game.current_score = {'user': 0, 'machine': 0}
                        game_state['user_gesture'] = None  # 清空用户手势
                        game.consecutive_invalid = 0  # 重置无效计数
                        change_state('countdown')
                        socketio.start_background_task(wave_hello_animation)
                        gesture_stable_frames = 0  # 重置
                        last_gesture = None  # 重置

            # 在倒计时期间不记录手势（只在countdown_task的0时刻识别一次）
            elif current_state == 'countdown':
                pass  # 空闲，不做处理

            # 在result状态不做OK检测（已在countdown_task的0时刻检测）
            elif current_state == 'result':
                pass  # 空闲，不做处理

            # 在paused状态不做OK检测（已在countdown_task的0时刻检测）
            elif current_state == 'paused':
                pass  # 空闲，不做处理

            # 转换为bytes
            frame_bytes = game.frame_to_bytes(frame)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"视频流错误: {e}")
            import traceback
            traceback.print_exc()
            socketio.sleep(0.1)
            continue


@app.route('/video_feed')
def video_feed():
    """视频流"""
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    if not game.initialize():
        print("游戏引擎初始化失败")
        exit(1)

    print("启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("\n游戏说明:")
    print("  1. 做出 👌 OK手势 开始游戏")
    print("  2. 321倒计时后做出 ✊✋✌️ 手势")
    print("  3. 游戏中做出 👌 OK手势 结束游戏（会做bye bye手势）")
    print("  4. 连续3次无效手势自动结束游戏（会做bye bye手势）")
    print("\n注意: thumb手势暂时禁用，等待重新录入更标准的数据")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
