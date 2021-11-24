class CODE:
    ARM_AND_TAKEOFF     = 1
    INCREASE_ALT        = 2
    DECREASE_ALT        = 3
    ROTATE_LEFT         = 4
    ROTATE_RIGHT        = 5
    FOREWARD            = 6
    BACKWARD            = 7
    LEFT                = 8
    RIGHT               = 9
    DROP_PACKGE         = 10
    RETURN_HOME         = 11
    LAND                = 12
    CAMERA_UP           = 13
    CAMERA_DOWN         = 14
    DISARM              = 15
    STOP_VERTICAL       = 16
    STOP_HORIZONTAL     = 17


class Command:
    def __init__(self, code):
        self.code = code
