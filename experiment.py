from queue import Queue
import threading

from mokumoku import Game
import gopro_ctrl

if __name__ == "__main__":
    que_game_to_cv2 = Queue()
    que_cv2_to_game = Queue()

    ## 撮影条件
    horizon_mode = True
    duration_sec = 60

    loop_thread = threading.Thread(
        target=gopro_ctrl.loop,
        args=(que_game_to_cv2, que_cv2_to_game, duration_sec, horizon_mode))
    loop_thread.start()

    print("START")
    game = Game()
    game.run(que_cv2_to_game, que_game_to_cv2)
