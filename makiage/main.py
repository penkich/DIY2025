from machine import Pin, I2C, SoftI2C, PWM, Timer, SPI
import os, sdcard, time
LED = Pin(25, Pin.OUT) # picoボード上のLED
LED.value(1) # LED点灯
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8))
spi = SPI( 0, baudrate = 100000, sck  = Pin(18), mosi = Pin(19), miso = Pin(16))
cs = Pin(17, mode=Pin.OUT, value=1)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, '/sd')

sw = Pin(2, Pin.IN) # ロータリーエンコーダー付属スイッチ　ON:0, OFF:1

cnt = 0

def counter(c):
    global cnt
    cnt += 1

tim = Timer()
tim.init(period=1000,mode=tim.PERIODIC,callback = counter)
tim.deinit()


from machine_i2c_lcd import I2cLcd
addr = i2c.scan()[1]
lcd = I2cLcd(i2c, addr, 2, 16)
#lcd.putstr_kana("ニュウリョクシテクダサイ")

"""
レベルバーに使うフォントを３つ登録
"""
charmap = [3, 3, 3, 3, 3, 3, 3, 0]
lcd.custom_char(0, charmap)
charmap = [24, 24, 24, 24, 24, 24, 24, 0]
lcd.custom_char(1, charmap)
charmap = [27, 27, 27, 27, 27, 27, 27, 0]
lcd.custom_char(2, charmap)

def levelbar(level):
    if level == 0:
        lcd.putstr("   ")
    if level == 1:
        lcd.putstr(chr(1))
        lcd.putstr("  ")
    if level == 2:
        lcd.putstr(chr(2))
        lcd.putstr("  ")
    if level == 3:
        lcd.putstr(chr(2))
        lcd.putstr(chr(1))
        lcd.putstr(" ")
    if level == 4:
        lcd.putstr(chr(2))
        lcd.putstr(chr(2))
        lcd.putstr(" ")
    if level == 5:
        lcd.putstr(chr(2))
        lcd.putstr(chr(2))
        lcd.putstr(chr(1))
    if level >5 or level <0:
        lcd.putstr("   ")

import onewire, ds18x20
datPin = machine.Pin(28) # 温度センサーのデーターピン
ds = ds18x20.DS18X20(onewire.OneWire(datPin))
try:
    rom = ds.scan()[0] # １つが前提
except:
    lcd.move_to(0, 1)
    lcd.putstr_kana("センサーエラー")
ds.convert_temp()
Temp = ds.read_temp(rom)
setTemp = 30
memTemp = []

def chkTemp(timer):
    global Temp
    ds.convert_temp()
    Temp = ds.read_temp(rom)


tim = Timer(period=1000, mode=Timer.PERIODIC, callback=chkTemp)

# 4つのモーターのオブジェクトを生成
import mlib
m0 = mlib.Motor(0)
m1 = mlib.Motor(1)
m2 = mlib.Motor(2)
m3 = mlib.Motor(3)

while True:
    time.sleep(1)
    lcd.move_to(0, 0)
    time.sleep(0.1)
    lcd.putstr("1")
    levelbar(int((m0.pos / m0.posmax)*5))
    lcd.putstr("2")
    levelbar(4)
    lcd.putstr("3")
    levelbar(1)
    lcd.putstr("4")
    levelbar(5)    
    try:
        lcd.move_to(0, 1)
        time.sleep(0.1)
        lcd.putstr_kana(f"{Temp:2.1f} / {m0.temp}℃")
        memTemp.append(Temp)
        if len(memTemp) > 100:
            memTemp.pop(0)
    except:
        print("Err")
        #a.lcd_print(f"{Temp:2.1f}/{setTemp:2.1f}℃ {diff}")
"""

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
"""
# list interface
mcp[0].input()
mcp[1].input(pull=1)
mcp[1].value()
"""
"""
LimitSW1U = Pin(21, Pin.IN) # 注意（2番めリレー動作）
LimitSW1D = Pin(20, Pin.IN) # 注意（1番めリレー動作）

SeiHanSW = Pin(15, Pin.IN) # 正反切り替えSW
manSW0 = mcp[4] # mcp[4] # GPA4
manSW1 = mcp[5] # mcp[5] # GPA5
manSW2 = mcp[6] # mcp[6] # GPA6
manSW3 = mcp[7] # mcp[7] # GPA7
manSW0.input()
manSW1.input()
manSW2.input()
manSW3.input()
manSWs = [manSW0, manSW1, manSW2, manSW3]

mcp[0].input() # GPA0
mcp[1].input() # GPA1
mcp[2].input() # GPA2
mcp[3].input() # GPA3
manExe0 = mcp[0]
manExe1 = mcp[1]
manExe2 = mcp[2]
manExe3 = mcp[3]
manExes = [manExe0, manExe1, manExe2, manExe3]
"""
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

flag = True
x=0
while True:
    if SeiHanSW.value() == 1: # 正転の場合
        for i in range(4):
            if manSWs[i].value() == 1: # マニュアルの場合
                if manExes[i].value() == 0:
                    gLEDs[i].value(1) # 緑を点灯
                    time.sleep(0.2)
                    mFs[i].value(1) # 正転を指示
                    if flag:
                        print("seiten")
                        tim.init(period=100,mode=tim.PERIODIC,callback = counter)
                        flag = False
                    if LimitSW1U.value() == 1:
                        print(f"U{i} {x} cnt={cnt}")
                        if x > 1:
                            tim.deinit()
                            print("Limit")
                            break
                        x+=1
                else:
                    gLEDs[i].value(0)
                    time.sleep(0.2)
                    mFs[i].value(0)
    else: # 反転の場合
        for i in range(4):
            if manSWs[i].value() == 1: # マニュアルの場合
                if manExes[i].value() == 0:
                    rLEDs[i].value(1) # 赤を点灯
                    time.sleep(0.1)
                    mRs[i].value(1) # 反転を指示
                    if flag:
                        print("hanten")
                        tim.init(period=100,mode=tim.PERIODIC,callback = counter)
                        flag = False
                    if LimitSW1D.value() == 1:
                        print(f"D{i} {x} cnt={cnt}")
                        if x > 1:
                            tim.deinit()
                            print("Limit")
                            break
                        x+=1
                else:
                    rLEDs[i].value(0)
                    time.sleep(0.1)
                    mRs[i].value(0)
"""

