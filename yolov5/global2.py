def __init__():
    global camera_flag
    camera_flag = True


def change_value(val):
    camera_flag = val


def get_value():
    return camera_flag

