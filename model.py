import torch
import torch.nn as nn
import numpy as np


# 模型參數
lstm_hidden_size = 128
lstm_num_layers = 2
model_path = r'mmwave_model_final.pth'
device = torch.device('cpu')

# 標籤對應表
label_list = ['background','focus', 'turn_left', 'turn_right', 'turn_up', 'turn_down', 'zoom_in', 'zoom_out']
label_map = {label: idx for idx, label in enumerate(label_list)}
label_map_invert = {idx: label for idx, label in enumerate(label_list)}

class ConvLSTMNet(nn.Module):
    def __init__(self, lstm_num_layers, lstm_hidden_size, fc_output_size=8):
        super(ConvLSTMNet, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 256, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(256, 512, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.flattened_size = 512 * 4 * 4
        self.lstm = nn.LSTM(
            input_size=self.flattened_size * 2,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_num_layers,
            batch_first=True
        )
        self.fc = nn.Linear(lstm_hidden_size, fc_output_size)

    def forward(self, rdi_map, phd_map):
        batch_size, timesteps, _, _ = rdi_map.size()

        h0 = torch.zeros(lstm_num_layers, batch_size, lstm_hidden_size).to(rdi_map.device)
        c0 = torch.zeros(lstm_num_layers, batch_size, lstm_hidden_size).to(rdi_map.device)

        combined_features = []
        for t in range(timesteps):
            rdi_frame = rdi_map[:, t, :, :].unsqueeze(1)
            rdi_conv_output = self.conv(rdi_frame).view(batch_size, -1)

            phd_frame = phd_map[:, t, :, :].unsqueeze(1)
            phd_conv_output = self.conv(phd_frame).view(batch_size, -1)

            combined_feature = torch.cat((rdi_conv_output, phd_conv_output), dim=1)
            combined_features.append(combined_feature)

        combined_features = torch.stack(combined_features, dim=1)
        lstm_out, _ = self.lstm(combined_features, (h0, c0))
        lstm_out_last = lstm_out[:, -1, :]
        out = self.fc(lstm_out_last)
        return out

def initial_model():
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

