import time
from machine import UART, Pin

BAUDRATE = 4800      
UART_NUM = 0         # GP4(TX), GP5(RX) は UART1
                     # GP0(TX), GP1(RX) は UART0
SLAVE_ADDR = 0x01    # センサーのデフォルトアドレス
# ===================================================

# UARTの初期化 (自動フロー制御モジュールを想定しているためDE/REピン制御はなし)
uart = UART(UART_NUM, baudrate=BAUDRATE, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

class Rainsensor:
    def __init__(self):
        self.heater_default()

    def write_register(self, reg_addr, value):
        """指定したレジスタアドレスに値を書き込む汎用関数"""
        frame = bytearray([
            SLAVE_ADDR,
            0x06,       # Write Single Register
            (reg_addr >> 8) & 0xFF,
            reg_addr & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF
        ])
    
        crc = crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
    
        while uart.any():
            uart.read()
        uart.write(frame)
        time.sleep_ms(150)
    
        if uart.any():
            response = uart.read()
            if len(response) == 8 and response[:-2] == frame[:-2]:
                return True
        return False

    def heater_on(self, temp):
        if self.write_register(0x0030, 70):
            print("成功: ヒーター上限温度を 70℃ に設定しました。")
        else:
            print("失敗: 開始温度の設定エラー")
    
        if self.write_register(0x0031, temp * 10):
            print(f"成功: ヒーター開始温度を {temp}℃ に設定しました。")
        else:
            print("失敗: 開始温度の設定エラー")

        # 2. ヒーター停止温度差 (0x0032) を「10℃」に設定（つまり50℃で停止）
        if self.write_register(0x0032, 5):
            print("成功: ヒーター停止温度差を 5℃ に設定しました。")
        else:
            print("失敗: 停止温度差の設定エラー")

    def heater_default(self):
        if self.write_register(0x0030, 35):
            print("成功: ヒーター上限温度を 35℃ に設定しました。")
        else:
            print("失敗: 開始温度の設定エラー")
    
        if self.write_register(0x0031, 15):
            print("成功: ヒーター開始温度を 15℃ に設定しました。")
        else:
            print("失敗: 開始温度の設定エラー")

        # 2. ヒーター停止温度差 (0x0032) を「10℃」に設定（つまり50℃で停止）
        if self.write_register(0x0032, 5):
            print("成功: ヒーター停止温度差を 5℃ に設定しました。")
        else:
            print("失敗: 停止温度差の設定エラー")
