import base64
import zlib
from KKT_Module.ksoc_global import kgl
from KKT_Module.Configs import SettingConfigs
from KKT_Module.SettingProcess.SettingProccess import SettingProc, ConnectDevice, ResetDevice
from KKT_Module.DataReceive.DataReciever import RawDataReceiver, HWResultReceiver, FeatureMapReceiver
import time
import numpy as np
import requests
import json

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

def compress_and_encode_json(data):
    # Convert the data dictionary to a JSON string
    json_data = json.dumps(data)
    
    # Compress the JSON string using zlib
    compressed_data = zlib.compress(json_data.encode('utf-8'))
    
    # Convert to base64 format
    base64_encoded = base64.b64encode(compressed_data)
    
    # Return the base64 encoded string
    return base64_encoded.decode('utf-8')

def decode_and_decompress_base64(base64_encoded):
    # Decode the base64 encoded string
    compressed_data = base64.b64decode(base64_encoded)
    
    # Decompress the data using zlib
    decompressed_data = zlib.decompress(compressed_data)
    
    # Convert the decompressed byte data back into a JSON string
    json_data = decompressed_data.decode('utf-8')
    
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_data)
    
    return data

def collectGestures(R):

    frame_count = 0
    max_frames = 100

    while frame_count < max_frames:
        res = R.getResults()
        if res is None:
            continue

        frame_count += 1
        print(f'📸 幀號: {frame_count}')

        rdi_map = np.array(res[0])
        phd_map = np.array(res[1])

        # Create a dictionary to hold the frame data
        data = {
            "frame": frame_count,
            "RDI": rdi_map.tolist(),
            "PHD": phd_map.tolist()
        }

        # Compress and encode the JSON data
        compressed_data_base64 = compress_and_encode_json(data)

        print(f"📊 compressed data (Base64) = \n{compressed_data_base64}")

        # Example: let's say we already have a base64 encoded string from the previous function
        base64_encoded_data = compressed_data_base64

        # Decode and decompress the data
        original_data = decode_and_decompress_base64(base64_encoded_data)

        # Print the original JSON data
        print("Original JSON data:", original_data)

    print("✅ 手勢收集完畢，共收集 100 幀。")

def startLoop():
    R = FeatureMapReceiver(chirps=32)       # Receiver for getting RDI PHD map
    R.trigger(chirps=32)                    # Trigger receiver before getting the data
    time.sleep(0.5)
    print('# ======== 開始收集手勢 ===========')

    while True:
        user_input = input("\n請輸入 'start' 開始手勢收集（或按 Ctrl+C 結束程式）：")
        if user_input.strip().lower() == 'start':
            collectGestures(R)
        else:
            print("❌ 指令錯誤，請輸入 'start' 才能開始收集手勢。")

def main():
    kgl.setLib()
    connect()
    startSetting()
    startLoop()

if __name__ == '__main__':
    main()
