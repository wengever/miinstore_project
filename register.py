import requests
import pytz
from datetime import datetime

from iottalkpy.dan import NoData

### The registeration api url, you can use IP or Domain.
api_url = 'https://miinstore.ncku.edu.tw/csm'  # default
mongodb_apiurl = 'https://miinstore.ncku.edu.tw/mongodb/data'
# api_url = 'http://localhost/csm'  # with URL prefix
# api_url = 'http://localhost:9992/csm'  # with URL prefix + port

### [OPTIONAL] If not given or None, server will auto-generate.
device_name = 'MongoDB_MMWave'

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
device_model = 'MongoDB'

### The input/output device features, please check IoTtalk document.
odf_list = ['Data-O']

### Set the push interval, default = 1 (sec)
### Or you can set to 0, and control in your feature input function.
push_interval = 0  # global interval
#interval = {
#    'Dummy_Sensor': 3,  # assign feature interval
#}


def on_register(dan):
    print('register successfully')


def Data_O(data_):
    tw = pytz.timezone('Asia/Taipei')
    local_time = datetime.now(tz=tw)

    # 將時間分成兩行：日期 + 時間
    formatted_time = local_time.strftime("%Y-%m-%d\n%H:%M:%S.%f")

    data = {
        "data": data_,
        "timestamp": formatted_time
    }
    try:
        response = requests.post(mongodb_apiurl, json=data)
        if response.status_code == 201:
            print("資料成功寫入 MongoDB！")
            print("回傳內容：", response.json())
        else:
            print("寫入失敗，狀態碼：", response.status_code)
            print("錯誤訊息：", response.text)
    except requests.exceptions.RequestException as e:
        print("請求失敗：", e)
