from machine import Pin, I2C, SoftI2C, PWM, Timer, SPI, RTC
import os, sdcard, time
from machine_i2c_lcd import I2cLcd
LED = Pin(25, Pin.OUT) # picoボード上のLED
LED.value(1) # LED点灯
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8))
addr = i2c.scan()[1]
lcd = I2cLcd(i2c, addr, 2, 16)
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

# ロータリーエンコーダー（割り込み仕様）
from rotary_irq_esp import RotaryIRQ

r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val=9, 
        max_val=60, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)

val_old = r.value()
# r.value() はいつでも割り込みで値を取得できる。

import time
from rotary_irq_esp import RotaryIRQ

lcd.hide_cursor()

items = ['ショキセッテイ ? Y/N']


def yn_sentaku(text):
    r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val=0,
        max_val=1, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)
    lcd.blink_cursor_on()
    lcd.putstr_kana(text)
    lcd.move_to(len(text)-3, 0)
    val_new = 0
    val_old = 0
    while True:
        if sw.value() == 0:
            lcd.clear()
            lcd.move_to(0,0)
            return val_new
        val_new = r.value()    
        if val_old != val_new:
            val_old = val_new
            lcd.move_to(val_new * 2 + len(text)-3, 0)

def val_sentaku(text):
    lcd.hide_cursor()
    lcd.putstr_kana(f"{text}    ℃")
    r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val=0,
        max_val=40, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)
    val_old = r.value()
    while True:
        val_new = r.value()
        if val_old != val_new:
            val_old = val_new
            lcd.move_to(len(text)+3,0)
            lcd.putstr(f'{r.value():02d}')
        if sw.value() == 0:
            return val_new

def jikoku_sentaku(text, min_val, max_val):
    lcd.hide_cursor()
    lcd.putstr_kana(f"{text} ")
    r = RotaryIRQ(pin_num_clk=3,  # RP2040
        pin_num_dt=4, 
        min_val= min_val,
        max_val= max_val, 
        reverse=False, 
        range_mode=RotaryIRQ.RANGE_WRAP)
    val_old = r.value()
    while True:
        val_new = r.value()
        if val_old != val_new:
            val_old = val_new
            lcd.move_to(len(text)+2,0)
            lcd.putstr(f'{r.value():02d}')
        if sw.value() == 0:
            lcd.clear()
            lcd.move_to(0,0)
            return val_new


res = yn_sentaku(items[0])
if res == 0:
    time.sleep(0.2)
    x = val_sentaku("オンド")
    print(x)
if res == 1:
    time.sleep(0.2)
    month = jikoku_sentaku("month", 1, 12)
    time.sleep(0.2)
    date = jikoku_sentaku("date", 1, 31)
    time.sleep(0.2)
    hour = jikoku_sentaku("hour", 0, 24)
    time.sleep(0.2)
    minute = jikoku_sentaku("minute", 0, 59)
    lcd.putstr(f"{month:02d}/{date:02d} {hour:02d}:{minute:02d}")

"""
while True:
    val_new = r.value()
    
    if val_old != val_new:
        val_old = val_new
        #print('result =', val_new)
        lcd.move_to(0, 0)
        lcd.putstr(f'{val_new}')
        lcd.move_to(0, 0)
    time.sleep_ms(50)

""" 
    
