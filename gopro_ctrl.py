# pip install open-gopro
import logging
logging.basicConfig(level=logging.WARN)

import datetime
import time
from open_gopro import WirelessGoPro, Params, constants

class AutoGoPro:
    def __init__(self):
        self.gopro = WirelessGoPro(enable_wifi = False)
    
    def connect(self, horizon_mode=False):
        self.gopro.open()

        stat = self.gopro.ble_command.get_camera_statuses()
        if stat[constants.StatusId.SD_STATUS] == Params.SDStatus.REMOVED:
            print("SD card removed!")
            return False

        self.gopro.ble_setting.resolution.set(Params.Resolution.RES_4K_4_3)
#        gopro.ble_setting.resolution.set(Params.Resolution.RES_2_7K_4_3)
        self.gopro.ble_setting.fps.set(Params.FPS.FPS_60)
        ret = self.gopro.ble_command.set_date_time(date_time=datetime.datetime.now())
        print(ret)
        if horizon_mode == True:
            self.gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.ON)
            self.gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR_HORIZON_LEVELING)
            self.gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.ON)
        else:
            self.gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.OFF)
            self.gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR)
            self.gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.OFF)

        settings = self.gopro.ble_command.get_camera_settings()
        return True
    
    def start(self):
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)

    def stop(self):
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        self.gopro.close()

def loop(que_in, que_out, duration_sec, horizon_mode):
    agp = AutoGoPro()
    que_out.put('GAME_INIT')

    response = agp.connect(horizon_mode=horizon_mode)
    if response == True:
        que_out.put('GAME_START')
    else:
        # SDCardREMOVEDならゲームを開始しない
        que_out.put('GAME_QUIT')
        return
    agp.start()
    time.sleep(duration_sec)
    que_out.put('GAME_END')
    time.sleep(1)
    agp.stop()
    que_out.put('GAME_QUIT')

def test(duration_sec):
    agp = AutoGoPro()
    response = agp.connect()
    agp.start()
    time.sleep(duration_sec)
    agp.stop()


if __name__ == "__main__":
    test(5)