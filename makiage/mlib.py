from machine import Pin, I2C, SoftI2C, Timer
import json
import time
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
import mcp23017 # Ｉ／Ｏエキスパンダー
mcp = mcp23017.MCP23017(i2c, 0x20)

LimitSWU = [Pin(21, Pin.IN), Pin(12, Pin.IN), Pin(26, Pin.IN), Pin(14, Pin.IN)] # 注意（2番めリレー動作）
LimitSWD = [Pin(20, Pin.IN), Pin(11, Pin.IN), Pin(22, Pin.IN), Pin(13, Pin.IN)] # 注意（1番めリレー動作）

f_pins = [mcp[8], mcp[10], mcp[12], mcp[14]] # モーター正転指示
r_pins = [mcp[9], mcp[11], mcp[13], mcp[15]] # モーター反転指示

for f_pin in f_pins:
    f_pin.output()
    f_pin.value(0)
for r_pin in r_pins:
    r_pin.output()
    r_pin.value(0)

class Motor:
    def __init__(self, n):
        self.conf_fname = "motor_cfg.py"
        self.dic = self.load_dic()
        self.nmotor = self.dic['nmotor']
        self.posmax = self.dic['posmax'][n]
        self.pos = self.dic['pos'][n]
        self.LimitSWU = LimitSWU[n]
        self.LimitSWD = LimitSWD[n]
        self.posmin = 0
        self.n = n
        self.tim = Timer()
        self.tim2 = Timer()
        self.tim3 = Timer()
        self.cnt = 0
        self.flg = False
    def counter(self,c):
        self.cnt += 1
    def stop_f(self, dsec):
        self.dsec -= 1
        self.pos += 1
        if (self.LimitSWU.value() == 1 or self.dsec == 0) and self.flg:
            self.tim2.deinit()
            f_pins[self.n].value(0)
            if self.LimitSWU.value() == 1:
                self.pos -= 1
        self.flg = True
    def stop_r(self, c):
        self.dsec -= 1
        self.pos -= 1
        if (self.LimitSWD.value() == 1 or self.dsec == 0) and self.flg:
            self.tim2.deinit()
            r_pins[self.n].value(0)
            if self.LimitSWD.value() == 1:
                self.pos = 0
        self.flg = True

    def chk_pos(self):
        return self.pos
    def mov_f_irq(self, dsec):
        self.dsec = dsec
        f_pins[self.n].value(1)
        self.tim2.init(period=100,mode=self.tim2.PERIODIC,callback = self.stop_f)
    def mov_r_irq(self, dsec):
        self.dsec = dsec
        r_pins[self.n].value(1)
        self.tim2.init(period=100,mode=self.tim2.PERIODIC,callback = self.stop_r)
    def mov_f(self, dsec):
        x = 0
        self.cnt = 0
        self.tim.init(period=100,mode=self.tim.PERIODIC,callback = self.counter)
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
        if self.LimitSWU.value() == 1 and self.flg == True:
            self.tim3.deinit()
            f_pins[self.n].value(0)
        self.flg = True

    def stop_rlimit(self, c):
        self.pos -= 1
        if self.LimitSWD.value() == 1 and self.flg == True:
            self.tim3.deinit()
            r_pins[self.n].value(0)
            self.pos = 0
        self.flg = True

    def mov_flimit_irq(self):
        f_pins[self.n].value(1)
        self.tim3.init(period=100,mode=self.tim3.PERIODIC,callback = self.stop_flimit)

    def mov_rlimit_irq(self):
        r_pins[self.n].value(1)
        self.tim3.init(period=100,mode=self.tim3.PERIODIC,callback = self.stop_rlimit)

    def mov_flimit(self):
        x = 0
        self.cnt = 0
        self.tim.init(period=100,mode=self.tim.PERIODIC,callback = self.counter)
        f_pins[self.n].value(1)
        while True:
            time.sleep(0.01)
            if self.LimitSWU.value() == 1:
                if x > 1:
                    self.tim.deinit()
                    break
                x += 1
        self.reset_relay()
        self.pos = self.posmax
        return self.cnt

    def mov_rlimit(self):
        x = 0
        self.cnt = 0
        self.tim.init(period=100,mode=self.tim.PERIODIC,callback = self.counter)
        r_pins[self.n].value(1)
        while True:
            time.sleep(0.01)
            if self.LimitSWD.value() == 1:
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
        f = open(self.conf_fname)
        dic = json.loads(f.read())
        f.close()
        return dic

    def save_dic(self):
        f = open(self.conf_fname)
        if (self.load_dic() != self.dic):
            f.write(json.dumps(self.dic))
        f.close()

    def put_posmax(self):
        self.dic['posmax'][self.n] = self.posmax

    def put_pos(self):
        self.dic['pos'][self.n] = self.pos
