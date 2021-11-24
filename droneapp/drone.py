import logging
from dronekit import connect, VehicleMode, LocationGlobalRelative

from codes import CODE

from controller import Controller
from codes import CODE, Command


logger = logging.getLogger()

class Drone:
    def __init__(self, drone_ip, drone_port):
        self._drone_state = 'DISARMED'
        self.vehicle = connect("{}:{}".format(drone_ip, drone_port), wait_ready=True)

        self.controller = Controller(self)

    
    def execute_command(self, command: Command):
        if command.code == CODE.ARM_AND_TAKEOFF:
            print('Executed command CODE.ARM_AND_TAKEOFF')
            self.controller.arm_and_takeoff(20)
            return
        elif command.code == CODE.INCREASE_ALT:
            print('Executed Command {}'.format(command.code))
            self.controller.increase_speed_z()
            return

        elif command.code == CODE.DECREASE_ALT:
            print('Executed Command {}'.format(command.code))
            self.controller.decrease_speed_z()
            return

        elif command.code == CODE.ROTATE_LEFT:
            print('Executed Command {}'.format(command.code))
            self.controller.rotate(-1, 10)
            return

        elif command.code == CODE.ROTATE_RIGHT:
            print('Executed Command {}'.format(command.code))
            self.controller.rotate(1, 10)
            return

        elif command.code == CODE.FOREWARD:
            print('Executed Command Foreward')
            self.controller.increase_speed_x()
            return

        elif command.code == CODE.BACKWARD:
            print('Executed Command Backward')
            self.controller.decrease_speed_x()
            return

        elif command.code == CODE.LEFT:
            print('Executed Command Left')
            self.controller.increase_speed_y()
            return

        elif command.code == CODE.RIGHT:
            print('Executed Command right')
            self.controller.decrease_speed_y()
            return

        elif command.code == CODE.STOP_VERTICAL:
            print('Executed Command STOP VERTICAL')
            self.controller.stop_speed_z()
            return

        elif command.code == CODE.STOP_HORIZONTAL:
            print('Executed Command STOP HORIZONTAL')
            self.controller.stop_speed_xy()
            return

        elif command.code == CODE.DROP_PACKGE:
            print('Executed Command {}'.format(command.code))
            return

        elif command.code == CODE.RETURN_HOME:
            print('Executed Command {}'.format(command.code))
            self.controller.return_home(40)
            return

        elif command.code == CODE.LAND:
            print('Executed Command {}'.format(command.code))
            self.controller.land()
            return

        elif command.code == CODE.CAMERA_DOWN:
            print('Executed Command {}'.format(command.code))
            return

        elif command.code == CODE.CAMERA_UP:
            print('Executed Command {}'.format(command.code))
            return

        elif command.code == CODE.DISARM:
            print('Executed Command {}'.format(command.code))
            return

        