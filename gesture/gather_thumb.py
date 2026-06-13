import cv2
import mediapipe as mp
import numpy as np
import csv

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
file_path = 'data/gesture_train.csv'

print("=== 录制Thumb手势数据 ===")
print("请做出标准的 👍 拇指手势")
print("按 'c' 捕获一帧数据")
print("按 'q' 退出并保存")
print()

data = []
count = 0

while cap.isOpened():
    ret, img = cap.read()
    if not ret:
        continue

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks:
        for res in result.multi_hand_landmarks:
            joint = np.zeros((21, 3))
            for j, lm in enumerate(res.landmark):
                joint[j] = [lm.x, lm.y, lm.z]

            v1 = joint[[0,1,2,3,0,5,6,7,0,9,10,11,0,13,14,15,0,17,18,19],:]
            v2 = joint[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],:]
            v = v2 - v1
            v = v / np.linalg.norm(v, axis=1)[:, np.newaxis]
            angle = np.arccos(np.einsum('nt,nt->n',
                v[[0,1,2,4,5,6,8,9,10,12,13,14,16,17,18],:],
                v[[1,2,3,5,6,7,9,10,11,13,14,15,17,18,19],:]))
            angle = np.degrees(angle)

            mp_drawing.draw_landmarks(img, res, mp_hands.HAND_CONNECTIONS)

    # 显示提示
    cv2.putText(img, f"Captured: {count}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(img, "Press 'c' to capture, 'q' to quit", (10, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow('Record Thumb Gesture', img)
    key = cv2.waitKey(1)

    if key == ord('c') and result.multi_hand_landmarks:
        row = np.append(angle, 12).astype(np.float32)  # 12 = thumb label
        data.append(row)
        count += 1
        print(f"Captured {count} samples")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# 保存数据
if data:
    with open(file_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"\n✅ Saved {count} thumb samples to {file_path}")
    print("Total thumb samples: 15 (existing) +", count, "(new) =", 15 + count)
else:
    print("No data captured")
