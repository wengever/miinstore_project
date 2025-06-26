from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import FeatureMapReceiver
from model import initial_model, predict_result, ConvLSTMNet
import time
from datetime import datetime
from iottalkpy import dan

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


def startLoop(R):

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


if __name__ == '__main__':
    main()