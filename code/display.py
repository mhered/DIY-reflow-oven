from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import writer
import freesans20

class Display:
    def __init__(self):
        # Initialize I2C and OLED
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
        self.oled = SSD1306_I2C(128, 64, i2c)
        self.writer = writer.Writer(self.oled, freesans20, verbose=False)

    def show_temp(self, title, value, heater_on):
        self.oled.fill(0)
        if value is not None:
            self.oled.text(title, 5, 5)
            self.writer.set_textpos(5, 30)
            self.writer.printstring("{:.1f} C".format(value))

            # if heater is on display an icon
            if heater_on:
                self.oled.text("ON", 50, 30)

        else:
            self.oled.text("NaN", 5, 5)
            self.writer.set_textpos(5, 30)
            self.writer.printstring("ERROR")

        self.oled.show()

    def show_message(self, title, text, line_height=20):
        self.oled.fill(0)
        self.oled.text(title, 5, 5)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            self.oled.text(line, 5, (i * line_height + 22))
        self.oled.show()
