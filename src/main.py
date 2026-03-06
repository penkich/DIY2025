from boardtype import Boardtype # ボードタイプ（4:モーター４つ用、6:モーター６つ用コントローラ）は、boardtype.pyを直接編集すること！
from machine import Pin, I2C, SoftI2C, PWM, Timer, SPI
import os, sdcard, time, machine
###import network, ambient # アンビエントは将来用
import config
led = Pin("LED", Pin.OUT)
led.on()
###LED = Pin(25, Pin.OUT) # picoボード上のLED(但し、picoW,pico2WはGPIOでは無いのでダメ）
###LED.value(1) # LED点灯

###########
# i2cを設定
###########
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq = 100000)
# lcd_addr = i2c.scan()[1]
# LCDの種類によっては、i2cアドレスが異なる(ex. 39, 63)。
# i2cアドレスは、lcd_cfg.py に保存される。
import lmenu 
lcd = lmenu.Menu()
#################
# Ｉ／Ｏエキスパンダー
#################
import mcp23017 
mcp = mcp23017.MCP23017(i2c, 0x20)
if Boardtype == 6:
    mcp2 = mcp23017.MCP23017(i2c, 0x21)

#########################################
# ロータリーエンコーダー付属スイッチ　ON:0, OFF:1
#########################################
sw = Pin(2, Pin.IN)

###############################
# SDカードの設定　（将来用）
###############################
#spi = SPI( 0, baudrate = 100000, sck  = Pin(18), mosi = Pin(19), miso = Pin(16))
#cs = Pin(17, mode=Pin.OUT, value=1)
#try:
#    sd = sdcard.SDCard(spi, cs)
#    os.mount(sd, '/sd')
#except:
#    print("sd card err.")

###############################
# 目標温度(この温度を越えたら開ける）
###############################
try:
    conf = config.Config()
    CTemp = conf.temp # 目標温度
except:
    lcd.print("config_cfg Err!")

#########################
# モーターのオブジェクトを生成
#########################
import lmotor
motor = [lmotor.Motor(0),lmotor.Motor(1),lmotor.Motor(2),lmotor.Motor(3)]
if Boardtype == 6:
    motor += [lmotor.Motor(4),lmotor.Motor(5)]
nmotor = conf.nmotor
print(nmotor)

#########################
# スイッチ類をポートに関連付け
#########################
def setport():
    global SeiHanSW, manSWs, manExes
    SeiHanSW = Pin(15, Pin.IN, Pin.PULL_DOWN) # 正反切り替えSW
    manSW0 = mcp[4] # GPA4　モーター０　自動/マニュアル = 0/1 切替スイッチ
    manSW1 = mcp[5] # GPA5　モーター１
    manSW2 = mcp[6] # GPA6　モーター２
    manSW3 = mcp[7] # GPA7　モーター３
    manSW0.input()
    manSW1.input()
    manSW2.input()
    manSW3.input()
    manSWs = [manSW0, manSW1, manSW2, manSW3]

    if Boardtype == 6:
        manSW4 = mcp2[4] # GPA6　モーター２
        manSW5 = mcp2[5] # GPA7　モーター３
        manSW4.input()
        manSW5.input()
        manSWs = [manSW0, manSW1, manSW2, manSW3, manSW4, manSW5]

    for i in range(4):
        mcp[i].input()
        mcp[i].input(pull=1)
    manExeBtn0 = mcp[0] # GPA0　モーター０のマニュアル操作ボタン push = 0
    manExeBtn1 = mcp[1] # GPA1　モーター１
    manExeBtn2 = mcp[2] # GPA2　モーター２
    manExeBtn3 = mcp[3] # GPA3　モーター３
    manExes = [manExeBtn0, manExeBtn1, manExeBtn2, manExeBtn3]

    if Boardtype == 6:
        mcp2[0].input(pull=1)
        mcp2[1].input(pull=1)
        manExeBtn4 = mcp2[0] # GPC0　モーター４のマニュアル操作ボタン push = 0
        manExeBtn5 = mcp2[1] # GPC1　モーター５
        manExes = [manExeBtn0, manExeBtn1, manExeBtn2, manExeBtn3, manExeBtn4, manExeBtn5]

###############################################
# 付属スイッチを押したまま起動すると初期設定モードに入る。
###############################################
lcd.clear()
if sw.value() == 0:
    setport()
    time.sleep(1)
    lcd.clear()
    lcd.print("ショキセッテイシマス")
    time.sleep(1)
    lcd.clear()
    nmotor = lcd.val_sentaku(1, 6, 1, 12, "モーターノカズ?",2) # １〜6台を選択
    time.sleep(0.5)
    conf.nmotor = nmotor
    conf.put_nmotor()
    conf.save_dic() # コンフィグファイルに辞書を保存

    while sw.value() == 0:
        pass
    time.sleep(0.5)
    lcd.clear()
    ans = lcd.yn_sentaku("カイヘイテスト?")
    time.sleep(0.5)
    if ans == 0:
        lcd.clear()
        lcd.print("マニュアルデ ボタン オシテ")
        while sw.value() != 0:
            time.sleep(0.5)
            if SeiHanSW.value() == 1: # 正転の場合
                for i in range(nmotor):
                    time.sleep(0.02)
                    if manSWs[i].value() == 1: # マニュアルの場合
                        if manExes[i].value() == 0: # ボタンが押されたら
                            time.sleep(0.1)
                            motor[i].mov_f_irq(20) # 正転10%
                        else:
                            time.sleep(0.02)
            else: # 反転の場合
                for i in range(nmotor):
                    time.sleep(0.02)
                    if manSWs[i].value() == 1: # マニュアルの場合
                        if manExes[i].value() == 0:
                            time.sleep(0.1)
                            motor[i].mov_r_irq(20) # 反転10%
                        else:
                            time.sleep(0.02)
    time.sleep(0.5)

#    ans = lcd.yn_sentaku("WiFiセッテイスル?")
#    if ans == 0:
#        time.sleep(0.5)
#        essid = lcd.moji_sentaku()
#        print(essid)
    time.sleep(0.5)


    lcd.clear()
    ans = lcd.yn_sentaku("モーターイキシニ?")
    if ans == 0:
        time.sleep(1)
        for i in range(nmotor):
            lcd.clear()
            lcd.print(f"Motor{i+1}")
            time.sleep(0.2)
            sentaku = lcd.line_sentaku(["Live","Dead"],8,0)
            if sentaku == "Live":
                motor[i].live = 1
            else:
                motor[i].live = 0
            motor[i].put_live()
            motor[i].save_dic()
    
    time.sleep(0.5)
    lcd.clear()
    ans = lcd.yn_sentaku("モーターセッテイ?")
    if ans == 0:
        time.sleep(0.5)
        while True:
            lcd.clear()
            n = lcd.val_sentaku(1, 6, 1, 13, "モーターノバンゴウ?",2)
            time.sleep(0.5)
            lcd.clear()
            lcd.print(f"{n}バンモーター CLOSING")
            motor[n-1].mov_rlimit() # 閉めてから
            lcd.clear()
            lcd.print(f"{n}バンモーター OPENING")
            motor[n-1].mov_flimit() # 全開して
            motor[n-1].posmax = motor[n-1].pos
            motor[n-1].put_pos() # posを辞書に保存（不要？）
            if motor[n-1].posmax > 0:
                motor[n-1].live = 1
                motor[n-1].put_live()
                motor[n-1].put_posmax() # posmaxを辞書に保存
            else:
                motor[n-1].live = 0
                motor[n-1].put_live()
                ##motor[n-1].posmax = 100 # エラーの場合、とりあえず100にする。
                motor[n-1].put_posmax()
                time.sleep(0.2)
                lcd.clear()
                lcd.print(f"{n}バンモーター エラー")
                time.sleep(5)
            motor[n-1].save_dic() # コンフィグファイルに辞書を保存
            lcd.clear()
            lcd.print(f"{n}バンモーター CLOSING")
            motor[n-1].mov_rlimit() # 閉める
            lcd.clear()
            print(f"{motor[n-1].posmax}")
            time.sleep(1)
            ans = lcd.yn_sentaku("シュウリョウ?")
            if ans == 0:
                break
        lcd.clear()
        lcd.print("カンリョウシマシタ")
        lcd.pos(0,1)
        ###lcd.print("リセットシテクダサイ")
        time.sleep(5)
        ###machine.reset()
        
#########################
# オンド設定
#########################
def set_temp():
    global CTemp
    lcd.clear()
    CTemp = lcd.val_sentaku(20, 40, CTemp, 12, "セッテイオンド", 2)
    time.sleep(0.5)
    lcd.clear()
    conf.temp = CTemp
    conf.put_temp()
    conf.save_dic()
    print(CTemp)

#########################
# 温度によるモーター動作の間隔
#########################
def set_measure_span():
    global tim_control
    global Span
    tim_control.deinit()
    lcd.clear()
    Span = lcd.val_sentaku(30, 600, Span, 12, "カイヘイカンカク",3) #
    time.sleep(0.5)
    lcd.clear()
    conf.measure_span = Span
    conf.put_measure_span()
    conf.save_dic()
    Span = conf.measure_span
    global tim_control
    tim_control = Timer(period = Span * 1000, mode = Timer.PERIODIC, callback = control) # Span秒ごとに実行
    print(Span)

################
# wifi　（将来用）
################
"""
def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("aterm-xxxxxx", "xxxxxxxxxxxx")
    while wlan.isconnected() == False: 
        print('Waiting for connection...')
        time.sleep(1)
    print("ok")

connect() # WiFi に接続

def sendData(e):
    am.send({'d1': Temp, 'd2': m0, 'd3': m1})

chid = "63931"
rkey = "xxxxxxxxxxxxxxxx"
wkey = "xxxxxxxxxxxxxxxx"
am = ambient.Ambient(chid, wkey, rkey)

# アンビエントに定期的にデータ送信
timAmbi = Timer(period=900000, mode=Timer.PERIODIC, callback=sendData)
"""

#############
# 温度センサー
#############
import onewire, ds18x20
try:
    datPin = machine.Pin(27) # 温度センサーのデーターピン
    ds = ds18x20.DS18X20(onewire.OneWire(datPin))
    rom = ds.scan()[0] # １つが前提
    ds.convert_temp()
    Temp = ds.read_temp(rom)
except:
    lcd.move_to(0, 1)
    lcd.print("センサーエラー")

setTemp = 30
memTemp = [] # 比例制御用に考えていたが使用していない

##########################################
# １秒ごとに割り込みで温度を取得　-> global Temp
##########################################
def chkTemp(timer):
    global Temp
    try:
        ds.convert_temp()
        Temp = ds.read_temp(rom)
    except:
        Temp = -99
tim = Timer(period=1000, mode=Timer.PERIODIC, callback=chkTemp)

#######################
# 温度に基づく開閉（割込み）
#######################
Alternate = 0
def control(e):
    global Alternate
    Alternate += 1
    Alternate %= 2
    for i in range(Alternate,nmotor,2):
        diff = abs(Temp - CTemp)
        print(diff)
        if Temp > CTemp and manSWs[i].value() != 1: # マニュアルでなかったら
            if int(motor[i].pos / motor[i].posmax * 100) <= 90:
                if diff > 1: # テスト的に比例制御っぽくしてみる（現場で検証する必要あり）
                    motor[i].mov_f_irq(int(motor[i].posmax/10)) # 1割巻き上げ
                else:
                    motor[i].mov_f_irq(int(motor[i].posmax/20)) # 0.5割巻き上げ
            if 100 > int(motor[i].pos / motor[i].posmax * 100) > 90:
                motor[i].mov_flimit_irq() # 最後まで巻き上げ
        if Temp < CTemp and manSWs[i].value() != 1:
            if int(motor[i].pos / motor[i].posmax * 100) >= 10:
                if diff > 1:
                    motor[i].mov_r_irq(int(motor[i].posmax/10)) # 1割巻き下げ
                else:
                    motor[i].mov_r_irq(int(motor[i].posmax/20)) # 0.5割巻き下げ
            if 0 < int(motor[i].pos / motor[i].posmax * 100) < 10:
                motor[i].mov_rlimit_irq() # 最後まで巻き下げ


lcd.clear()
CTemp = conf.temp

##################################
# 電源が入ったらモーターを閉位置にリセット
##################################
lcd.clear()
lcd.print("ショキカチュウ")

try:
    live_range = [x for x in range(nmotor) if motor[x].live ==1]
except:
    lcd.clear()
    lcd.print("Err ショキカミナオシテネ")

if nmotor >= 4: # モーター数が多い場合は、半分づつ負荷分散する
    live_rangeEv = [] # 生きてる偶数番モーター
    live_rangeOd = [] # 生きてる奇数番もーーター
    for i in live_range:
        if i % 2 == 0:
            live_rangeEv.append(i)
        else:
            live_rangeOd.append(i)
    
    for i in live_range:
        if live_rangeEv != []:
            if i == live_rangeEv[-1]:
                motor[i].mov_rlimit() # 最後のモーターは割り込みしない
            else:
                if i in live_rangeEv:
                    motor[i].mov_rlimit_irq()
        time.sleep(0.5)
        if live_rangeOd != []:
            if i == live_rangeOd[-1]:
                motor[i].mov_rlimit() # 最後のモーターは割り込みしない
            else:
                if i in live_rangeOd:
                    motor[i].mov_rlimit_irq()
        time.sleep(0.5)

    flag = 1
    while flag != 0:
        flag = 0
        for i in range(0, nmotor, 2):
            if motor[i].live == 1:
                flag += motor[i].pos
    flag = 1
    while flag != 0:
        flag = 0
        for i in range(1, nmotor, 2):
            if motor[i].live == 1:
                flag += motor[i].pos
else:
    for i in live_range:
        if i == live_range[-1]:
            motor[i].mov_rlimit() # 最後のモーターは割り込みしない
        else:
            motor[i].mov_rlimit_irq()
        time.sleep(0.5)
    flag = 1
    while flag != 0:
        flag = 0
        for i in range(nmotor):
            if motor[i].live == 1:
                flag += motor[i].pos

lcd.clear()
lcd.print("ショキカ デキマシタ")
time.sleep(3)

#######################################
# 初期化後に温度による開閉割り込みを動作させる
#######################################
Span = conf.measure_span
tim_control = Timer(period = Span * 1000, mode = Timer.PERIODIC, callback = control) # Span秒ごとに実行

def main():
    lcd.clear()
    lcd.hide_cursor()
    time.sleep(0.5)
    print("main loop")
    while True:
        time.sleep(0.02)
        lcd.hide_cursor()
        if sw.value() == 0: # スイッチが押されていたら
            lcd.clear()
            time.sleep(0.5)
            ans = lcd.yn_sentaku("オンドセッテイ", offset=1)
            time.sleep(0.5)
            if ans == 0:
                set_temp() # 設定変更によるCTempは、辞書に登録するがオンメモリーです。
                ##conf = config.Config()
                ##CTemp = conf.temp
            lcd.clear()
            ans = lcd.yn_sentaku("カイヘイカンカク")
            time.sleep(0.5)        
            if ans == 0:
                set_measure_span()
        v0 = int((motor[0].pos / motor[0].posmax)*100)
        v1 = int((motor[1].pos / motor[1].posmax)*100)
        v2 = int((motor[2].pos / motor[2].posmax)*100)
        v3 = int((motor[3].pos / motor[3].posmax)*100)
        if motor[0].live == 0:
            v0 = -1
        if motor[1].live == 0:
            v1 = -1
        if motor[2].live == 0:
            v2 = -1
        if motor[3].live == 0:
            v3 = -1
    ###print(motor[0].pos)
        if Boardtype == 4:
            if nmotor == 2:
                lcd.disp_2(v0, v1)
            else:
                lcd.disp_4(v0, v1, v2, v3)
        if Boardtype == 6:
            v4 = int((motor[4].pos / motor[4].posmax)*100)
            v5 = int((motor[5].pos / motor[5].posmax)*100)
            if motor[4].live == 0:
                v4 = -1
            if motor[5].live == 0:
                v5 = -1
            lcd.disp_6(v0, v1, v2, v3, v4, v5)
        #try:
        if Boardtype == 4:
            lcd.move_to(1,1)
        if Boardtype == 6:
            lcd.move_to(1,3)
        time.sleep(0.05)  
        if Temp == -99:
            lcd.print("Sensor Err")
        else:
            lcd.print(f"{Temp:2.1f}/{conf.temp}℃/{Span:03d}s")
        memTemp.append(Temp) # 比例制御のために準備(但し、未使用）
        if len(memTemp) > 100:
            memTemp.pop(0)

        #except: # 温度測定時の例外処理が多重になるので避ける
        #    lcd.print("Sensor Err　　　　")

        if SeiHanSW.value() == 1: # 正転の場合
            for i in range(nmotor):
                if manSWs[i].value() == 1: # マニュアルの場合
                    if manExes[i].value() == 0: # ボタンが押されたら
                        time.sleep(0.1)
                        motor[i].mov_f_irq(int(motor[i].posmax/10)) # 正転10%
                    else:
                        time.sleep(0.02)
        else: # 反転の場合
            for i in range(nmotor):
                if manSWs[i].value() == 1: # マニュアルの場合
                    if manExes[i].value() == 0:
                        time.sleep(0.1)
                        motor[i].mov_r_irq(int(motor[i].posmax/10)) # 反転10%
                    else:
                        time.sleep(0.02)

################
# メインループ
################
setport()
main()

