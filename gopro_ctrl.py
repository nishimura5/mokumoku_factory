# pip install open-gopro

'''
メモ
mainからmokumokuとgopro_ctrlをマルチスレッドで呼ぶ
gopro_ctrlは設定の固定化と自動撮影開始・自動撮影終了を担う、時刻設定も試す
タイムラグ(ゲーム開始タイミングと撮影開始の同期)の性能を確認する。
1secくらいの誤差ならゲームから音を出して調整できる。
10sec以上になってくると探すのがちょっと辛いが、傾向が一様ならディレイを入れて調整できるかも

実験者がプログラムを実行
プレイヤーは自分のタイミングでゲームを開始
カメラの設定と録画をスタート
ゲームをスタート
N分後にゲームを自動で終了
カメラの録画をストップ

ゲームのログと動画を一つのフォルダにれて管理
'''

import datetime
import time
from open_gopro import WirelessGoPro, Params

HORIZON = False

def start():
    with WirelessGoPro(enable_wifi = False) as gopro:
        print('START')
        gopro.ble_setting.resolution.set(Params.Resolution.RES_4K_4_3)
#        gopro.ble_setting.resolution.set(Params.Resolution.RES_2_7K_4_3)
        gopro.ble_setting.fps.set(Params.FPS.FPS_60)
        ret = gopro.ble_command.set_date_time(date_time=datetime.datetime.now())
        print(ret)
        if HORIZON == True:
            gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.ON)
            gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR_HORIZON_LEVELING)
            gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.ON)
        else:
            gopro.ble_setting.hypersmooth.set(Params.HypersmoothMode.OFF)
            gopro.ble_setting.video_field_of_view.set(Params.VideoFOV.LINEAR)
            gopro.ble_setting.video_horizon_leveling.set(Params.HorizonLeveling.OFF)

        response = gopro.ble_command.get_camera_settings()
        print(response)

        gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
#        response = gopro.ble_command.tag_hilight()
#        print(response)
#        print(response.status)

def stop():
    with WirelessGoPro(enable_wifi = False) as gopro:
        gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
    print('STOP')

def loop(que_in, que_out, duration_sec):
    start()
    que_out.put('START')
    time.sleep(duration_sec)
    stop()
    que_out.put('QUIT')
