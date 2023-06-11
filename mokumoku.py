from queue import Queue
import threading
import random
import itertools
import pyxel

from PIL import Image
import cv2

import image_show
import game_object

BLK = 16

img = cv2.imread('./img/a.jpg')
cv2.imshow('cap', img)

class Game:
    STORAGE_NUM = 5
    PRODUCT_NUM = 5
    CLOCK_PERIOD = 240

    def __init__(self):
        self.clock = 0
        self.materials: list[game_object.Material] = [game_object.Material(code) for code in ['yellow_juel', 'red_juel', 'blue_juel', 'green_juel', 'yellow_rod', 'red_rod', 'blue_rod', 'green_rod']]
        self.worker = game_object.Worker(7*BLK, BLK)
        self.storages: list[game_object.Storage] = [game_object.Storage(i, 5*BLK, 2*BLK + i*2*BLK) for i in range(self.STORAGE_NUM)]
        self.products: list[game_object.Product] = [game_object.Product(i, 16*BLK, 2*BLK + i*2*BLK, self.materials) for i in range(self.PRODUCT_NUM)]
        self.trash = game_object.Trash(7*BLK, 12*BLK)
        self.fps_disp = ''

        pyxel.init(20*BLK, 13*BLK)
        pyxel.load('./mokumoku.pyxres')

    def run(self, que_in, que_out):
        self.que_in = que_in
        self.que_out = que_out

        ## 別スレッドからqueueが入ってくるまでブロック
        print(self.que_in.get())

        ## フレーム更新時にupdate、描画時にdrawを実行する
        pyxel.run(self.update, self.draw)

    def update(self):
        ## image_showにQUITを送ってカメラと動画ファイルを閉じさせる
        ## 先に動画ファイルを閉じてからゲームを終了させる必要があるため
        if pyxel.btnp(pyxel.KEY_Q):
            self.que_out.put('QUIT')

        if self.que_in.qsize() > 0:
            got_msg = self.que_in.get()
            ## image_showからQUITが送り返されてきたらゲームを終了
            if got_msg == 'QUIT':
                pyxel.quit()
            else:
                self.fps_disp = got_msg

        ## 時計の針を進める
        if self.clock > self.CLOCK_PERIOD:
            self.clock = 0
        else:
            self.clock += 1

        ## 移動キーの判定
        directions = []
        if pyxel.btn(pyxel.KEY_D):
            directions.append('right')
        if pyxel.btn(pyxel.KEY_A):
            directions.append('left')
        if pyxel.btn(pyxel.KEY_W):
            directions.append('up')
        if pyxel.btn(pyxel.KEY_S):
            directions.append('down')

        self.worker.update_clock(self.clock)
        self.worker.move(4, directions)

        ## 倉庫の処理
        all_needs = list(itertools.chain.from_iterable([x.needs for x in self.products]))
        if len(all_needs) > self.STORAGE_NUM:
            add_materials = random.sample(all_needs, self.STORAGE_NUM)
        else:
            add_materials = random.sample(self.materials, self.STORAGE_NUM)
        for storage, material in zip(self.storages, add_materials):
            storage.update_clock(self.clock)
            storage.add_material(material)

            ## ワーカーが材料を入手する処理
            if pyxel.btn(pyxel.KEY_J) and\
                    storage.is_near(self.worker) == True and\
                    self.worker.get_slot('j') is None:
                self.worker.prop_material('j', storage.pop_material())
                storage.add_cnt()
            if pyxel.btn(pyxel.KEY_K) and\
                    storage.is_near(self.worker) == True and\
                    self.worker.get_slot('k') is None:
                self.worker.prop_material('k', storage.pop_material())
                storage.add_cnt()

        ## 製品の処理
        for product in self.products:
            ## ワーカーが材料を設置する処理
            if pyxel.btn(pyxel.KEY_J) and\
                    product.is_near(self.worker) == True and\
                    self.worker.get_slot('j') is not None and\
                    self.worker.get_slot('j') in product.needs:
                product.add_material(self.worker.place_material('j'))
            elif pyxel.btn(pyxel.KEY_K) and\
                    product.is_near(self.worker) == True and\
                    self.worker.get_slot('k') is not None and\
                    self.worker.get_slot('k') in product.needs:
                product.add_material(self.worker.place_material('k'))

            ## 完成したらリセット
            if len(product.needs) == 0:
                product.reset()
                product.add_cnt()
                img = cv2.imread('./img/b.jpg')
                cv2.imshow('cap', img)

        ## ゴミ箱の処理
        if pyxel.btn(pyxel.KEY_J) and\
               self.trash.is_near(self.worker) == True and\
               self.worker.get_slot('j') is not None:
           self.worker.place_material('j')
           self.trash.add_cnt()
        elif pyxel.btn(pyxel.KEY_K) and\
               self.trash.is_near(self.worker) == True and\
               self.worker.get_slot('k') is not None:
           self.worker.place_material('k')
           self.trash.add_cnt()

    def draw(self):
        pyxel.cls(0)

        ## タイルマップを描画
        pyxel.bltm(0, 0, 0, 0, 0, 20*BLK, 13*BLK)

        ## 倉庫を描画
        for storage in self.storages:
            storage.blt()

        ## 製品を描画
        for product in self.products:
            product.blt()

        ## ワーカーを描画
        self.worker.blt()

        ## テキストを描画
        storage_score = sum([i.cnt for i in self.storages]) * 10
        product_score = sum([i.cnt for i in self.products]) * 100
        trash_score = self.trash.cnt * 10
        score = product_score + storage_score - trash_score

        pyxel.text(8, 2*BLK, self.fps_disp, 7)
        pyxel.text(8, BLK, f"SCORE: {score:>5}", 7)

if __name__ == "__main__":
    que_game_to_cv2 = Queue()
    que_cv2_to_game = Queue()
    loop_thread = threading.Thread(target=image_show.loop, args=(que_game_to_cv2, que_cv2_to_game))
    loop_thread.start()

    game = Game()
    game.run(que_cv2_to_game, que_game_to_cv2)
