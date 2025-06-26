import sys
import time
from datetime import datetime
from iottalkpy import dan

# ====== 建立 DAN 客戶端 ======
client = dan.Client()

# ====== 設定資訊 ======
device_model = 'Dummy_Device'
idf_list = [('DummySensor-I', ['list'])] # 注意格式是 tuple: (name, unit)
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


# ====== 主程式互動 ======
if __name__ == '__main__':
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n🛑 中斷操作（Ctrl+C）')
    finally:
        try:
            client.deregister()
            print('✅ 已解除裝置註冊')
        except Exception as e:
            print('⚠️ 解除註冊失敗:', e)
