from queue import Queue
import threading

from mokumoku import Game
import gopro_ctrl

if __name__ == "__main__":
    que_game_to_cv2 = Queue()
    que_cv2_to_game = Queue()

    loop_thread = threading.Thread(target=gopro_ctrl.loop, args=(que_game_to_cv2, que_cv2_to_game, 60))
    loop_thread.start()

    game = Game()
    game.run(que_cv2_to_game, que_game_to_cv2)
