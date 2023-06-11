import random
import itertools

import pyxel

import game_object

BLK = 16

class Game:
    STORAGE_NUM = 5
    PRODUCT_NUM = 5
    CLOCK_PERIOD = 240

    def __init__(self):
        self.clock = 0
        self.scene = 0
        self.materials: list[game_object.Material] = [game_object.Material(code) for code in ['yellow_juel', 'red_juel', 'blue_juel', 'green_juel', 'yellow_rod', 'red_rod', 'blue_rod', 'green_rod']]
        self.worker = game_object.Worker(7*BLK, BLK)
        self.storages: list[game_object.Storage] = [game_object.Storage(i, 5*BLK, 2*BLK + i*2*BLK) for i in range(self.STORAGE_NUM)]
        self.products: list[game_object.Product] = [game_object.Product(i, 16*BLK, 2*BLK + i*2*BLK, self.materials) for i in range(self.PRODUCT_NUM)]
        self.trash = game_object.Trash(7*BLK, 12*BLK)
        self.fps_disp = ''

        pyxel.init(20*BLK, 13*BLK)
        pyxel.load('./mokumoku.pyxres')

    def run(self, que_in=None, que_out=None):
        self.que_in = que_in
        self.que_out = que_out

        if self.que_in is not None:
            ## 別スレッドからqueueが入ってくるまでブロック
            print(self.que_in.get())

        ## フレーム更新時にupdate、描画時にdrawを実行する
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            if self.que_out is not None:
                ## image_showにQUITを送ってカメラと動画ファイルを閉じさせる
                ## 先に動画ファイルを閉じてからゲームを終了させる必要があるため
                self.que_out.put('QUIT')
            else:
                pyxel.quit()

        if self.que_in is not None:
            if self.que_in.qsize() > 0:
                got_msg = self.que_in.get()
                ## image_showからQUITが送り返されてきたらゲームを終了
                if got_msg == 'QUIT':
                    pyxel.quit()
                else:
                    self.fps_disp = got_msg

        ## シーン0
        if pyxel.btnp(pyxel.KEY_SPACE) and self.scene==0:
            self.scene = 1

        ## シーン1
        if self.scene == 1:
            self._scene_1()

    def _scene_1(self):
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

        ## 倉庫に入れる材料の選定
        all_needs = list(itertools.chain.from_iterable([x.needs for x in self.products]))
        if len(all_needs) > self.STORAGE_NUM:
            add_materials = random.sample(all_needs, self.STORAGE_NUM)
        else:
            add_materials = random.sample(self.materials, self.STORAGE_NUM)
        ## 倉庫の処理
        for storage, material in zip(self.storages, add_materials):
            self._storage_worker(storage, self.worker, material)

        ## 製品の処理
        for product in self.products:
            complete = self._product_worker(product, self.worker)

        self._trash_worker(self.trash, self.worker)


    ## 倉庫の処理
    ## material: 倉庫に入れる材料
    def _storage_worker(self, storage, worker, material):
        btn_dict = {'j':pyxel.KEY_J, 'k':pyxel.KEY_K}
        storage.update_clock()
        storage.add_material(material)

        ## ワーカーが材料を入手する処理
        for k,btn in btn_dict.items():
            if pyxel.btn(btn) and\
                    storage.is_near(worker) == True and\
                    worker.get_slot(k) is None:
                worker.prop_material(k, storage.pop_material())
                storage.add_cnt()

    ## 製品の処理
    def _product_worker(self, product, worker):
        complete = False
        btn_dict = {'j':pyxel.KEY_J, 'k':pyxel.KEY_K}
        ## ワーカーが材料を設置する処理
        for k,btn in btn_dict.items():
            if pyxel.btn(btn) and\
                    product.is_near(worker) == True and\
                    worker.get_slot(k) is not None and\
                    worker.get_slot(k) in product.needs:
                product.add_material(worker.place_material(k))

        ## 完成したらリセット
        if len(product.needs) == 0:
            product.reset()
            product.add_cnt()
            complete = True
        return complete

    ## ゴミ箱の処理
    def _trash_worker(self, trash, worker):
        btn_dict = {'j':pyxel.KEY_J, 'k':pyxel.KEY_K}
        for k,btn in btn_dict.items():
            if pyxel.btn(btn) and\
                   trash.is_near(worker) == True and\
                   worker.get_slot(k) is not None:
               worker.place_material(k)
               trash.add_cnt()

    def draw(self):
        pyxel.cls(0)

        if self.scene == 1:
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
    game = Game()
    game.run()
