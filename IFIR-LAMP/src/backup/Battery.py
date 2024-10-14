# -*- coding: utf-8 -*-
""" 获取电池电量的API """
try:
    from pisugar import *
except Exception as e:
    print("当前系统不支持PiSugar")


def getPower():
    try:
        conn, event_conn = connect_tcp('raspberrypi.local')
        server = PiSugarServer(conn, event_conn)
        server.register_single_tap_handler(lambda: print('single'))
        server.register_double_tap_handler(lambda: print('double'))
        level = server.get_battery_level()
        charging = server.get_battery_charging()
        return level, charging
    except Exception:
        return 0, False


if __name__ == "__main__":
    print(getPower())

