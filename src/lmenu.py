from machine import Pin, I2C, SoftI2C, PWM, Timer, SPI, RTC
import os, sdcard, time
from machine_i2c_lcd import I2cLcd
from rotary_irq_esp import RotaryIRQ
# ロータリーエンコーダー（割り込み仕様）
#i2c = I2C(0, scl=Pin(9), sda=Pin(8))
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq = 100000)
import json
import lcd_cfg
f = open("lcd_cfg.py")
lcd_dic = json.loads(f.read())
f.close()
#addr = lcd_dic['addr']
addr = i2c.scan()[1] # lcdの種類によってアドレス異なるため、lcd_cfg.py での設定をやめた。
char = lcd_dic['char']
line = lcd_dic['line']


lcd = I2cLcd(i2c, addr, line, char)
#lcd = I2cLcd(i2c, addr, 4, 16) # 4行16文字
sw = Pin(2, Pin.IN) # ロータリーエンコーダー付属スイッチ　ON:0, OFF:1

rtc = RTC()
rtc.datetime((2017, 8, 23, 2, 12, 48, 0, 0))  # 指定の日時(2017/8/23 1:12:48)を設定
rtc.datetime() # 日時を取得

"""
レベルバーに使うフォントを３つ登録
"""
charmap = [3, 3, 3, 3, 3, 3, 3, 0]
lcd.custom_char(0, charmap)
charmap = [24, 24, 24, 24, 24, 24, 24, 0]
lcd.custom_char(1, charmap)
charmap = [27, 27, 27, 27, 27, 27, 27, 0]
lcd.custom_char(2, charmap)

class Menu:
    def __init__(self):
        self.r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val = 0,
        max_val = 1, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)
        
    def set_span(self, min_val, max_val):
        return RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val = min_val,
        max_val = max_val, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)

    def yn_sentaku(self,text, offset=0):
        self.r = self.set_span(0, 1)
        lcd.blink_cursor_on()
        lcd.putstr_kana(text + "? Y/N")
        lcd.move_to(len(text)+2+offset, 0)
        val_new = 0
        val_old = 0
        while True:
            if sw.value() == 0:
                lcd.clear()
                lcd.move_to(0,0)
                return val_new
            val_new = self.r.value()    
            if val_old != val_new:
                val_old = val_new
                lcd.move_to(val_new * 2 + len(text)+2+offset, 0)

    def val_sentaku(self, min_val, max_val, offset_val, offset, text, keta):
        time.sleep(0.5)
        lcd.hide_cursor()
        lcd.putstr_kana(f"{text}")
        lcd.move_to(offset,0)
        lcd.putstr_kana(f"{offset_val:{keta}d}")
        self.r = self.set_span(min_val, max_val)
        self.r.set(offset_val)
        val_old = self.r.value()
        while True:
            val_new = self.r.value()
            if val_old != val_new:
                val_old = val_new
                lcd.move_to(offset,0)
                lcd.putstr(f'{self.r.value():{keta}d}')
            if sw.value() == 0:
                return val_new

    def vals_sentaku(self, params):
        # params [(min_val, max_val, offset),(min_val, max_val, offset), ...]
        lcd.hide_cursor()
        tmp = []
        for param in params:
            time.sleep(0.5)
            self.r = self.set_span(param[0], param[1])
            val_old = self.r.value()
            while True:
                val_new = self.r.value()
                if val_old != val_new:
                    val_old = val_new
                    lcd.move_to(param[2],0)
                    lcd.putstr(f'{self.r.value():02d}')
                if sw.value() == 0:
                    tmp.append(self.r.value())
                    break
        return tmp

    def moji_sentaku(self):
        mojis = [chr(x) for x in range(0x20, 0x7f)]
        mojis.append(chr(2))
        lcd.hide_cursor()
        self.r = self.set_span(0, len(mojis)-1)
        self.r.set(0x61)
        val_old = self.r.value()
        i = 0
        lcd.move_to(i, 0)
        tmp = ''
        while True:
            val_new = self.r.value()
            if val_old != val_new:
                val_old = val_new
                lcd.move_to(i, 0)
                lcd.putstr(f'{mojis[self.r.value()]}')
            if sw.value() == 0:
                if self.r.value() == len(mojis)-1:
                    print("end")
                    return tmp
                lcd.putstr(f'{mojis[self.r.value()]}')
                tmp += mojis[self.r.value()]
                time.sleep(0.5)
                i += 1

    def line_sentaku(self, items, posx=0, posy=0):
        self.r = self.set_span(0, len(items)-1)
        lcd.blink_cursor_on()
        lcd.move_to(posx, posy)
        lcd.putstr_kana(items[0][:16])
        lcd.move_to(posx, posy)
        val_new = 0
        val_old = 0
        while True:
            if sw.value() == 0:
                lcd.move_to(posx,posy)
                return items[val_new]
            val_new = self.r.value()    
            if val_old != val_new:
                val_old = val_new
                lcd.putstr(" " * 16)
                lcd.move_to(posx,posy)
                lcd.putstr(items[val_new][:16])
                lcd.move_to(posx,posy)

    def next(self, items):
        n = len(items)
        self.r = self.set_span(0, n-1)
        lcd.blink_cursor_on()
        lcd.move_to(0, 1)
        for i in range(n):
            lcd.putstr(items[i]+" ")
        lcd.move_to(0, 1)
        val_new = 0
        val_old = 0
        while True:
            if sw.value() == 0:
                lcd.clear()
                lcd.move_to(0,0)
                return val_new
            val_new = self.r.value()    
            if val_old != val_new:
                val_old = val_new
                lcd.move_to(0,1)
                lcd.move_to((len(items[val_new])+1) * val_new, 1)

    def print(self, text):
        lcd.putstr_kana(text)
    
    def pos(self, pos, line):
        lcd.move_to(pos, line)
        
    def blink_off(self):
        lcd.blink_cursor_off()

    def blink_on(self):
        lcd.blink_cursor_on()

    def hide_cursor(self):
        lcd.hide_cursor()

    def show_cursor(self):
        lcd.show_cursor()

    def backlight_off(self):
        lcd.backlight_off()

    def backlight_on(self):
        lcd.backlight_on()

    def clear(self):
        lcd.clear()

    def move_to(self,n,m):
        lcd.move_to(n,m)
        
    def levelbar(self,level):
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
        if level == 6:
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
        if level == 7:
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(1))
        if level == 8:
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
        if level == 9:
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(1))
        if level == 10:
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))
            lcd.putstr(chr(2))            
        if level >10:
            lcd.putstr("+++")
        if level <0:
            lcd.putstr("---")

    def disp_level2(self,l1,l2):
        lcd.move_to(0,0)
        lcd.putstr("1")
        lcd.move_to(1,0)
        self.levelbar(l1)
        lcd.move_to(8,0)
        lcd.putstr("2")
        lcd.move_to(9,0)
        self.levelbar(l2)

    def disp_2(self,l1,l2):
        lcd.move_to(0,0)
        lcd.putstr("1")
        if l1 >=0:
            lcd.putstr(f": {l1:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(8,0)
        lcd.putstr("2")
        if l2 >=0:
            lcd.putstr(f": {l2:3d}%")
        else:
            lcd.putstr(": ----")

    def disp_level(self,l1,l2,l3,l4):
        lcd.move_to(0,0)
        lcd.putstr("1")
        lcd.move_to(1,0)
        self.levelbar(l1)
        lcd.putstr("2")
        lcd.move_to(5,0)
        self.levelbar(l2)
        lcd.putstr("3")
        lcd.move_to(9,0)
        self.levelbar(l3)
        lcd.putstr("4")
        lcd.move_to(13,0)
        self.levelbar(l4)

    def disp_level6(self,l1,l2,l3,l4,l5,l6):
        lcd.move_to(0,0)
        lcd.putstr("1")
        self.levelbar(l1)
        lcd.move_to(8,0)
        lcd.putstr("2")
        self.levelbar(l2)
        lcd.move_to(0,1)
        lcd.putstr("3")
        self.levelbar(l3)
        lcd.move_to(8,1)
        lcd.putstr("4")
        self.levelbar(l4)
        lcd.move_to(0,2)
        lcd.putstr("5")
        self.levelbar(l5)
        lcd.move_to(8,2)
        lcd.putstr("6")
        self.levelbar(l6)
        lcd.move_to(0,3)

    def disp_6(self,l1,l2,l3,l4,l5,l6):
        lcd.move_to(0,0)
        lcd.putstr("1")
        if l1 >=0:
            lcd.putstr(f": {l1:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(8,0)
        lcd.putstr("2")
        if l2 >=0:
            lcd.putstr(f": {l2:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(0,1)
        lcd.putstr("3")
        if l3 >=0:
            lcd.putstr(f": {l3:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(8,1)
        lcd.putstr("4")
        if l4 >=0:
            lcd.putstr(f": {l4:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(0,2)
        lcd.putstr("5")
        if l5 >=0:
            lcd.putstr(f": {l5:3d}%")
        else:
            lcd.putstr(": ----")
        lcd.move_to(8,2)
        lcd.putstr("6")
        if l6 >=0:
            lcd.putstr(f": {l6:3d}%")
        else:
            lcd.putstr(": ----")





