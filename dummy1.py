from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import RawDataReceiver, HWResultReceiver, FeatureMapReceiver
import time
from iottalkpy.dan import NoData

# 引入剛剛分出去的model.py
from model import initial_model, predict_result, ConvLSTMNet

model = initial_model()

### The registeration api url, you can use IP or Domain.
api_url = 'https://miinstore.ncku.edu.tw/csm'  # default
### The Device Model in IoTtalk, please check IoTtalk document.
device_model = 'Dummy_Device'
### The input/output device features, please check IoTtalk document.
idf_list = ['DummySensor-I']
push_interval = 1  # 全局推送間隔

# 註冊成功回調
def on_register(dan):
    print('device1 register successfully')

def connect():
    connect = ConnectDevice()
    connect.startUp()                       # Connect to the device
    reset = ResetDevice()
    reset.startUp()                         # Reset hardware register

def startSetting():
    SettingConfigs.setScriptDir("K60168-Test-00256-008-v0.0.8-20230717_120cm")  # Set the setting folder name
    ksp = SettingProc()                 # Object for setting process to setup the Hardware AI and RF before receive data
    ksp.startUp(SettingConfigs)             # Start the setting process

def startLoop():
    R = FeatureMapReceiver(chirps=32)
    R.trigger(chirps=32)
    time.sleep(0.5)

    print('# ======== 輸入 start 才開始收集一筆手勢 ===========')

    color = 0
    luminance = 0

    while True:
        user_input = input("\n請輸入 'start' 開始偵測一筆手勢（或 Ctrl+C 離開）：")

        if user_input.strip().lower() == 'start':
            print("✅開始收集手勢...請稍等...")

            buffer_rdi = []
            buffer_phd = []

            # 開始收集 100筆資料點
            while len(buffer_rdi) < 100:
                res = R.getResults()
                if res is None:
                    continue
                buffer_rdi.append(res[0])
                buffer_phd.append(res[1])
                print(f"📡 正在收集第 {len(buffer_rdi)} 幀 / 共 100 幀", end='\r')

            # 收集滿了，開始預測
            rdi_map = buffer_rdi
            phd_map = buffer_phd

            gesture = predict_result(rdi_map, phd_map, model)
            print(f'✅ 偵測到的手勢是: {gesture}')

            # 根據手勢更新 color 和 luminance
            if gesture == 'turn_up':
                luminance += 1
            elif gesture == 'turn_down':
                luminance -= 1
            elif gesture == 'turn_right':
                color += 1
            elif gesture == 'turn_left':
                color -= 1

            # 印出目前color與luminance
            print(f'🎨 color: {color}, 💡 luminance: {luminance}')

        else:
            print("❌ 指令錯誤，請輸入 'start' 才能開始。")


def main():
    kgl.setLib()
    connect()
    startSetting()
    startLoop()

if __name__ == '__main__':
    main()
else:
     print("Dummy1 no working")