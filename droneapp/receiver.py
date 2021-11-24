from sender import Sender
from drone_data_pb2 import DroneData
import logging
import time
from codes import Command
from drone import Drone
from threading import Thread
import socket


class Receiver(Thread):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self.drone = Drone('127.0.0.1', 14551)
         
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('192.168.1.11', 5002))

        self.__terminate_signal = False

        self.sender_thread = Sender(self.drone)
        self.sender_thread.start()

        logging.info('Reveiver thread started')

    def run(self) -> None:
        v = self.drone.vehicle

        while not self.__terminate_signal:
            try:
                data, addr = self.sock.recvfrom(4*1024)

                command = Command(int(data.decode()))
                self.drone.execute_command(command)

            except Exception as e:
                print(str(e))
            # time.sleep(5)
        return super().run()

    def terminate(self):
        self.__terminate_signal = True
