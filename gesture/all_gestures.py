import cv2
import mediapipe as mp
import numpy as np

max_num_hands = 1
# 所有手势映射（包括thumb和ok）
gesture = {
    0:'rock', 5:'paper', 9:'scissors', 12:'thumb', 10:'ok',
}
# emoji显示
emoji = {
    'rock': '✊',
    'paper': '✋',
    'scissors': '✌️',
    'thumb': '👍',
    'ok': '👌'
}

# MediaPipe hands model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=max_num_hands,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Gesture recognition model
file = np.genfromtxt('data/gesture_train.csv', delimiter=',')
angle = file[:,:-1].astype(np.float32)
label = file[:, -1].astype(np.float32)
knn = cv2.ml.KNearest_create()
knn.train(angle, cv2.ml.ROW_SAMPLE, label)

cap = cv2.VideoCapture(0)

# 稳定性检测
last_gesture = None
stable_frames = 0

print("手势识别Demo - 所有手势")
print("按 'q' 退出")
print(f"加载了 {angle.shape[0]} 个训练样本")

while cap.isOpened():
    ret, img = cap.read()
    if not ret:
        continue

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    result = hands.process(img_rgb)

    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks is not None:
        for res in result.multi_hand_landmarks:
            joint = np.zeros((21, 3))
            for j, lm in enumerate(res.landmark):
                joint[j] = [lm.x, lm.y, lm.z]

            # Compute angles between joints
            v1 = joint[[0,1,2,3,0,5,6,7,0,9,10,11,0,13,14,15,0,17,18,19],:] # Parent joint
            v2 = joint[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],:] # Child joint
            v = v2 - v1 # [20,3]
            # Normalize v
            v = v / np.linalg.norm(v, axis=1)[:, np.newaxis]

            # Get angle using arcos of dot product
            angle = np.arccos(np.einsum('nt,nt->n',
                v[[0,1,2,4,5,6,8,9,10,12,13,14,16,17,18],:],
                v[[1,2,3,5,6,7,9,10,11,13,14,15,17,18,19],:])) # [15,]

            angle = np.degrees(angle) # Convert radian to degree

            # Inference gesture
            data = np.array([angle], dtype=np.float32)
            ret, results, neighbours, dist = knn.findNearest(data, 3)
            idx = int(results[0][0])

            # 稳定性检测
            current_gesture = gesture.get(idx, None)
            if current_gesture == last_gesture and current_gesture is not None:
                stable_frames += 1
            else:
                stable_frames = 0
                last_gesture = current_gesture

            # 显示识别结果
            if current_gesture:
                gesture_name = current_gesture.upper()
                emoji_char = emoji.get(current_gesture, '?')

                # 显示稳定帧数
                stability_text = f"Stable: {stable_frames}/5"
                cv2.putText(img, stability_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                # 只有稳定5帧以上才显示最终识别结果
                if stable_frames >= 5:
                    # 绿色背景显示识别结果
                    text_size = cv2.getTextSize(gesture_name, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
                    cv2.rectangle(img, (10, 50), (text_size[0] + 30, 110), (0, 255, 0), -1)
                    cv2.putText(img, gesture_name, (20, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
                    cv2.putText(img, emoji_char, (text_size[0] + 40, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
                else:
                    # 不稳定时显示灰色
                    cv2.putText(img, f"Detecting: {gesture_name}...", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)

            mp_drawing.draw_landmarks(img, res, mp_hands.HAND_CONNECTIONS)

    cv2.imshow('All Gestures Recognition', img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
