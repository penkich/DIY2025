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
    
    def set_sensitivity(self,value):
        value = 100 - value # valueは、０～１００で設定する（大きい値程、感度が高い）
        if not(0 <= value <= 100):
            print("value error")
            return -1
        else:
            sens_value = 500 + (value * 30) # 500（最高感度）～3500（最低感度）に変換
            if self.write_register(0x0034, sens_value):
                print(f"成功: 感度を{100-value}に設定しました。")
                
    def chk_rain(self):
        frame = bytearray([SLAVE_ADDR, 0x03, 0x00, 0x00, 0x00, 0x01])
        crc = crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
    
        while uart.any():
            uart.read()
        uart.write(frame)
    
        time.sleep_ms(150)
    
        if uart.any():
            response = uart.read()
            if len(response) >= 7:
                rcv_crc = (response[-1] << 8) | response[-2]
                cal_crc = crc16(response[:-2])
                if rcv_crc != cal_crc:
                    return None
                status_val = (response[3] << 8) | response[4]
                return status_val # 0:降ってない 1:降ってる
        return None

    def read_registers(self, start_addr, count):
        """
        複数レジスタを一括で読み出す
        0030h:加熱上限温度
        0031h:加熱開始温度x10（この温度以下なら加熱開始）
        0032h:加熱温度差（この温度差以上で加熱中止）
        0033h:発報までの時間（秒)
        0034H:発報感度（500-3500 低い程高感度）
        """
        frame = bytearray([
            SLAVE_ADDR, 0x03,
            (start_addr >> 8) & 0xFF, start_addr & 0xFF,
            (count >> 8) & 0xFF, count & 0xFF
        ])
        crc = crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
    
        while uart.any(): uart.read()
        uart.write(frame)
        time.sleep_ms(150)
    
        if uart.any():
            res = uart.read()
            if len(res) >= 5 + (count * 2):
                values = []
                for i in range(count):
                    idx = 3 + (i * 2)
                    val = (res[idx] << 8) | res[idx+1]
                    # 符号付き16bit処理
                    if val > 32767: val -= 65536
                    values.append(val)
                return values
        return None
