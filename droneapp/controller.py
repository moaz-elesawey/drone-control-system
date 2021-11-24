from threading import Thread
import time
from dronekit import Vehicle, VehicleMode
from pymavlink import mavutil

class Controller:
    def __init__(self, drone):
        self.drone = drone
        self.v : Vehicle = drone.vehicle

        self.speed_x     = 0
        self.speed_y     = 0
        self.speed_z     = 0

        self.speed_increment_x = .5
        self.speed_increment_y = .5
        self.speed_increment_z = .2
        
        self.rotation_angle = 10

        self.alt         = 0
        self.airspeed    = 0
        self.groundspeed = 0
        self.lat         = 0
        self.lon         = 0

        self.exec_thread = Thread(target=self.send_command_exec)
        self.exec_thread.start()

    def exec_now(self):

        print(self.speed_x, self.speed_y, self.speed_z)

        # self.v.mode = VehicleMode("GUIDED")
        msg = self.v.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_BODY_NED, # frame
            0b0000111111000111, # type_mask (only positions enabled)
            0, 0, 0,
            self.speed_x, self.speed_y, self.speed_z,
            0, 0, 0,
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

        self.v.send_mavlink(msg)
        self.v.flush()

    def rotate(self, direction, angle):
        msg = self.v.message_factory.command_long_encode(
            0,0,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,
            angle,
            1,
            direction,
            1,
            0,0,0
        )

        self.v.send_mavlink(msg)
        self.v.flush()

    def increase_speed_x(self):
        self.speed_x += self.speed_increment_x
        self.exec_now()
    def increase_speed_y(self):
        self.speed_y -= self.speed_increment_y
        self.exec_now()
    def increase_speed_z(self):
        self.speed_z -= self.speed_increment_z
        self.exec_now()

    def decrease_speed_x(self):
        self.speed_x -= self.speed_increment_x
        self.exec_now()
    def decrease_speed_y(self):
        self.speed_y += self.speed_increment_y
        self.exec_now()
    def decrease_speed_z(self):
        self.speed_z += self.speed_increment_z
        self.exec_now()

    def rotate_left(self, angle):
        self.rotate(1, angle)
    def rotate_right(self, angle):
        self.rotate(angle)

    def stop_speed_xy(self):
        self.speed_x = 0
        self.speed_y = 0
        self.exec_now()

    def stop_speed_z(self):
        self.speed_z = 0
        self.exec_now()
    
    def arm_and_takeoff(self, alt):
        self.v.mode = VehicleMode('GUIDED')
        
        self.v.arm()
        self.v.armed = True
        time.sleep(1.)

        while not self.v.is_armable:
            self.v.armed = True
            time.sleep(1.)

        self.v.simple_takeoff(alt)

        while True:
            cur_alt = self.v.location.global_relative_frame.alt

            if cur_alt >= alt*.95:
                self.v.simple_goto( self.v.location.global_relative_frame)
                break
            time.sleep(1.)
    
    def kill_motors(self):
        msg = self.vehicle.message_factory.command_long_encode(
            1, 1,    # target system, target component
            mavutil.mavlink.MAV_CMD_DO_FLIGHTTERMINATION , #command
            1, #confirmation
            1,  # param 1, yaw in degrees
            1,          # param 2, yaw speed deg/s
            1,          # param 3, direction -1 ccw, 1 cw
            True, # param 4, 1 - relative to current position offset, 0 - absolute, angle 0 means North
            0, 0, 0)    # param 5 ~ 7 not used
        self.v.send_mavlink(msg)
        self.v.flush()

    def return_home(self, rtl_alt):
        self.v.mode = VehicleMode('GUIDED')

        for _ in range(0, 10):
            self.increase_speed_z()
            time.sleep(.5)

        while True:
            cur_alt = self.v.location.global_relative_frame.alt
            if cur_alt > rtl_alt * .95:
                self.v.mode = VehicleMode('RTL')
                break
            time.sleep(1.)

    def land(self):
        self.v.channels.overrides = {}
        self.v.mode = VehicleMode('LAND')

    def send_command_exec(self):
        while True:
            try:
                if self.speed_x != 0 or self.speed_y != 0 or self.speed_z != 0:
                    msg = self.v.message_factory.set_position_target_local_ned_encode(
                    0,       # time_boot_ms (not used)
                    0, 0,    # target system, target component
                    mavutil.mavlink.MAV_FRAME_BODY_NED, # frame
                    0b0000111111000111, # type_mask (only positions enabled)
                    0, 0, 0,
                    self.speed_x, self.speed_y, self.speed_z, # x, y, z velocity in m/s
                    0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
                    0, 0)

                    self.v.send_mavlink(msg)
                    self.v.flush()
                time.sleep(1.)

            except Exception as e:
                print("Engine killed: "+str(e))
