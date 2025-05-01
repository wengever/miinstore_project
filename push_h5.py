from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import FeatureMapReceiver
from model import initial_model, predict_result, ConvLSTMNet
import sys
import time
from datetime import datetime
from iottalkpy import dan

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
        name='wenggg',
        profile={
            "model": device_model,
            "is_sim": False,             # 是否為模擬裝置（可選）
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

# === 收集一筆手勢資料，更新color與luminance ===
def startLoop(R):
    global color, luminance

    buffer_rdi = []
    buffer_phd = []

    print("✅ 開始收集手勢資料...請稍後...")

    while len(buffer_rdi) < 50:
        res = R.getResults()
        if res is None:
            continue
        buffer_rdi.append(res[0])
        buffer_phd.append(res[1])
        print(f"📡 收集中: {len(buffer_rdi)}/50 幀", end='\r')

    # 預測手勢
    gesture = predict_result(buffer_rdi, buffer_phd, model)
    print(f'\n✅ 偵測到的手勢為: {gesture}')

    # 根據手勢更新 color 和 luminance
    if gesture == 'turn_up':
        luminance += 1
    elif gesture == 'turn_down':
        luminance -= 1
    elif gesture == 'turn_right':
        color += 1
    elif gesture == 'turn_left':
        color -= 1

    color = float(color)
    client.push('DummySensor-I', [color])
    print(datetime.now().isoformat(), f'→ 已推送：{color}')


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

color = 0
luminance = 0


if __name__ == '__main__':
    main()
