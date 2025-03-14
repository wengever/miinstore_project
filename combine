from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import RawDataReceiver, HWResultReceiver, FeatureMapReceiver
from iottalkpy import dan 
import time
import numpy as np
import requests
import json

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

    frame_count = 0  # 幀計數器

    while True:
        res = R.getResults()
        if res is None:
            continue
        
        frame_count += 1  # 增加幀號
        print(f'📸 幀號: {frame_count}')  # 顯示當前幀號

         # res 內包含兩個 32x32 的 NumPy 陣列
        rdi_map = np.array(res[0])  # RDI MAP
        phd_map = np.array(res[1])  # PHD MAP
        
        print(f"📊 rdi = \n{rdi_map}")  # 顯示 RDI 數據
        print(f"📊 phd = \n{phd_map}")  # 顯示 PHD 數據
        
        print("📡 收到 RDI 和 PHD 數據，準備發送 JSON...")

        # 構建 JSON 資料
        data = {
            "frame": frame_count,  # 加入幀號
            "RDI": rdi_map.tolist(),  # 轉換為 JSON 可傳輸格式
            "PHD": phd_map.tolist()
        }
        try:
            dan.push('DummySensor-I', json.dumps(data))
            print(f"✅ 成功上傳 frame {frame_count} 至 IoTtalk")
        except Exception as e:
            print(f"❌ 上傳失敗: {e}")


def main():
    kgl.setLib()
    connect()
    startSetting()
    startLoop()

if __name__ == '__main__':
    main()
