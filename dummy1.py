from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import FeatureMapReceiver
import sys
import time
from datetime import datetime
from iottalkpy import dan
import numpy as np
import base64
import zlib
import json

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
        name = 'wenggg_collect',
        id_= '66032986-e854-4d12-9962-7231e474fb3b',
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

# ========== 主手勢資料收集流程 ==========
def startLoop(R, gesture_index):
    frames_per_gesture = 30

    gesture_frames = []
    print(f'📸 開始收集手勢 {gesture_index}...')
    frame_count = 0

    while len(gesture_frames) < frames_per_gesture:
        res = R.getResults()
        if res is None:
            continue

        frame_count += 1
        print(f'📸 幀號: {frame_count} - 手勢 {gesture_index}')

        rdi_map = np.array(res[0])
        phd_map = np.array(res[1])

        gesture_frames.append({
            "frame": frame_count,
            "RDI": rdi_map.tolist(),
            "PHD": phd_map.tolist(),
        })

    print(f"✅ 成功收集手勢 {gesture_index} 的數據，開始上傳...")

    data = {
        "gesture": gesture_index,
        "frames": gesture_frames
    }

    json_str = json.dumps(data)
    json_bytes = json_str.encode('utf-8')
    compressed = zlib.compress(json_bytes)
    b64_encoded = base64.b64encode(compressed)
    b64_str = b64_encoded.decode('utf-8')

    try:
        client.push('DummySensor-I', [b64_str])
        print(datetime.now().isoformat(), f'→ 已推送：b64_str')
        return True
    except Exception as e:
        print(f'推送失敗: {e}')
        return False

# ====== 主程式互動 ======
def main():
    kgl.setLib()
    connect()
    startSetting()
    R = FeatureMapReceiver(chirps=32)
    R.trigger(chirps=32)
    time.sleep(0.5)

    max_gesture_count = 20  # ✅ 可自行調整
    gesture_count = 0

    print('# ======== 請輸入 start 開始收集手勢 =========')
    try:
        while gesture_count < max_gesture_count:
            user_input = input(f"\n請輸入 'start' 以開始收集第 {gesture_count + 1} 筆手勢（共 {max_gesture_count} 筆）：")
            if user_input.strip().lower() == 'start':
                startLoop(R, gesture_count + 1)
                gesture_count += 1
            else:
                print("❌ 輸入錯誤，請輸入 'start'。")

        print("✅ 已收集完所有手勢資料，程式結束")

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