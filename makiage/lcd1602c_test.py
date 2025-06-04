from LCD1602c import LCD1602
import time


a=LCD1602()
a.lcd_home()
a.lcd_clear()
a.lcd_pos(0, 0)

a.lcd_clear()

a.lcd_print("1:ガラガッチョ")
a.lcd_pos(0, 1)
a.lcd_print("2:マージャン　オオガチッチョ！")
a.lcd_curR()
