from boardtype import Boardtype
from machine import Pin, I2C, SoftI2C, Timer
import json
import time
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
import mcp23017 # Ｉ／Ｏエキスパンダー

mcp = mcp23017.MCP23017(i2c, 0x20) # mcp[0]=A0,...,mcp[7]=A7,mcp[8]=B0,...mcp[15]=B7

WorkF = [Pin(21, Pin.IN), Pin(12, Pin.IN), Pin(26, Pin.IN), Pin(14, Pin.IN)] # 注意（2番めリレー動作中:0 非動作:1)
WorkR = [Pin(20, Pin.IN), Pin(11, Pin.IN), Pin(22, Pin.IN), Pin(13, Pin.IN)] # 注意（1番めリレー動作中:0 非動作:1)
f_pins = [mcp[8], mcp[10], mcp[12], mcp[14]] # [B0,B2,B4,B6]モーター正転指示
r_pins = [mcp[9], mcp[11], mcp[13], mcp[15]] # [B1,B3,B5,B7]モーター反転指示

if Boardtype == 6:
    mcp2 = mcp23017.MCP23017(i2c, 0x21) # a0,a1,a2 = 1,0,0
    WorkF += [Pin(6, Pin.IN), Pin(10, Pin.IN)] # 注意（2番めリレー動作）
    WorkR += [Pin(5, Pin.IN), Pin( 7, Pin.IN)] # 注意（1番めリレー動作）
    f_pins += [mcp2[8], mcp2[10]] # [D0,D2]モーター正転指示
    r_pins += [mcp2[9], mcp2[11]] # [D1,D3]モーター反転指示


for f_pin in f_pins:
    f_pin.output()
    f_pin.value(0)
for r_pin in r_pins:
    r_pin.output()
    r_pin.value(0)

class Motor:
    def __init__(self, n):
        self.conf_fname = f"motor{n}_cfg.py"
        self.dic = self.load_dic()
        self.posmax = self.dic['posmax']
        self.posmaxdic = self.dic['posmax']
        self.pos = self.dic['pos']
        self.WorkF = WorkF[n]
        self.WorkR = WorkR[n]
        self.posmin = 0
        self.n = n
        self.tim = Timer()
        self.cnt = 0
        self.flg = False
        self.live = self.dic['live']
        self.x = 0
        self.y = 0
    def counter(self,c):
        self.cnt += 1
    def stop_f(self, dsec):
        self.dsec -= 1
        self.pos += 1
        #f_pins[self.n].value(1)
        if self.WorkF.value() == 1:
            self.x += 1 # 他モーター動作時にWorkFの値が安定しないので、連続した値で判定する
        if (self.x > 5 or self.dsec == 0) and self.flg:
            self.tim.deinit()
            if self.WorkF.value() == 1:
                self.pos -= 1
            f_pins[self.n].value(0)
            if self.x > 5:
                self.pos = self.posmax
            self.x = 0
        self.flg = True
    def stop_r(self, c):
        self.dsec -= 1
        self.pos -= 1
        #r_pins[self.n].value(1)
        if self.WorkR.value() == 1:
            self.x += 1 # 他モーター動作時にWorkRの値が安定しないので、連続した値で判定する
        if (self.x > 5 or self.dsec == 0) and self.flg:
            self.tim.deinit()
            if self.WorkR.value() == 1:
                self.pos = 0
            r_pins[self.n].value(0)
            self.x = 0
        self.flg = True

    def chk_pos(self):
        return self.pos
    def mov_f_irq(self, dsec):
        self.dsec = dsec
        f_pins[self.n].value(1)
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.stop_f)
    def mov_r_irq(self, dsec):
        self.dsec = dsec
        r_pins[self.n].value(1)
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.stop_r)
    def mov_f(self, dsec):
        x = 0
        self.cnt = 0
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.counter)
        while self.cnt < dsec:
            f_pins[self.n].value(1)
        f_pins[self.n].value(0)
        self.reset_relay()
        self.tim.deinit()
        self.pos += dsec
    def mov_r(self, dsec):
        x = 0
        self.cnt = 0
        self.tim.init(period=100,mode=self.tim.PERIODIC,callback = self.counter)
        while self.cnt < dsec:
            r_pins[self.n].value(1)
        r_pins[self.n].value(0)
        self.reset_relay()
        self.tim.deinit()
        self.pos -= dsec

    def stop_flimit(self, c):
        self.pos += 1
        if self.WorkF.value() == 1 and self.flg == True:
            self.tim.deinit()
            f_pins[self.n].value(0)
        self.flg = True

    def stop_rlimit(self, c):
        self.pos -= 1
        if self.WorkR.value() == 1 and self.flg == True:
            self.tim.deinit()
            r_pins[self.n].value(0)
            self.pos = 0
        if self.pos < -10000:
            self.tim.deinit()
        self.flg = True

    def mov_flimit_irq(self): # 割り込みを使って最後まで正転
        f_pins[self.n].value(1)
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.stop_flimit)

    def mov_rlimit_irq(self): # 割り込みを使って最後まで反転
        r_pins[self.n].value(1)
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.stop_rlimit)

    def mov_flimit(self):
        x = 0
        self.cnt = self.pos
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.counter)
        f_pins[self.n].value(1)
        while True:
            time.sleep(0.01)
            if self.WorkF.value() == 1:
                if x > 1:
                    self.tim.deinit()
                    break
                x += 1
        self.reset_relay()
        #self.pos = self.posmax
        #self.pos = x
        self.pos = self.cnt
        self.put_pos()
        return self.cnt

    def mov_rlimit(self):
        x = 0
        self.cnt = 0
        self.tim.init(period=100, mode=self.tim.PERIODIC,callback = self.counter)
        r_pins[self.n].value(1)
        while True:
            time.sleep(0.01)
            if self.WorkR.value() == 1:
                if x > 1:
                    self.tim.deinit()
                    break
                x += 1
        self.reset_relay()
        self.pos = self.posmin
        return self.cnt

    def reset_relay(self):
        f_pins[self.n].value(0)
        r_pins[self.n].value(0)

    def load_dic(self):
        f = open(self.conf_fname, "r")
        try:
            dic = json.loads(f.read())
        except:
            print(f"{self.n} load dic err")
            return self.dic
        f.close()
        return dic

    def save_dic(self):
        f = open(self.conf_fname)
        if (self.load_dic() != self.dic):
            f.write(json.dumps(self.dic))
        f.close()

    def put_posmax(self):
        self.dic['posmax'] = self.posmax

    def put_pos(self):
        self.dic['pos'] = self.pos

    def put_nmotor(self):
        self.dic['nmotor'] = self.nmotor

    def put_live(self):
        self.dic['live'] = self.live
    #def put_temp(self):
    #    self.dic['temp'] = self.temp
        
    def clear_pos(self):
        self.dic['pos'] = 0


    def islive_f(self):
        self.y = 0
        self.mov_f_irq(10)
        for i in range(20):
            time.sleep(0.02)
            if self.WorkF.value() == 1:
                self.y += 1
        if self.y < 5:
            return True
        else:
            return False


