from kivy.uix.widget import Widget
from kivymd.uix.behaviors import CircularElevationBehavior

import socket

ADDR = ('192.168.1.11', 5000)
SIM_ADDR = ('192.168.1.11', 5555)

sim_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class JoyStick(
        CircularElevationBehavior,
        Widget):
    pass

class FingerController(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def on_touch_down(self, touch):
        
        controller_x = int(self.x)
        controller_w = int(self.width)
        controller_y = int(self.y)
        controller_h = int(self.height)
        #print(ud)
        if int(touch.x) in range(controller_x, controller_x+controller_w) and \
            int(touch.y) in range(controller_y, controller_y+controller_h):
            _coords = self.get_stick_coords(touch)

            print(_coords)
            # self.__app.label.text = str(_coords).upper()
            self.joystick.center = touch.x, touch.y

            try:
                sim_socket.sendto('{}'.format(_coords).encode(), SIM_ADDR)
            except Exception as e:
                pass
        else:
            self.joystick.center = self.center
            try:
                pass
                # s.sendto(b'stop', ADDR)
            except Exception as e:
                pass
        touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        ud = touch.ud
        #print(ud)
        
        controller_x = int(self.x)
        controller_w = int(self.width)
        controller_y = int(self.y)
        controller_h = int(self.height)

        if int(touch.x) in range(controller_x, controller_x+controller_w) and \
            int(touch.y) in range(controller_y, controller_y+controller_h):
            _coords = self.get_stick_coords(touch)
            print(_coords)
            self.joystick.center = touch.x, touch.y
            # self.__app.label.text = str(_coords).upper()
            try:
                sim_socket.sendto('{}'.format(_coords).encode(), SIM_ADDR)
            except Exception as e:
                pass
                
        else:
            self.joystick.center = self.center
            try:
                sim_socket.sendto(b'stop', SIM_ADDR)
            except Exception as e:
                pass

    def on_touch_up(self, touch):
        self.joystick.center = self.center
        touch.ungrab(self)
        # self.__app.label.text = "stable".upper()
        try:
            sim_socket.sendto(b'stop', SIM_ADDR)
        except Exception as e:
                pass

    def get_stick_coords(self, touch):
        s_x = int(touch.x)
        s_y = int(touch.y)
        p_x = int(self.x)
        p_y = int(self.y)
        p_w = int(self.width)
        p_h = int(self.height)

        w = p_w // 3
        h = p_h // 3

        current_position = None

        # bottom left
        if s_x in range(p_x, p_x+w) and s_y in range(p_y, p_y+h):
            current_position = "left-90"
        # bottom middle
        if s_x in range(p_x+w, p_x+w*2) and s_y in range(p_y, p_y+h):
            current_position = "backward"
        # bottom right
        if s_x in range(p_x+w*2, p_x+w*3) and s_y in range(p_y, p_y+h):
            current_position = "right-90"

        # middle left 
        if s_x in range(p_x, p_x+w) and s_y in range(p_y+h, p_y+h*2):
            current_position = "left"
        # middle middle
        if s_x in range(p_x+w, p_x+w*2) and s_y in range(p_y+h, p_y+h*2):
            current_position = "stop"
        # middle right
        if s_x in range(p_x+w*2, p_x+w*3) and s_y in range(p_y+h, p_y+h*2):
            current_position = "right"

        # top left
        if s_x in range(p_x, p_x+w) and s_y in range(p_y+h*2, p_y+h*3):
            current_position = "left-45"
        # top middle
        if s_x in range(p_x+w, p_x+w*2) and s_y in range(p_y+h*2, p_y+h*3):
            current_position = "foreward"
        # top right
        if s_x in range(p_x+w*2, p_x+w*3) and s_y in range(p_y+h*2, p_y+h*3):
            current_position = "right-45"

        return current_position


