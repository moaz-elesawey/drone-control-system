import time

from dronekit import Vehicle
from drone_data_pb2 import DroneData
import socket
from threading import Thread


CONTROLLER_ADDR = ('192.168.1.11', 5005)
MONITOR_ADDR = ('192.168.1.11', 5006)

class Sender(Thread):
    def __init__(self, drone):
        super().__init__()

        self.__terminate_signal = False
        self.drone = drone

        self.v = drone.vehicle

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(CONTROLLER_ADDR)

    def run(self) -> None:
        v :Vehicle = self.drone.vehicle
        
        _, addr = self.sock.recvfrom(1024)

        __home_lat = v.location.global_relative_frame.lat
        __home_lon = v.location.global_relative_frame.lon

        while not self.__terminate_signal:
            try:
                drone_data = DroneData()
                drone_data.alt = v.location.global_relative_frame.alt
                drone_data.lat = v.location.global_relative_frame.lat
                drone_data.lon = v.location.global_relative_frame.lon
                drone_data.home_lat = __home_lat
                drone_data.home_lon = __home_lon
                drone_data.speed.extend(v.velocity)
                drone_data.airspeed = v.airspeed
                drone_data.groundspeed = v.groundspeed
                drone_data.pitch = v.attitude.pitch
                drone_data.yaw = v.attitude.yaw
                drone_data.roll = v.attitude.roll
                drone_data.bat = v.battery.level
                drone_data.vltg = v.battery.voltage
                drone_data.current = v.battery.current
                drone_data.distance = v.rangefinder.distance if v.rangefinder.distance else -1.0
                drone_data.mode = v.mode.name
                drone_data.armed = v.armed

                payload = drone_data.SerializeToString()

                self.sock.sendto(payload, addr)
                self.sock.sendto(payload, MONITOR_ADDR)
                time.sleep(1./25.)

            except KeyboardInterrupt:
                self.terminate()

            except Exception as e:
                print(str(e))
        return super().run()


    def terminate(self):
        self.__terminate_signal = True
