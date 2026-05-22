import json
import time
import lmenu

lcd = lmenu.Menu()

class Config:
    def __init__(self):
        self.conf_fname = "config_cfg.py"
        self.dic = self.load_dic()
        self.nmotor = self.dic['nmotor']
        self.temp = self.dic['temp']
        self.measure_span = self.dic['measure_span']

    def load_dic(self):
        with open(self.conf_fname, "r") as f:
            try:
                dic = json.loads(f.read())
                return dic
            except:
                lcd.print("Dic load Err")
                time.sleep(2)

    def save_dic(self):
        if (self.load_dic() != self.dic):
            try:
                json.dumps(self.dic)
            except:
                lcd.print("Dic json Err")
                time.sleep(2)
                return
            with open(self.conf_fname,"w") as f:
                f.write(json.dumps(self.dic))
    
    def put_nmotor(self):
        self.dic['nmotor'] = self.nmotor

    def put_temp(self):
        self.dic['temp'] = self.temp

    def put_measure_span(self):
        self.dic['measure_span'] = self.measure_span








