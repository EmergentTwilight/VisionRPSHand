#!/usr/bin/env python3
"""
VisionRPSHand Web版 - 321猜拳游戏
Flask + SocketIO + MediaPipe + OpenCV
"""
import cv2
import numpy as np
import random
import base64
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

# MediaPipe会在运行时导入


app = Flask(__name__)
app.config['SECRET_KEY'] = 'rps-game-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=False)


class RPSGameEngine:
    """猜拳游戏引擎"""

    GESTURES = {0: 'rock', 5: 'paper', 9: 'scissors'}
    GESTURE_NAMES = {'rock': '石头', 'paper': '布', 'scissors': '剪刀'}
    EMOJI = {'rock': '✊', 'paper': '✋', 'scissors': '✌️'}

    WIN_RULES = {
        ('rock', 'scissors'): '石头砸剪刀',
        ('scissors', 'paper'): '剪刀剪布',
        ('paper', 'rock'): '布包石头'
    }

    def __init__(self):
        self.user_score = 0
        self.machine_score = 0
        self.tie_count = 0
        self.mp_hands = None
        self.knn = None
        self.mp_drawing = None
        self.camera = None
        self.hand_connected = False

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
            data_path = '/home/nvidia/VisionRPSHand/Rock-Paper-Scissors-Machine/data/gesture_train.csv'
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

            print("初始化成功")
            return True
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def recognize_gesture(self, landmarks):
        """识别手势"""
        if self.knn is None:
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
        return random.choice(list(self.GESTURE_NAMES.keys()))

    def determine_winner(self, user_gesture, machine_gesture):
        """判断胜负"""
        if user_gesture == machine_gesture:
            return 'tie', '平局'
        elif (user_gesture, machine_gesture) in self.WIN_RULES:
            return 'user', f'你赢了! {self.WIN_RULES[(user_gesture, machine_gesture)]}'
        else:
            return 'machine', f'机器赢了! {self.WIN_RULES[(machine_gesture, user_gesture)]}'

    def process_frame(self):
        """处理一帧图像"""
        if not self.camera or not self.camera.isOpened():
            return None, None

        ret, frame = self.camera.read()
        if not ret:
            return None, None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb)
        hand_landmarks = None

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                hand_landmarks = res.landmark
                self.mp_drawing.draw_landmarks(
                    frame, res, self.mp_hands.HAND_CONNECTIONS
                )
                break  # 只取第一只手

        # RGB转回BGR用于显示
        frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return frame, hand_landmarks

    def frame_to_bytes(self, frame):
        """将frame转换为jpeg bytes"""
        if frame is None:
            return None
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes() if ret else None

    # ==================== 灵巧手接口（预留） ====================
    def dexterous_hand_init(self):
        """初始化灵巧手"""
        print("[灵巧手接口] 初始化...")
        self.hand_connected = True
        return True

    def dexterous_hand_make_gesture(self, gesture):
        """控制灵巧手做出手势"""
        emoji = self.EMOJI.get(gesture, gesture)
        print(f"[灵巧手接口] 做出手势: {emoji}")


# 全局游戏引擎
game = RPSGameEngine()

# 游戏状态
game_state = {
    'state': 'idle',  # idle, countdown, result
    'countdown': 0,
    'user_gesture': None,
    'machine_gesture': None,
    'scores': {'user': 0, 'machine': 0, 'tie': 0}
}


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


@socketio.on('start_game')
def handle_start_game():
    """开始游戏"""
    if game_state['state'] != 'idle':
        return

    game_state['state'] = 'countdown'
    game_state['countdown'] = 3
    game_state['user_gesture'] = None
    game_state['machine_gesture'] = None

    emit('game_state', {'state': 'countdown', 'countdown': 3})
    emit('gestures', {'user': None, 'machine': None})
    emit('result', {'text': '', 'color': '#2c3e50'})

    # 开始倒计时
    socketio.start_background_task(countdown_task)


def countdown_task():
    """倒计时任务"""
    import time

    for i in range(3, 0, -1):
        if game_state['state'] != 'countdown':
            return
        game_state['countdown'] = i
        socketio.emit('countdown', {'countdown': i})
        socketio.sleep(1)

    if game_state['state'] != 'countdown':
        return

    socketio.emit('countdown', {'countdown': '出!'})
    socketio.sleep(0.5)

    # 显示结果
    show_result()


def show_result():
    """显示结果"""
    game_state['state'] = 'result'

    # 机器出拳
    game_state['machine_gesture'] = game.get_machine_gesture()

    # 控制灵巧手
    game.dexterous_hand_make_gesture(game_state['machine_gesture'])

    # 判断胜负
    user_gesture = game_state['user_gesture'] if game_state['user_gesture'] else '未识别'

    if game_state['user_gesture']:
        winner, reason = game.determine_winner(
            game_state['user_gesture'],
            game_state['machine_gesture']
        )
        if winner == 'user':
            result = f"你赢了! {reason}"
            color = "#27ae60"
            game_state['scores']['user'] += 1
        elif winner == 'machine':
            result = f"机器赢了! {reason}"
            color = "#e74c3c"
            game_state['scores']['machine'] += 1
        else:
            result = "平局!"
            color = "#f39c12"
            game_state['scores']['tie'] += 1
    else:
        result = "未识别手势，机器获胜!"
        color = "#e74c3c"
        game_state['scores']['machine'] += 1

    # 发送结果
    socketio.emit('gestures', {
        'user': game_state['user_gesture'],
        'machine': game_state['machine_gesture']
    })
    socketio.emit('result', {'text': result, 'color': color})
    socketio.emit('scores', game_state['scores'])

    # 2秒后重置
    socketio.sleep(2)
    reset_game()


def reset_game():
    """重置游戏"""
    game_state['state'] = 'idle'
    game_state['countdown'] = 0
    socketio.emit('game_state', {'state': 'idle'})


def video_stream():
    """视频流生成器"""
    frame_count = 0
    while True:
        try:
            frame, landmarks = game.process_frame()
            if frame is None:
                continue

            frame_count += 1

            # 游戏进行中，识别手势
            if game_state['state'] == 'countdown' and landmarks:
                gesture = game.recognize_gesture(landmarks)
                if gesture:
                    game_state['user_gesture'] = gesture

            # 转换为bytes
            frame_bytes = game.frame_to_bytes(frame)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                print(f"Frame {frame_count}: 编码失败")
        except Exception as e:
            print(f"视频流错误: {e}")
            continue


@app.route('/video_feed')
def video_feed():
    """视频流"""
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # 初始化游戏引擎
    if not game.initialize():
        print("游戏引擎初始化失败")
        exit(1)

    print("启动Web服务器...")
    print("访问地址: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
