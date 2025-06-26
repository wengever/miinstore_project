import h5py

# 設定 .h5 檔案的路徑
h5_file_path = 'C:\\Users\\Wengg\\Desktop\\Collect_RDI\\Collect_RDI\\Record\\RDIPHD\\turn_up\\my_file.h5'

# 打開 .h5 檔案並列出結構
with h5py.File(h5_file_path, 'r') as h5_file:
    def print_structure(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"Dataset: {name}, Shape: {obj.shape}, Data type: {obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"Group: {name}")

    h5_file.visititems(print_structure)
