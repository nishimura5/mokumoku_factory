# pip install open-gopro

import datetime
import time
from open_gopro import WirelessGoPro, Params

def start(horizon_mode=False):
    with WirelessGoPro(enable_wifi = False) as gopro:
        print('START')
        gopro.ble_setting.resolution.set(Params.Resolution.RES_4K_4_3)
#        gopro.ble_setting.resolution.set(Params.Resolution.RES_2_7K_4_3)
        gopro.ble_setting.fps.set(Params.FPS.FPS_60)
        ret = gopro.ble_command.set_date_time(date_time=datetime.datetime.now())
        print(ret)
        if horizon_mode == True:
            gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.ON)
            gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR_HORIZON_LEVELING)
            gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.ON)
        else:
            gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.OFF)
            gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR)
            gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.OFF)

        response = gopro.ble_command.get_camera_settings()

        gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
    return response

def stop():
    with WirelessGoPro(enable_wifi = False) as gopro:
        gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
    print('STOP')

def loop(que_in, que_out, duration_sec, horizon_mode):
    response = start(horizon_mode=horizon_mode)
    print(response)
    que_out.put('START')
    time.sleep(duration_sec)
    stop()
    que_out.put('QUIT')
