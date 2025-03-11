#!/usr/bin/env python3
# Example of accessing USB Audio devices produced by The Modal Shop (TMS)
#
# Devices include Digital Accelerometers and Digital Signal Conditioners
# Developed using Python 3.10.5 on Windows
#
# Device interface details are available in The Modal Shop manual
# MAN-0343 (USB Audio Interface Guide)
#
# Version 1.0 6/21/2022 TEC
#
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import datetime
from sys import platform
import time
import queue

# ※ PortAudio の初期化（TMSFindDevices() の前に必ず初期化する）
sd._initialize()

# define sensitivity for attached sensors if using digital signal conditioner
# Units are mV / engineering units, e.g. 100mV / g
# set to 0 to not apply sensitivity (to get volts)
#
# Digital Accelerometers like the 333D01 return g's.
# They can be scaled to m/s^2.
eu_sen = np.array([100.0, 100.0])
eu_units = ["g", "g"]

# Number of samples per block
blocksize = 1024  
# Sampling rate in Hz (48000, 44100, 32000, 22100, 16000, 11050, 8000)
samplerate = 48000  

# ループ回数（ブロック数）
num_blocks = 200
# 全サンプル数
total_samples = blocksize * num_blocks
# 信号取得時間とグラフの表示時間は全サンプル数に合わせる（秒）
display_time = total_samples / samplerate

# TMSFindDevices
def TMSFindDevices():
    models = ["485B", "333D", "633A", "SDC0"]
    
    if platform == "win32":  # Windowsの場合
        hapis = sd.query_hostapis()
        api_num = 0
        for api in hapis:
            if api['name'] == "Windows WDM-KS":
                break
            api_num += 1
    else:
        api_num = 0
    devices = sd.query_devices()
    dev_info = []
    dev_num = 0
    for device in devices:
        if device['hostapi'] == api_num:
            name = device['name']
            match = next((x for x in models if x in name), False)
            if match != False:
                loc = name.find(match)
                model = name[loc:loc+6]  # モデル番号抽出
                fmt = name[loc+7:loc+8]  # データ形式抽出
                serialnum = name[loc+8:loc+14]  # シリアル番号抽出
                if fmt == "2" or fmt == "3":
                    form = 1  # 電圧
                    sens = [int(name[loc+14:loc+21]), int(name[loc+21:loc+28])]
                    if fmt == "3":
                        sens[0] *= 20
                        sens[1] *= 20 
                    scale = np.array([8388608.0/sens[0],
                                      8388608.0/sens[1]],
                                     dtype='float32')
                    date = datetime.datetime.strptime(name[loc+28:loc+34], '%y%m%d')
                elif fmt == "1":
                    form = 0  # 加速度
                    sens = [int(name[loc+14:loc+19]), int(name[loc+19:loc+24])]
                    scale = np.array([855400.0/sens[0],
                                      855400.0/sens[1]],
                                     dtype='float32')
                    date = datetime.datetime.strptime(name[loc+24:loc+30], '%y%m%d')
                else:
                    raise Exception("Expecting 1, 2, or 3 format")
                dev_info.append({"device": dev_num,
                                 "model": model,
                                 "serial_number": serialnum,
                                 "date": date,
                                 "format": form,
                                 "sensitivity_int": sens,
                                 "scale": scale,
                                 })
        dev_num += 1
    if len(dev_info) == 0:
        raise Exception("No compatible devices found")
    return dev_info

# Callback function (別スレッドから呼ばれる)
def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(indata[:, :])  # キューにデータを送る

def time_ms():
    return int(time.monotonic_ns() / 1000000)

# デバイス検出
info = TMSFindDevices()
if len(info) > 1:
    print("Using first device found.")
dev = 0

# データスケーリング設定
units = ["Volts", "Volts"]
scale = info[dev]['scale']
if info[dev]['format'] == 1:
    for ch in range(len(scale)):
        if eu_sen[ch] != 0.0:
            scale[ch] *= 1.0 / (eu_sen[ch] / 1000.0)
            units[ch] = eu_units[ch]
elif info[dev]['format'] == 0:
    units = ["g", "g"]

q = queue.Queue()

# 全取得データを保持する配列を用意（1次元: チャンネル0 のみ表示する場合）
all_data = np.empty(total_samples, dtype='float32')
current_sample_index = 0

# x軸は全体の取得時間に合わせる
x_full = np.linspace(0, display_time, total_samples)

plt.ion()
figure, ax = plt.subplots()
plt.title("The Modal Shop " + info[dev]['model'], fontsize=20)
plt.xlabel("Time (S)")
plt.ylabel(units[0])
plt.axis([0, display_time, 0, 20])
first = 0

# with 構文を用いてストリーム作成（自動クローズ）
with sd.InputStream(
        device=info[dev]['device'], channels=2,
        samplerate=samplerate, dtype='float32', blocksize=blocksize,
        callback=callback) as stream:
    
    # num_blocks回ループして全サンプルを取得
    for i in range(num_blocks):
        data = q.get()  # 1ブロック分（1024サンプル）の取得
        sdata = data * scale
        block_data = sdata[:, 0]  # チャンネル0 のデータ
        
        # 取得したブロックを全体バッファに保存
        all_data[current_sample_index:current_sample_index+blocksize] = block_data
        current_sample_index += blocksize
        
        # 現在までの累積データをプロット
        if first == 0:
            # 初回はプロットオブジェクト作成
            line, = plt.plot(x_full[:current_sample_index], all_data[:current_sample_index])
            first = 1
        else:
            line.set_xdata(x_full[:current_sample_index])
            line.set_ydata(all_data[:current_sample_index])
        
        # y軸は現在のデータ範囲に合わせて調整
        ymin = np.min(all_data[:current_sample_index]) * 1.10
        ymax = np.max(all_data[:current_sample_index]) * 1.10
        plt.axis([0, display_time, ymin, ymax])
        figure.canvas.draw()
        figure.canvas.flush_events()

# with ブロック終了でストリームは自動クローズ
