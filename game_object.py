import random
import pyxel

BLK = 16
IMG_BANK_0 = 0
IMG_BANK_1 = 1

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
