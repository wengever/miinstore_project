import time
import threading
from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import FeatureMapReceiver
from model import initial_model, predict_result, ConvLSTMNet
from iottalkpy.dan import NoData

# === IoTtalk Device Basic Info ===
api_url = 'https://miinstore.ncku.edu.tw/csm'
device_model = 'Dummy_Device'
idf_list = ['DummySensor-I']

# === 全域變數 ===
color = 0
luminance = 0
_ready_to_send = False
model = None
R = None
big_thread = None
hardware_initialized = False  # 用來判斷硬體是否已初始化
big_lock = threading.Lock()

# === IoTtalk 註冊成功後回呼 ===
def on_register(dan):
    print('✅ Device registered to miinstore successfully!')

# === 初始化硬體 ===
def setup_hardware():
    global model, R
    try:
        kgl.setLib()
        connect = ConnectDevice()
        connect.startUp()
        reset = ResetDevice()
        reset.startUp()
        print("✅ 硬體連線完成")

        SettingConfigs.setScriptDir("K60168-Test-00256-008-v0.0.8-20230717_60cm")
        ksp = SettingProc()
        ksp.startUp(SettingConfigs)
        print("✅ 硬體參數設定完成")

        model = initial_model()
        R = FeatureMapReceiver(chirps=32)
        R.trigger(chirps=32)
        time.sleep(0.5)
        print("✅ 硬體觸發完成")
        return True
    except Exception as e:
        print(f"❌ 硬體初始化失敗: {e}")
        return False

# === 收集手勢資料並預測 ===
def startLoop():
    global color, luminance, _ready_to_send, R, model

    buffer_rdi = []
    buffer_phd = []

    print("✅ 開始收集手勢資料...請稍後...")

    while len(buffer_rdi) < 100:
        res = R.getResults()
        if res is None:
            continue
        buffer_rdi.append(res[0])
        buffer_phd.append(res[1])
        print(f"📡 收集中: {len(buffer_rdi)}/100 幀", end='\r')

    gesture = predict_result(buffer_rdi, buffer_phd, model)
    print(f'\n✅ 偵測到的手勢為: {gesture}')

    if gesture == 'turn_up':
        luminance += 1
    elif gesture == 'turn_down':
        luminance -= 1
    elif gesture == 'turn_right':
        color += 1
    elif gesture == 'turn_left':
        color -= 1

    print(f'🎨 color: {color}, 💡 luminance: {luminance}')

    _ready_to_send = True

# === 背景互動循環，等待使用者輸入 'start' ===
def interactive_gesture_loop():
    global _ready_to_send

    print('# ======== 請輸入 start 開始收集手勢 =========')

    try:
        while True:
            user_input = input("\n請輸入 'start' 開始偵測(Ctrl+C 離開):")
            if user_input.strip().lower() == 'start':
                _ready_to_send = False
                startLoop()
            else:
                print("❌ 請輸入 'start'。")
    except KeyboardInterrupt:
        print("\n🛑 手動中斷手勢收集")

# === 大組合，只在第一次初始化硬體 ===
def big():
    global hardware_initialized
    if not hardware_initialized:
        if setup_hardware():
            hardware_initialized = True  # 只在成功初始化後標記
        else:
            print("❌ 硬體初始化失敗，無法開始互動")
            return
    # 不管有沒有新初始化，每次都跑互動等待
    interactive_gesture_loop()

# === IoTtalk 呼叫此函數以獲取資料並上傳 ===
def DummySensor_I():
    print("DummySensor_I() called")
    global big_thread

    if big_thread is None or not big_thread.is_alive():
        def run_big():
            with big_lock:
                big()
        big_thread = threading.Thread(target=run_big, daemon=True)
        big_thread.start()
        print("🚀 背景執行緒啟動成功 (初始化硬體＋等待start)")

    global _ready_to_send, color, luminance
    if _ready_to_send:
        print(f"✅ Sent: color={color}, luminance={luminance}")
        _ready_to_send = False
        return [float(color), float(luminance)]
    else:
        print("⏳ No new data to send")
        return NoData
