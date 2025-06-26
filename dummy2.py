from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import FeatureMapReceiver
from model import initial_model, predict_result, ConvLSTMNet
import sys
import time
from datetime import datetime
from iottalkpy import dan
import cv2

# ====== 建立 DAN 客戶端 ======
client = dan.Client()

# ====== 設定資訊 ======
device_model = 'Dummy_Device'
idf_list = [('DummySensor-I', [])]  # 注意格式是 tuple: (name, unit)
odf_list = []  # 沒有控制功能

def on_signal(cmd, df_list):
    print(f'[Signal] {cmd} on {df_list}')
    return True

def on_data(df_name, data):
    print(f'[ODF] {df_name} received: {data}')

try:
    client.register(
        url='https://miinstore.ncku.edu.tw/csm',
        on_signal=on_signal,
        on_data=on_data,
        idf_list=idf_list,
        odf_list=odf_list,
        name = 'wenggg',
        id_= '990b2d60-9ff8-4503-95dc-eb700c71a707',
        profile={
            "model": device_model,
            "is_sim": False,
        }
    )   
    print('[✔] 裝置註冊成功')
except Exception as e:
    print('[✘] 註冊失敗:', e)
    sys.exit(1)

# === 初始化硬體連線 ===
def connect():
    connect = ConnectDevice()
    connect.startUp()
    reset = ResetDevice()
    reset.startUp()

# === 設定硬體參數 ===
def startSetting():
    SettingConfigs.setScriptDir("K60168-Test-00256-008-v0.0.8-20230717_60cm")
    ksp = SettingProc()
    ksp.startUp(SettingConfigs)

# === 手勢影片播放 ===
def play_gesture_video(gesture):
    gesture_videos = {
        "turn_up": "videos/turn_up.mp4",
        "turn_down": "videos/turn_down.mp4",
        "turn_left": "videos/turn_left.mp4",
        "turn_right": "videos/turn_right.mp4",
        "background": "videos/background.mp4",
    }

    video_path = gesture_videos.get(gesture)
    if video_path is None:
        print(f"⚠️ 無對應影片可播放: {gesture}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 無法開啟影片: {video_path}")
        return

    print(f"🎬 播放手勢影片: {gesture}")

    # 建立並設定視窗為置頂
    window_name = "Gesture Demo"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Gesture Demo", frame)
        # 按 q 可中斷
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyWindow("Gesture Demo")

# === 收集一筆手勢資料，更新color與luminance ===
# ====== 全域變數 ======
luminance = 99.0
color = 3.0
red = 255.0
green = 255.0
blue = 0.0

def update_rgb_by_color():
    global red, green, blue, color
    color_mod = color % 6.0
    if color_mod == 0.0:
        red, green, blue = 255.0, 0.0, 0.0
    elif color_mod == 1.0:
        red, green, blue = 0.0, 255.0, 0.0
    elif color_mod == 2.0:
        red, green, blue = 0.0, 0.0, 255.0
    elif color_mod == 3.0:
        red, green, blue = 255.0, 255.0, 0.0
    elif color_mod == 4.0:
        red, green, blue = 0.0, 255.0, 255.0
    elif color_mod == 5.0:
        red, green, blue = 255.0, 0.0, 255.0

def startLoop(R):
    global color, luminance, red, green, blue

    buffer_rdi = []
    buffer_phd = []

    print("✅ 開始收集手勢資料...請稍後...")

    while len(buffer_rdi) < 30:
        res = R.getResults()
        if res is None:
            continue
        buffer_rdi.append(res[0])
        buffer_phd.append(res[1])
        print(f"📡 收集中: {len(buffer_rdi)}/30 幀", end='\r')

    # 預測手勢
    gesture = predict_result(buffer_rdi, buffer_phd, model)
    print(f'\n✅ 偵測到的手勢為: {gesture}')

    play_gesture_video(gesture)
    
    # 根據手勢更新 luminance 與 color 並略過 background
    if gesture == 'turn_up':
        luminance = min(luminance + 33.0, 99.0)
    elif gesture == 'turn_down':
        luminance = max(luminance - 33.0, 0.0)
    elif gesture == 'turn_right':
        color += 1.0
    elif gesture == 'turn_left':
        color -= 1.0

    # 根據 color 計算 RGB
    update_rgb_by_color()

    try:
        data_list = [luminance, red, green, blue]
        client.push('DummySensor-I', [data_list])
        print(datetime.now().isoformat(), f'→ 已推送：{data_list}')
    except Exception as e:
        print(f'推送失敗: {e}')
        return False

    return True



# ====== 主程式互動 ======
def main():
    global model
    kgl.setLib()
    connect()
    startSetting()
    model = initial_model()
    R = FeatureMapReceiver(chirps=32)
    R.trigger(chirps=32)
    time.sleep(0.5)

    print('# ======== 請輸入 start 開始收集手勢 =========')

    try:
        while True:
            user_input = input("\n請輸入 'start' 開始偵測（Ctrl+C 離開）：")
            if user_input.strip().lower() == 'start':
                startLoop(R)
            else:
                print("❌ 輸入錯誤，請輸入 'start'。")

            time.sleep(0.5)  # 避免過快的迴圈
            
    except KeyboardInterrupt:
        print("\n🛑 偵測中斷（Ctrl+C）")

    finally:
        try:
            client.deregister()
            print("✅ 已解除裝置註冊")
        except Exception as e:
            print("⚠️ 解除註冊失敗：", e)

if __name__ == '__main__':
    main()