import random
import itertools

import pyxel

BLK = 16
IMG_BANK_0 = 0
IMG_BANK_1 = 1

class Game:
    STORAGE_NUM = 5
    PRODUCT_NUM = 5
    CLOCK_PERIOD = 240
    BTN_DICT = {'j':pyxel.KEY_J, 'k':pyxel.KEY_K}

    def __init__(self):
        self.clock = 0
        self.scene = 0
        self.materials: list[Material] = [Material(code) for code in ['yellow_juel', 'red_juel', 'blue_juel', 'green_juel', 'yellow_rod', 'red_rod', 'blue_rod', 'green_rod']]
        self.worker = Worker(7*BLK, BLK)
        self.storages: list[Storage] = [Storage(i, 5*BLK, 2*BLK + i*2*BLK) for i in range(self.STORAGE_NUM)]
        self.products: list[Product] = [Product(i, 16*BLK, 2*BLK + i*2*BLK, self.materials) for i in range(self.PRODUCT_NUM)]
        self.trash = Trash(7*BLK, 12*BLK)
        self.fps_disp = ''

        ## ワーカーが材料の取得に失敗した回数
        self.err_cnt = {k:0 for k in self.BTN_DICT.keys()}
        ## 製品を完成させた回数
        self.complete_cnt = 0

        pyxel.init(20*BLK, 13*BLK, title="mokumoku_factory")
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

        ## ボタン押し間違いカウンター用配列
        stat = {k:{'storage':[], 'product':[], 'trash':0, 'push':pyxel.btnp(v), 'err':False} for k,v in self.BTN_DICT.items()}

        ## 倉庫に入れる材料の選定
        all_needs = list(itertools.chain.from_iterable([x.needs for x in self.products]))
        if len(all_needs) > self.STORAGE_NUM:
            add_materials = random.sample(all_needs, self.STORAGE_NUM)
        else:
            add_materials = random.sample(self.materials, self.STORAGE_NUM)
        ## 倉庫の処理
        for storage, material in zip(self.storages, add_materials):
            result = self._storage_worker(storage, self.worker, material)
            for k in self.BTN_DICT.keys():
                stat[k]['storage'].append(result[k])

        ## 製品の処理
        for product in self.products:
            complete, result = self._product_worker(product, self.worker)
            self.complete_cnt += complete
            for k in self.BTN_DICT.keys():
                stat[k]['product'].append(result[k])

        result = self._trash_worker(self.trash, self.worker)
        for k in self.BTN_DICT.keys():
            stat[k]['trash'] = result[k]

        ## ボタン押し間違い計算
        for k in self.BTN_DICT.keys():
            ## ボタンを押していないときは評価しない
            if stat[k]['push']==False:
                continue
            ## 倉庫にも製品にも接触してなかったらerr=True
            storage_err = sum([x==-1 for x in stat[k]['storage']]) == self.STORAGE_NUM
            product_err = sum([x==-1 for x in stat[k]['product']]) == self.PRODUCT_NUM
            trash_err = stat[k]['trash'] == -1
            stat[k]['err'] = storage_err and product_err and trash_err

            if stat[k]['err']==True:
                self.err_cnt[k] += 1


        print(self.err_cnt['j'], self.err_cnt['k'], self.complete_cnt)

    ## 倉庫の処理
    ## material: 倉庫に入れる材料
    ## ret: ワーカーが何か手に入れたら1,空振りなら-1,ボタンを押してなければ0
    def _storage_worker(self, storage, worker, material):
        """
        ワーカーは倉庫から材料を受け取る。
        プレイヤーがボタンを押したとき、近くに当該倉庫がなければretval=-1、倉庫があっても材料を受け取れなければretval=-1、
        倉庫があり、かつ材料を受け取れればretval=1を返す。
        ボタンを押さなければretval=0を返す。
        """
        storage.update_clock()
        storage.add_material(material)

        retval = {k:0 for k in self.BTN_DICT.keys()}
        ## ワーカーが材料を入手する処理
        for k,btn in self.BTN_DICT.items():
            if pyxel.btn(btn):
                if storage.is_near(worker) == True and worker.get_slot(k) is None:
                    worker.prop_material(k, storage.pop_material())
                    storage.add_cnt()
                    retval[k] = 1
                    break
                else:
                    retval[k] = -1
        return retval

    def _product_worker(self, product, worker):
        """
        製品はワーカーから材料を受け取り、製品を進捗する。
        製品が完成したらcomplete=1、完成しなければcomplete=0を返す。
        プレイヤーがボタンを押したとき、近くに当該製品がなければretval=-1、倉庫があっても材料を受け取れなければretval=-1、
        倉庫があり、かつ材料を受け取れればretval=1を返す。
        ボタンを押さなければretval=0を返す。
        """
        retval = {k:0 for k in self.BTN_DICT.keys()}
        complete = 0
        ## ワーカーが材料を設置する処理
        for k,btn in self.BTN_DICT.items():
            if pyxel.btn(btn):
                if product.is_near(worker) == True and\
                        worker.get_slot(k) is not None and\
                        worker.get_slot(k) in product.needs:
                    product.add_material(worker.place_material(k))
                    retval[k] = 1
                    break
                else:
                    retval[k] = -1

        ## 完成したらリセット
        if len(product.needs) == 0:
            product.reset()
            product.add_cnt()
            complete = 1
        return complete, retval

    ## ゴミ箱の処理
    def _trash_worker(self, trash, worker):
        """
        ゴミ箱はワーカーから材料を受け取る。
        プレイヤーがボタンを押したとき、近くに当該ゴミ箱がなければretval=-1、ゴミ箱があっても材料を受け取れなければretval=-1、
        ゴミ箱があり、かつ材料を受け取れればretval=1を返す。
        ボタンを押さなければretval=0を返す。
        """
        retval = {k:0 for k in self.BTN_DICT.keys()}
        for k,btn in self.BTN_DICT.items():
            if pyxel.btn(btn) and trash.is_near(worker) == True and worker.get_slot(k) is not None:
                worker.place_material(k)
                trash.add_cnt()
                retval[k] = 1
                break
            else:
                retval[k] = -1
        return retval


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

class Worker:
    def __init__(self, init_x, init_y):
        self.is_active = True
        self.clock_max = 2
        self.x = init_x
        self.y = init_y
        self.direction = 'down'

        ## スロットコードはボタンに対応
        self.slot: dict[str, Material] = {'j':None, 'k':None}

    def update_clock(self, clock_val):
        if clock_val % self.clock_max == 0:
            self.is_active = True
        else:
            self.is_active = False

    def get_slot(self, slot_code):
        return self.slot[slot_code]

    def prop_material(self, slot_code, material):
        if material is None:
            return 
        self.slot[slot_code] = material
    
    def place_material(self, slot_code):
        ret_material = None
        ## スロットに何か入っていたらその材料を返す
        if self.slot[slot_code] is not None:
            ret_material = self.slot[slot_code]
            self.slot[slot_code] = None
        return ret_material

    ## 右・上同時押しすると斜めに移動、右側だけに障害物があったら上にだけ移動する、他の方向も同じ
    ## 右・左同時押しは想定していないけどたぶん問題ない(その場にとどまる？)
    def move(self, speed, directions):
        if self.is_active == False:
            return
        next_x = self.x
        next_y = self.y
        now_x1 = (self.x+2)//8
        now_x2 = (self.x+13)//8
        now_y1 = (self.y+8)//8
        now_y2 = (self.y+13)//8
        if 'right' in directions:
            next_x += speed
            next_right = (next_x+13)//8
            if self._is_floor_tile(next_right, now_y1, next_right, now_y2):
                self.x = next_x
            self.direction = 'right'
        if 'left' in directions:
            next_x -= speed
            next_left = (next_x+2)//8
            if self._is_floor_tile(next_left, now_y1, next_left, now_y2):
                self.x = next_x
            self.direction = 'left'
        if 'up' in directions:
            next_y -= speed
            next_top = (next_y+8)//8
            if self._is_floor_tile(now_x1, next_top, now_x2, next_top):
                self.y = next_y
            self.direction = 'up'
        if 'down' in directions:
            next_y += speed
            next_bottom = (next_y+13)//8
            if self._is_floor_tile(now_x1, next_bottom, now_x2, next_bottom):
                self.y = next_y
            self.direction = 'down'

    ## 対象タイルが床タイルかを判定
    def _is_floor_tile(self, x1, y1, x2, y2):
        tile1 = pyxel.tilemap(0).pget(x1, y1)
        tile2 = pyxel.tilemap(0).pget(x2, y2)
        if tile1[0]<2 and tile1[1]<2 and tile2[0]<2 and tile2[1]<2:
            return True
        else:
            return False
    
    def blt(self):
        ## 今持っている材料
        if self.slot['j'] is not None:
            pyxel.blt(BLK+4, 11*BLK+4, IMG_BANK_0, self.slot['j'].addr_x, self.slot['j'].addr_y, 8, 8, 0)
        if self.slot['k'] is not None:
            pyxel.blt(12+2*BLK, 11*BLK+4, IMG_BANK_0, self.slot['k'].addr_x, self.slot['k'].addr_y, 8, 8, 0)

        if self.direction == 'right':
            pyxel.blt(self.x, self.y, IMG_BANK_0, 16, 0, 16, 16, 8)
        elif self.direction == 'left':
            pyxel.blt(self.x, self.y, IMG_BANK_0, 32, 0, 16, 16, 8)
        elif self.direction == 'up':
            pyxel.blt(self.x, self.y, IMG_BANK_0, 48, 0, 16, 16, 8)
        else:
            pyxel.blt(self.x, self.y, IMG_BANK_0, 0, 0, 16, 16, 8)

## 材料
class Material:
    def __init__(self, code):
        self.code = code
        if code == 'yellow_juel':
            self.addr_x = 16
            self.addr_y = 16
        elif code == 'red_juel':
            self.addr_x = 16
            self.addr_y = 24
        elif code == 'blue_juel':
            self.addr_x = 24
            self.addr_y = 16
        elif code == 'green_juel':
            self.addr_x = 24
            self.addr_y = 24
        elif code == 'yellow_rod':
            self.addr_x = 32 
            self.addr_y = 16
        elif code == 'red_rod':
            self.addr_x = 32
            self.addr_y = 24
        elif code == 'blue_rod':
            self.addr_x = 40 
            self.addr_y = 16
        elif code == 'green_rod':
            self.addr_x = 40 
            self.addr_y = 24

## 倉庫
class Storage:
    def __init__(self, idx, init_x, init_y):
        self.charge_cnt = 0
        self.is_active = True
        self.charge_max = 60
        self.idx = idx 
        self.x = init_x
        self.y = init_y
        self.cnt = 0

        self.capacity = 1
        self.materials: list[Material] = []

    def update_clock(self):
        self.charge_cnt += 1
        if self.charge_cnt > self.charge_max:
            self.is_active = True
        else:
            self.is_active = False

    def add_material(self, material):
        if self.is_active == False:
            return False

        if len(self.materials) < self.capacity:
            self.materials.append(material)

    def pop_material(self):
        material = None
        if len(self.materials) > 0:
            material = self.materials.pop(0)
            self.is_active = False
            self.charge_cnt = 0
            self.charge_max = random.randint(360, 560)
        return material

    def is_near(self, worker):
        x_dist = abs(self.x+8 - worker.x)
        y_dist = abs(self.y+8 - worker.y-12)
        if x_dist < 16 and y_dist < 13:
            return True
        else:
            return False

    def blt(self):
        ## 中身
        if len(self.materials) > 0:
            pyxel.blt(self.x+4, self.y+4, IMG_BANK_0, self.materials[0].addr_x, self.materials[0].addr_y, 8, 8, 0)

    def add_cnt(self):
        self.cnt += 1

## 成果物
class Product:
    def __init__(self, idx, init_x, init_y, materials):
        self.idx = idx
        self.x = init_x
        self.y = init_y
        materials.extend(materials)
        self.needs = random.sample(materials, 5)
        self.materials = materials
        self.cnt = 0

    def add_material(self, material):
        if material in self.needs:
            self.needs.remove(material)

    def is_near(self, worker):
        x_dist = abs(self.x - worker.x)
        y_dist = abs(self.y+8 - worker.y-12)
        if x_dist < 18 and y_dist < 13:
            return True
        else:
            return False

    def is_completed(self):
        ret_bool = False
        if len(self.needs) == 0:
            ret_bool = True
        return ret_bool

    def reset(self):
        self.needs = random.sample(self.materials, 5)

    def blt(self):
        ## 穴
        for offset, need in enumerate(self.needs):
            pyxel.blt(self.x+4+offset*8, self.y+4, IMG_BANK_0, need.addr_x+32, need.addr_y, 8, 8, 0)

    def add_cnt(self):
        self.cnt += 1

## ゴミ箱
class Trash:
    def __init__(self, init_x, init_y):
        self.x = init_x
        self.y = init_y
        self.cnt = 0

    def is_near(self, worker):
        x_dist = abs(self.x+8 - worker.x-8)
        y_dist = abs(self.y+8 - worker.y-12)
        if x_dist < 18 and y_dist < 18:
            return True
        else:
            return False
        
    def add_cnt(self):
        self.cnt += 1

if __name__ == "__main__":
    game = Game()
    game.run()
