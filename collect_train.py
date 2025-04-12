from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import RawDataReceiver, HWResultReceiver, FeatureMapReceiver
from iottalkpy import dan 
import time
import numpy as np
import requests
import json
import base64
import zlib


### IoTtalk 設定
api_url = 'https://miinstore.ncku.edu.tw/csm'  # IoTtalk 伺服器
device_model = 'Dummy_Device'  # IoTtalk 上的裝置名稱
idf_list = ['DummySensor-I']  # 輸入數據通道
odf_list = ['DummyControl-O']  # 輸出數據通道
push_interval = 1  # 每 1 秒上傳一次數據

# 設定 NumPy 顯示完整數據
np.set_printoptions(threshold=np.inf)

def connect():
    connect = ConnectDevice()
    connect.startUp()                       # Connect to the device
    reset = ResetDevice()
    reset.startUp()                         # Reset hardware register

def startSetting():
    SettingConfigs.setScriptDir("K60168-Test-00256-008-v0.0.8-20230717_120cm")  # Set the setting folder name
    ksp = SettingProc()                 # Object for setting process to setup the Hardware AI and RF before receive data
    ksp.startUp(SettingConfigs)             # Start the setting process
    # ksp.startSetting(SettingConfigs)        # Start the setting process in sub_thread

def startLoop():
    # kgl.ksoclib.switchLogMode(True)
    #R = RawDataReceiver(chirps=32)

    # Receiver for getting Raw data
    R = FeatureMapReceiver(chirps=32)       # Receiver for getting RDI PHD map
    # R = HWResultReceiver()                  # Receiver for getting hardware results (gestures, Axes, exponential)
    # buffer = DataBuffer(100)                # Buffer for saving latest frames of data
    R.trigger(chirps=32)                             # Trigger receiver before getting the data
    time.sleep(0.5)
    print('# ======== Start getting gesture ===========')

    gesture_count = 0  # 手勢計數器
    frame_count = 0    # 幀計數器
    max_gesture_count = 20  # 設置最大手勢數量
    frames_per_gesture = 100  # 每筆手勢包含的幀數量

    while gesture_count < max_gesture_count:
        gesture_frames = []  # 用來存儲每個手勢的幀數據

        print(f'📸 開始收集手勢 {gesture_count + 1}...')
        
        while len(gesture_frames) < frames_per_gesture:
            res = R.getResults()
            if res is None:
                continue
            
            frame_count += 1  # 增加幀號
            print(f'📸 幀號: {frame_count} - 手勢 {gesture_count + 1}')  # 顯示當前幀號

            # res 內包含兩個 32x32 的 NumPy 陣列
            rdi_map = np.array(res[0])  # RDI MAP
            phd_map = np.array(res[1])  # PHD MAP

            # 存儲當前幀的數據
            gesture_frames.append({
                "frame": frame_count,  # 加入幀號
                "RDI": rdi_map.tolist(),  # 轉換為 JSON 可傳輸格式
                "PHD": phd_map.tolist()
            })
        
        # 完成一個手勢的數據收集，將其上傳至 IoTtalk
        print(f"✅ 成功收集手勢 {gesture_count + 1} 的數據，開始上傳...")

        # 構建 JSON 資料
        data = {
            "gesture": gesture_count + 1,  # 手勢編號
            "frames": gesture_frames  # 包含 100 幀數據
        }

        # --- JSON + Zlib + Base64 ---
        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')
        compressed = zlib.compress(json_bytes)
        b64_encoded = base64.b64encode(compressed)
        b64_str = b64_encoded.decode('utf-8')

        # ✅ Print base64
        print(f"🟣 base64 data = \n{b64_str}\n")

        try:
            dan.push('DummySensor-I', b64_str)
            print(f"✅ 成功上傳手勢 {gesture_count + 1} 的數據至 IoTtalk")
        except Exception as e:
            print(f"❌ 上傳失敗: {e}")

        gesture_count += 1  # 增加手勢計數

        # 等待使用者按 Enter 鍵才繼續下一筆手勢的收集
        
        input(f"請按 Enter 鍵繼續收集下一筆手勢 ({gesture_count}/{max_gesture_count})")

    print("✅ 所有手勢數據收集並上傳完成")

def main():
    kgl.setLib()
    connect()
    startSetting()
    startLoop()

if __name__ == '__main__':
    main()
