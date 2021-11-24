from drone_data_pb2 import DroneData
from widgets import CameraFeedThumbnail
from joycontroller import JoyStick, FingerController
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from kivymd.toast import toast
from kivy.logger import Logger
from kivy.lang.builder import Builder

import plyer, math, time, random
from threading import Thread

from PIL import Image as PILImage
from io import BytesIO
import base64
import socket
import time
import json
from datetime import datetime
from pathlib import Path

try:
    from android.permissions import request_permissions, check_permission, Permission
except ImportError as e:
    Logger.error(str(e))

ADDR = ('192.168.1.11', 5000)
SIM_ADDR = ('192.168.1.11', 5002)

sim_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


HOST = '192.168.1.11'
PORT = 5000
VIDEO_ADDR = (HOST, PORT)
BUFF = 65536

class DJIMainApp(MDApp):
    MAP_TOGGLED = False
    STOP_READING = False

    CHANGE_FULL_FEED = True

    stop_recv = False
    ARMED = False
    dialog = None

    my_frame = None
    CLOSE_SIGNAL = False
    CONNECTION_STABLISHED = False
    FEED_STARTED = False
    STARTED = True
    STOP = False
    my_texture = None
    send_command_clock = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.recv_thread = Thread(target=self.recv_status_callback, daemon=True)
        self.update_info_thread = Thread(target=self.update_info_layer_values)

        self.drone_camera_feed_thumbnail = CameraFeedThumbnail(pos=(dp(5), dp(5)),
                                            size=(dp(180),dp(100)))

        self.an_full = Animation(pos=(0,0), size=(Window.width, Window.height), duration=.2)
        self.an_defull = Animation(pos=(dp(3), dp(3)), size=(dp(180), dp(100)), duration=.2)
        
        self.an_full_vid = Animation(pos=(0,0), size=Window.size, duration=.2)
        self.an_defull_vid = Animation(pos=(dp(3), dp(3)), size=(dp(180), dp(100)), duration=.2)

        self.open_setting_panel_animation = Animation(x=Window.width*.3, duration=.2)
        self.close_setting_panel_animation = Animation(x=Window.width+dp(40), duration=.2)

        self._start_time = datetime.utcnow()

    def start_recv(self):
        try:
            self.CONNECTION_STABLISHED = True
            print(self.CONNECTION_STABLISHED)
        except:
            toast("No Connection Stablished, plz check your IP or/and PORT")
            return 

        if not self.FEED_STARTED and self.CONNECTION_STABLISHED:
            self.recv_data_thread =  Thread(target=self.recv_data) 
            self.texture_scheduler = Clock.schedule_interval(self.change_texture_callback, 0.0)
            self.recv_data_thread.start()

        self.FEED_STARTED = True
        
    def __wait_till_ready(self):
        
        self.receiver_socket.sendto(b'server', ADDR)

        while True:
            data = self.receiver_socket.recv(1024).decode()

            if data.strip() == 'ready':
                Logger.info('checked in with server, waiting')
                break

        data = self.receiver_socket.recv(1024).decode()

        ip, sport, _ = data.split(' ')
        sport = int(sport)

        self.__sender_ip = ip
        self.__sender_port = sport

        print(self.__sender_ip, self.__sender_port)

        self.receiver_socket.connect((self.__sender_ip, self.__sender_port))
        Logger.info("connected to the drone client with {}:{}".format(self.__sender_ip, self.__sender_port))

    def change_texture_callback(self, *a):

        if not self.STARTED: return

        # self.gyroscope._angle = math.degrees(random.random())

        if self.my_frame is not None:

            f = BytesIO()
            f.write(self.my_frame)
            f.seek(0)

            cm = CoreImage(f, ext='jpeg', anim_delay=0.0)
            if self.CHANGE_FULL_FEED:
                self.drone_camera_feed.texture = cm.texture
            else:
                self.drone_camera_feed_thumbnail.feed.texture = cm.texture

        
    def recv_data(self):
        self.__wait_till_ready()

        if not self.STARTED: return

        while True:
            if self.STOP: break
            
            data, _ = self.receiver_socket.recvfrom(BUFF)

            buffer = base64.b64decode(data, ' /')

            self.my_frame = buffer

            time.sleep(1./20.)

    def send_commands_collback(self, e):
        if self.send_command_clock:
            Clock.unschedule(self.send_command_clock)
        self.send_data(e.command)
        self.send_command_clock = Clock.schedule_interval(lambda _: self.send_data(e.command), 1)

    def on_release_command(self, e):
        Clock.unschedule(self.send_command_clock)
        self.send_data('stop')
        
    def send_data(self, data, addr=SIM_ADDR):
        try:
            sim_socket.sendto(data.encode(), addr)
        except Exception as e:
            Logger.error(str(e))


    def recv_status_callback(self):
        while True:
            
            time.sleep(.5)
            
    def close_recv(self):
        if self.FEED_STARTED:
            self.CLOSE_SIGNAL = True
            self.texture_scheduler.cancel()
            self.STOP = True
        self.FEED_STARTED = False


    def on_start(self):
        self.gyroscope = self.root._controll_layer._gyroscope
        self.setting_panel = self.root._setting_panel
        self.panel_manager = self.setting_panel.panel_manager
        self.camera_feed_layer = self.root._camera_feed_layer
        self.statusbar = self.root.statusbar
        self.flight_mode = self.statusbar.flight_mode
        self.armed_indecator = self.statusbar.armed_indecator

        self.drone_camera_feed = self.camera_feed_layer.drone_camera_feed

        # get the info widget proxy
        _info_layer = self.root._info_layer
        self.device_info = _info_layer._device_info
        # self.camera_info = _info_layer._camera_info
        self.rotation_info = _info_layer._rotation_info
        self.altitude_info = _info_layer._altitude_info
        self.speed_info = _info_layer._speed_info
        self.partial_speed_info = _info_layer._partial_speed_info
        self.flight_time_info = _info_layer._flight_time_info

        self._map_layer = self.root._map_layer
        self.dronesmap = self._map_layer.dronesmap
        self.dronemarker = self.dronesmap.dronemarker
        self.homemarker = self.dronesmap.homemarker
        
        # plyer.accelerometer.enable()


        # self.sensors_callback = Clock.schedule_interval(self.read_sensors, 1./30.)
        # self.sensors_thread = Thread(target=self.read_sensors, args=(self.gyroscope,))
        # self.sensors_thread.start()

        if platform == 'android':
            plyer.orientation.set_landscape()

    def save_feed_frame(self):
        try:
            has_perms = check_permission('android.permission.WRITE_EXTERNAL_STORAGE')
            if not has_perms:
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        except Exception as e:
            Logger.error(str(e))

        image_path = Path(plyer.storagepath.get_pictures_dir()) / 'hawkeye_screenshots'

        if not image_path.is_dir():
            Logger.debug('created the screenshots path')
            image_path.mkdir()

        if self.my_frame:
            im = PILImage.open(BytesIO(self.my_frame))
            im_filename = '[{}]-hawkeye-image.png'.format(datetime.utcnow().strftime("%Y:%m:%d-%H:%M:%S"))
            try:
                im.save(image_path / im_filename)
                toast('{} saved successfully'.format(im_filename))
                return 
            except Exception as e:
                Logger.error(type(e) + str(e))

        toast('Image not saved try again')

    def change_frame_size(self, e):
        if e.text == '16:9':
            self.drone_camera_feed.width = Window.height * 16./9.
        elif e.text == '4:3':
            self.drone_camera_feed.width = Window.height * 4./3.
        elif e.text == 'Full':
            self.drone_camera_feed.width = Window.width
        else:
            pass

    def send_command(self, command_code):
        self.send_data(command_code)

        if command_code == '1':
            plyer.tts.speak('Arming the Drone.')
            plyer.tts.speak('Begining the asending proccess.')

        elif command_code == '11':
            plyer.tts.speak('Returning to home.')


    def change_panel_screen(self, e):
        screenname = e.text.lower()
        screennames = ['safety', 'camera', 'control', 'transimission', 'tutorial', 'about']
        if not screenname in screennames:
            return

        for ph in self.setting_panel.panel_header:
            ph.toggled = False

        e.toggled = True

        sn_idx = screennames.index(screenname)
        cur_sn_idx = screennames.index(self.panel_manager.current)
        self.panel_manager.current = screenname
        self.panel_manager.transition.direction = 'left' if sn_idx < cur_sn_idx else 'right'

    @staticmethod
    def euc_velocity(itr):
        dis = itr[0]**2 + itr[1]**2 + itr[2]**2
        return math.sqrt(dis)

    def update_info_layer_values(self):
        
        self.data_recv_socket.sendto(b'ready', ('192.168.1.11', 5005))

        while True:
            if self.CLOSE_SIGNAL: break

            data, addr = self.data_recv_socket.recvfrom(1024)
            drone_data = DroneData()
            drone_data.ParseFromString(data)

            if self.STOP_READING: break

            self.device_info.bat  = str(round(drone_data.bat, 1))
            self.device_info.vltg = str(round(drone_data.vltg, 1))
            self.device_info.temp = str(round(random.random()*50, 1))
            self.dronemarker.lat = drone_data.lat
            self.dronemarker.lon = drone_data.lon

            self.homemarker.lat = drone_data.home_lat
            self.homemarker.lon = drone_data.home_lon

            self.rotation_info.pitch = str(round(math.degrees(drone_data.pitch), 2))
            self.rotation_info.yaw = str(round(math.degrees(drone_data.yaw), 2))
            self.rotation_info.roll = str(round(math.degrees(drone_data.roll), 2))

            self.gyroscope.roll_angle = math.degrees(-drone_data.roll)
            self.gyroscope.yaw_angle = math.degrees(-drone_data.yaw)
            self.gyroscope.pitch_angle = -drone_data.pitch

            self.altitude_info.alt = str(round(drone_data.alt, 2))
            
            self.speed_info.speed = str(round(self.euc_velocity(drone_data.speed), 2))
            self.partial_speed_info.vx =  round(drone_data.speed[0], 1)
            self.partial_speed_info.vy =  round(drone_data.speed[1], 1)
            self.partial_speed_info.vz =  round(drone_data.speed[2], 1)

            self.flight_mode.text = drone_data.mode
            
            self.armed_indecator.armed = drone_data.armed

            self.flight_time_info.time = str(datetime.utcnow()-self._start_time).split('.')[0]

    def toggle_map_view(self, e):
        
        if not self.MAP_TOGGLED:
            e.icon = "fullscreen-exit"
            self.an_full.start(e.parent)
            self.an_defull_vid.start(self.camera_feed_layer)
            Window.add_widget(self.drone_camera_feed_thumbnail)
            
        else:
            e.icon = "fullscreen"
            self.an_defull.start(e.parent)
            self.an_full_vid.start(self.camera_feed_layer)
            Window.remove_widget(self.drone_camera_feed_thumbnail)
        
        self.MAP_TOGGLED = not self.MAP_TOGGLED
        self.CHANGE_FULL_FEED = not self.CHANGE_FULL_FEED


    def read_sensors(self, e):
        while True:
            if self.STOP_READING: break

            x, y, z = random.random(),random.random(),random.random()
            if y:
                e._angle = math.degrees(-y/2)

    def on_stop(self):
        self.STOP_READING = True
        
        self.send_data('quit', ('192.168.1.11', 5555))
        self.send_data('0', SIM_ADDR)
        self.STOP = True
        self.receiver_socket.close()
        if self.CONNECTION_STABLISHED:
            self.CLOSE_SIGNAL = True
            self.texture_scheduler.cancel()
        self.receiver_socket.close()


        # plyer.accelerometer.disable()
        
    def build(self):
        
        return Builder.load_file('./main.kv')

if __name__ == '__main__':
    DJIMainApp().run()
