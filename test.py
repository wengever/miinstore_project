import random
import h5py
import json

from iottalkpy.dan import NoData

### The registeration api url, you can use IP or Domain.
api_url = 'https://miinstore.ncku.edu.tw/csm'  # default
# api_url = 'http://localhost/csm'  # with URL prefix
# api_url = 'http://localhost:9992/csm'  # with URL prefix + port

### [OPTIONAL] If not given or None, server will auto-generate.
# device_name = 'Dummy_Test'

### [OPTIONAL] If not given or None, DAN will register using a random UUID.
### Or you can use following code to use MAC address for device_addr.
# from uuid import getnode
# device_addr = "{:012X}".format(getnode())
# device_addr = "..."

### [OPTIONAL] If the device_addr is set as a fixed value, user can enable
### this option and make the DA register/deregister without rebinding on GUI
# persistent_binding = True

### [OPTIONAL] If not given or None, this device will be used by anyone.
# username = 'myname'

### The Device Model in IoTtalk, please check IoTtalk document.
device_model = 'Dummy_Device'

### The input/output device features, please check IoTtalk document.
idf_list = ['DummySensor-I']
odf_list = ['DummyControl-O']

### Set the push interval, default = 1 (sec)
### Or you can set to 0, and control in your feature input function.
push_interval = 1  # global interval
interval = {
    'Dummy_Sensor': 3,  # assign feature interval
}


def on_register(dan):
    print('register successfully so good')

h5_file_path = 'C:\\Users\\Wengg\\Desktop\\Collect_RDI\\Collect_RDI\\Record\\RDIPHD\\turn_up\\my_file.h5'
current_index = 0  # 用來記錄當前索引

def DummySensor_I():
    global current_index
    print("DummySensor_I() called")  # 確認函數被呼叫
    try:
        with h5py.File(h5_file_path, 'r') as h5_file:
            ds1 = h5_file['DS1']  # 讀取 DS1 資料集
            
            print(f"Current index: {current_index}, DS1 shape: {ds1.shape}")
            
            if current_index < ds1.shape[-1]:  # 確保索引在範圍內
                ds1_data = ds1[0, :, :, current_index]  # 提取當前索引的數據
                current_index += 1  # 移動到下一個索引
                
                # 在終端列印數據來檢查
                print(f"Sending DS1 data mean: {ds1_data.mean()}")
                return float(ds1_data.mean())  # 傳回數據的均值作為範例
                
        
                
            else:
                print("No more data to send.")
                return NoData  # 沒有更多數據時返回 NoData
    except (KeyError, OSError, ValueError) as e:
        print(f"Error reading .h5 file: {e}")
        return NoData



def DummyControl_O(data: list):
    print(str(data[0]))

# 手動調用 DummySensor_I() 來測試
if __name__ == "__main__":
    print(DummySensor_I())  # 測試函數是否能正常工作
else:
     print("no working")