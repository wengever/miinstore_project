import h5py
import sys
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
        profile={
            "model": device_model,
            "is_sim": False,
        }
    )   
    print('[✔] 裝置註冊成功')
except Exception as e:
    print('[✘] 註冊失敗:', e)
    sys.exit(1)

# ====== 資料來源 (.h5) ======
h5_file_path = r'C:\Users\Wengg\Desktop\Collect_RDI\Collect_RDI\Record\RDIPHD\turn_up\my_file.h5'
current_index = 0

# ====== 手動推送一筆資料 ======
def push_next_frame():
    global current_index
    try:
        with h5py.File(h5_file_path, 'r') as h5_file:
            ds1 = h5_file['DS1']
            if current_index < ds1.shape[-1]:
                ds1_data = ds1[0, :, :, current_index]
                current_index += 1
                data_mean = float(ds1_data.mean())
                client.push('DummySensor-I', [data_mean])
                print(datetime.now().isoformat(), f'→ 已推送：{data_mean}')
            else:
                print('📦 沒有更多資料了')
                return False
    except Exception as e:
        print(f'讀取錯誤或推送失敗: {e}')
        return False
    return True

# ====== 主程式互動 ======
if __name__ == '__main__':
    try:
        while True:
            cmd = input('輸入 [push] 推送一筆資料，或 [exit] 離開：').strip().lower()
            if cmd == 'push':
                if not push_next_frame():
                    break
            elif cmd == 'exit':
                break
    except KeyboardInterrupt:
        print('\n🛑 中斷操作（Ctrl+C）')
    finally:
        try:
            client.deregister()
            print('✅ 已解除裝置註冊')
        except Exception as e:
            print('⚠️ 解除註冊失敗:', e)
