from machine import Pin, I2C, SoftI2C, PWM, Timer, SPI
import os
import sdcard
import time
LED = Pin(25, Pin.OUT) # picoボード上のLED
LED.value(1) # LED点灯
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8))
spi = SPI( 0, baudrate = 100000, sck  = Pin(18), mosi = Pin(19), miso = Pin(16))
cs = Pin(17, mode=Pin.OUT, value=1)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, '/sd')

sw = Pin(2, Pin.IN) # ロータリーエンコーダー付属スイッチ　ON:0, OFF:1

from machine_i2c_lcd import I2cLcd
addr = i2c.scan()[1]
a = I2cLcd(i2c, addr, 2, 16)
a.putstr_kana("ニュウリョクシテクダサイ")

import onewire, ds18x20
datPin = machine.Pin(28) # 温度センサーのデーターピン
ds = ds18x20.DS18X20(onewire.OneWire(datPin))

setTemp = 30
memTemp = []

def chkTemp(timer):
    global Temp
    try:
        rom = ds.scan()[0] # １つが前提
    except:
        a.move_to(0, 1)
        a.putstr_kana("センサーエラー")
        return
    rom = ds.scan()[0]
    ds.convert_temp()
    Temp = ds.read_temp(rom)
    a.move_to(0, 1)
    a.putstr_kana(f"{Temp:2.1f}℃")
    memTemp.append(Temp)
    if len(memTemp) > 10:
        memTemp.pop(0)
        #a.lcd_print(f"{Temp:2.1f}/{setTemp:2.1f}℃ {diff}")
tim = Timer(period=1000, mode=Timer.PERIODIC, callback=chkTemp)

# ロータリーエンコーダー（割り込み仕様）
from rotary_irq_esp import RotaryIRQ

r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val=9, 
        max_val=60, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)

val_old = r.value()


from machine import Pin, I2C
import mcp23017 # Ｉ／Ｏエキスパンダー
mcp = mcp23017.MCP23017(i2c, 0x20)

"""
# list interface
mcp[0].input()
mcp[1].input(pull=1)
mcp[1].value()
"""

SeiHanSW = Pin(15, Pin.IN, Pin.PULL_UP) # 正反切り替えSW
manSW0 = Pin(5, Pin.IN)
manSW1 = Pin(6, Pin.IN)
manSW2 = Pin(7, Pin.IN)
manSW3 = Pin(10, Pin.IN)
manSWs = [manSW0, manSW1, manSW2, manSW3]

manExe0 = Pin(11, Pin.IN, Pin.PULL_UP)
manExe1 = Pin(12, Pin.IN, Pin.PULL_UP)
manExe2 = Pin(13, Pin.IN, Pin.PULL_UP)
manExe3 = Pin(14, Pin.IN, Pin.PULL_UP)
manExes = [manExe0, manExe1, manExe2, manExe3]

"""
while True:
    a.move_to(0, 1)
    val_new = r.value()
    if val_old != val_new:
        val_old = val_new
        if val_new >= 60:
            r.set(59)
        if val_new <= 10:
            r.set(10)
        a.putstr_kana(f"{val_new:02d}℃")
"""
rLEDs = [mcp[0], mcp[1], mcp[2], mcp[3]]
gLEDs = [mcp[4], mcp[5], mcp[6], mcp[7]]
for rLED in rLEDs:
    rLED.output()
for gLED in gLEDs:
    gLED.output()


mFs = [mcp[8], mcp[10], mcp[12], mcp[14]] # モーター正転指示
mRs = [mcp[9], mcp[11], mcp[13], mcp[15]] # モーター反転指示

for mF in mFs:
    mF.output()
    mF.value(0)
for mR in mRs:
    mR.output()
    mR.value(0)

while True:
    if SeiHanSW.value() == 1: # 正転の場合
        for i in range(4):
            if manSWs[i].value() == 1: # マニュアルの場合
                if manExes[i].value() == 0:
                    gLEDs[i].value(1) # 緑を点灯
                    time.sleep(0.1)
                    mFs[i].value(1) # 正転を指示
                else:
                    gLEDs[i].value(0)
                    time.sleep(0.1)
                    mFs[i].value(0)
    else: # 反転の場合
        for i in range(4):
            if manSWs[i].value() == 1: # マニュアルの場合
                if manExes[i].value() == 0:
                    rLEDs[i].value(1) # 赤を点灯
                    time.sleep(0.1)
                    mRs[i].value(1) # 反転を指示
                else:
                    rLEDs[i].value(0)
                    time.sleep(0.1)
                    mRs[i].value(0)
