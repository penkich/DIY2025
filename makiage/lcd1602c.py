# https://www.route55go.com/self-study/pico/class/s013_lcd/ を参考にしました。

from machine import I2C,Pin
import time
# LCD 1602
# HD44780U (LCD-II) Dot Matrix Liquid Crystal Display Controller/Driver
class LCD1602:
    def __init__(self,num=0, sda=8, scl=9):
        self.adr_lcd=0x3f    # 0x50(80)~0x57(87)
        self.i2c=I2C(num, sda=Pin(sda), scl=Pin(scl), freq=100_000)
        self.kana={
            "。":[161],"「":[162],"」":[163],"、":[164],"・":[165],"ヲ":[166],
            "ァ":[167],"ィ":[168],"ゥ":[169],"ェ":[170],"ォ":[171],
            "ャ":[172],"ュ":[173],"ョ":[174],"ッ":[175],
            "ア":[177],"イ":[178],"ウ":[179],"エ":[180],"オ":[181],
            "カ":[182],"キ":[183],"ク":[184],"ケ":[185],"コ":[186],
            "サ":[187],"シ":[188],"ス":[189],"セ":[190],"ソ":[191],
            "タ":[192],"チ":[193],"ツ":[194],"テ":[195],"ト":[196],
            "ナ":[197],"ニ":[198],"ヌ":[199],"ネ":[200],"ノ":[201],
            "ハ":[202],"ヒ":[203],"フ":[204],"ヘ":[205],"ホ":[206],
            "マ":[207],"ミ":[208],"ム":[209],"メ":[210],"モ":[211],
            "ヤ":[212],"ユ":[213],"ヨ":[214],"ラ":[215],"リ":[216],
            "ル":[217],"レ":[218],"ロ":[219],"ワ":[220],"ン":[221],
            "　":[32], "！":[33], "＃":[35], "ー":[45],
            "ガ":[182,222],"ギ":[183,222],"グ":[184,222],"ゲ":[185,222],"ゴ":[186,222],
            "ザ":[187,222],"ジ":[188,222],"ズ":[189,222],"ゼ":[190,222],"ゾ":[191,222],
            "ダ":[192,222], "ヂ":[193,222],"ヅ":[194,222], "デ":[195,222],"ド":[196,222],
            "バ":[202,222],"ビ":[203,222],"ブ":[204,222],"ベ":[205,222],"ボ":[206,222],
            "パ":[202,223],"ピ":[203,223],"プ":[204,223],"ペ":[205,223],"ポ":[206,223],
        }


    def lcd_wr(self,dat):           # write
        buf = bytearray(1)          # 1byteごとに送る
        buf[0] = dat
        self.i2c.writeto(self.adr_lcd,buf)
        time.sleep_ms(2)

    # 4bitモード送信の型
    #|D7/3|D6/2|D5/1|D4/1|BL|EN|R/W|RS| 8bit
    def lcd_dat(self,dat,RS=0):     #デフォルトはコマンド送信(RS=0)、データ送信はRS=1
        f= (dat & 0xf0)|0x0C|RS     # |BL|EN|R/W|RS|=|1|1|0|RS| 
        s= (dat & 0xf0)|0x08|RS     # |BL|EN|R/W|RS|=|1|0|0|RS| 
        return f,s

    # 4bitモード 4回送信する
    def lcd_cmd(self,dat):
        f,s=self.lcd_dat(dat)
        self.lcd_wr(f)
        self.lcd_wr(s)

        f,s=self.lcd_dat(dat<<4)         # LSB4bitをシフト
        self.lcd_wr(f)
        self.lcd_wr(s)
        
    # 初期化 4-bit mode、2行、カーソル点滅
    def lcd_init(self):
        # Initialize　4-bit mode
        fset=[0x30,0x30,0x30,0x20]
        for c in fset:
            f,s=self.lcd_dat(c)
            self.lcd_wr(f)
            self.lcd_wr(s)

        # 28:4bit col2,disp-cur,blink,entry-increase,disp-clear
        bset=[0x28,0x0F,0x06,0x01]
        for c in bset:
            f,s=self.lcd_dat(c)
            self.lcd_wr(f)
            self.lcd_wr(s)
            
            f,s=self.lcd_dat(c<<4)
            self.lcd_wr(f)
            self.lcd_wr(s)

    # moji data 
    def lcd_chr(self,dat):
        #RS=1 
        f,s=self.lcd_dat(dat,RS=1)
        self.lcd_wr(f)
        self.lcd_wr(s)
        f,s=self.lcd_dat(dat<<4,RS=1)
        self.lcd_wr(f)
        self.lcd_wr(s)

    #*****　カーソル位置 (DDRAM address)
    def lcd_pos(self,x, y):
        pos=(0x80 | (y* 0x40 + x))
        self.lcd_cmd(pos)

    #***** lcd に文字を表示 2行16文字 データ送信(RS=1)
    # eisuuji
    #def lcd_print(self,pr):
    #    m_dat=pr.encode()
    #    for i in m_dat:
    #        self.lcd_chr(i)

    def lcd_print(self,chs):
        for ch in chs:
            if ch in self.kana:
                if len(self.kana[ch]) ==1:
                    self.lcd_chr(self.kana[ch][0])
                elif len(self.kana[ch]) ==2:
                    self.lcd_chr(self.kana[ch][0])
                    self.lcd_chr(self.kana[ch][1])
            else:
                self.lcd_chr(ord(ch))
                
## 他のコマンド
    #Clear display
    def lcd_clear(self):
        self.lcd_cmd(0x01)
    #Return home
    def lcd_home(self):
        self.lcd_cmd(0x02)
    #Display on
    def lcd_on(self):
        self.lcd_cmd(0x0f)
    #Display on
    def lcd_off(self):
        self.lcd_cmd(0x08)
    #cursor shift-L
    def lcd_curL(self):
        self.lcd_cmd(0x10)
    #cursor shift-R
    def lcd_curR(self):
        self.lcd_cmd(0x14)
    #display shift-L
    def lcd_dspL(self):
        self.lcd_cmd(0x18)
    #display shift-L
    def lcd_dspR(self):
        self.lcd_cmd(0x1c)
