import torch
import torch.nn as nn
import numpy as np
import sys



# 模型參數
lstm_hidden_size = 128
lstm_num_layers = 2
fc_output_size = 5 
model_path = r'mmwave_model_r1.pth'
device = torch.device('cpu')

# 標籤對應表
label_list = ['background', 'turn_left', 'turn_right', 'turn_up', 'turn_down']
label_map = {label: idx for idx, label in enumerate(label_list)}
label_map_invert = {idx: label for idx, label in enumerate(label_list)}

class ConvLSTMNet(nn.Module):
    def __init__(self, lstm_num_layers, lstm_hidden_size, fc_output_size):
        super(ConvLSTMNet, self).__init__()
        
        # 定義卷積層
        # RDI & PHD 卷積
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),  # 16x16 feature map
            
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),  # 8x8 feature map
            
            nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)  # 4x4 feature map
        )
         
        # 計算卷積後輸出的特徵圖大小
        # 最終大小為 4x4 , 然後有512個通道
        self.flattened_size = 512 * 4 * 4
        
        # 定義 LSTM 層
        self.lstm = nn.LSTM(
            input_size = self.flattened_size * 2, 
            hidden_size = lstm_hidden_size, 
            num_layers = lstm_num_layers, 
            batch_first = True
        )
        
        # 定義全連接層
        self.fc = nn.Linear(lstm_hidden_size, fc_output_size)
        
    def forward(self, rdi_map, phd_map):
        # 批次大小,  幀數 , 32, 32
        batch_size, timesteps, _, _ = rdi_map.size()
        
        # 初始化 LSTM 隱藏狀態 並確保他的device跟輸入一樣
        h0 = torch.zeros(lstm_num_layers, batch_size, lstm_hidden_size).to(rdi_map.device)
        c0 = torch.zeros(lstm_num_layers, batch_size, lstm_hidden_size).to(rdi_map.device)
        
        # 結合兩個Map的卷積結果
        combined_features = []
        
        for t in range(timesteps):
            rdi_frame = rdi_map[:, t, :, :].unsqueeze(1)  # (batch_size, 1, 32, 32)
            rdi_conv_output = self.conv(rdi_frame)  # (batch_size, 64, 8, 8)
            rdi_conv_output = rdi_conv_output.view(batch_size, -1)  # 攤平 (batch_size, 64*8*8)
            
            phd_frame = phd_map[:, t, :, :].unsqueeze(1)
            phd_conv_output = self.conv(phd_frame)  # (batch_size, 64, 8, 8)
            phd_conv_output = phd_conv_output.view(batch_size, -1)  # 展平 (batch_size, 64*8*8)
            
            # 將兩個卷積輸出並在一起
            combined_feature = torch.cat((rdi_conv_output, phd_conv_output), dim=1)  # (batch_size, flattened_size*2)
            combined_features.append(combined_feature)
        
        # 把所有時間點的特徵結合成一個序列 (batch_size, timesteps, flattened_size*2)
        combined_features = torch.stack(combined_features, dim=1)

        # 把特徵序列輸入到LSTM中
        lstm_out, _ = self.lstm(combined_features, (h0, c0))
        
        # 取 LSTM 最後的輸出
        lstm_out_last = lstm_out[:, -1, :]
        

        out = self.fc(lstm_out_last)
        
        return out

def initial_model():
    sys.modules['__main__'].ConvLSTMNet = ConvLSTMNet
    
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    return model

def predict_result(rdi_map, phd_map, model):
    rdi_map = torch.tensor(np.array(rdi_map), dtype=torch.float32).unsqueeze(0).to(device)
    phd_map = torch.tensor(np.array(phd_map), dtype=torch.float32).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(rdi_map, phd_map)
        _, predicted_class = torch.max(output, 1)
        print(output)

    predicted_label = label_map_invert[predicted_class.item()]
    return predicted_label

