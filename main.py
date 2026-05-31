"""
╔═══════════════════════════════════════╗
║        【轮回之战】Roguelike 生存      ║
║   ─────────────────────────────────    ║
║  打怪升级 → 选天赋 → 挑战 Boss       ║
║  每 5 关小 Boss · 每 10 关大 Boss     ║
╚═══════════════════════════════════════╝
"""

import pygame
import random
import math
import sys
import json
import os
from enum import Enum

# ──────────────────────────────────────
#  初始化
# ──────────────────────────────────────
pygame.init()
pygame.display.set_caption("轮回之战 — Roguelike 生存")
try: pygame.key.stop_text_input()
except: pass
pygame.key.set_repeat(100, 50)
screen = pygame.display.set_mode((1280, 720))
W, H = screen.get_size()
clock = pygame.time.Clock()

# 字体 — 用 SysFont 加载系统字体，安全支持中文
_zh_font_path = None
for _try_font in [
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/msyh.ttf',
    'C:/Windows/Fonts/simsun.ttc',
    'C:/Windows/Fonts/SIMLI.TTF',
]:
    if os.path.exists(_try_font):
        _zh_font_path = _try_font
        break

if _zh_font_path:
    try:
        font_small = pygame.font.Font(_zh_font_path, 28)
        font_med  = pygame.font.Font(_zh_font_path, 42)
        font_large = pygame.font.Font(_zh_font_path, 72)
        font_huge  = pygame.font.Font(_zh_font_path, 100)
    except:
        _zh_font_path = None

if not _zh_font_path:
    # SysFont 比 Font(None) 更可靠地支持中文
    font_small = pygame.font.SysFont('microsoftyahei,simhei,msyh,simsun,tahoma', 28)
    font_med  = pygame.font.SysFont('microsoftyahei,simhei,msyh,simsun,tahoma', 42)
    font_large = pygame.font.SysFont('microsoftyahei,simhei,msyh,simsun,tahoma', 72)
    font_huge  = pygame.font.SysFont('microsoftyahei,simhei,msyh,simsun,tahoma', 100)

CENTER = (W // 2, H // 2)

# 世界地图大小（屏幕的 4 倍）
WORLD_W, WORLD_H = W * 4, H * 4
WORLD_CENTER = (WORLD_W // 2, WORLD_H // 2)

# ──────────────────────────────────────
#  颜色
# ──────────────────────────────────────
C = {
    'bg':         (10, 5, 22),
    'grid':       (22, 14, 36),
    'player':     (80, 200, 255),
    'player_hl':  (160, 230, 255),
    'hp':         (60, 230, 90),
    'hp_bg':      (50, 18, 18),
    'xp':         (120, 90, 240),
    'xp_bg':      (25, 18, 45),
    'enemy_n':    (210, 70, 70),    # 普通
    'enemy_f':    (220, 210, 40),   # 快速
    'enemy_t':    (160, 40, 160),   # 坦克
    'enemy_r':    (40, 200, 110),   # 远程
    'boss_m':     (220, 80, 200),   # 小Boss
    'boss_b':     (220, 40, 40),    # 大Boss
    'bullet':     (255, 255, 120),
    'bullet_fire':(255, 120, 40),
    'bullet_ice': (100, 200, 255),
    'xp_orb':     (100, 255, 140),
    'text':       (240, 240, 255),
    'text_dim':   (140, 140, 170),
    'gold':       (255, 215, 0),
    'talent_bg':  (22, 14, 42),
    'talent_bdr': (80, 60, 140),
    'talent_hov': (55, 40, 85),
    'dmg_txt':    (255, 100, 80),
    'wave_ann':   (255, 215, 0, 0),
    'overlay':    (0, 0, 0, 180),
}

# ──────────────────────────────────────
#  工具函数
# ──────────────────────────────────────
def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def angle(a, b):
    return math.atan2(b[1]-a[1], b[0]-a[0])

def lerp(a, b, t):
    return a + (b-a)*t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def rand_range(lo, hi):
    return random.random() * (hi-lo) + lo

# ── 魔法棒鼠标指针 ──
_wand_angle = 0
def draw_magic_wand(surface):
    """在鼠标位置绘制魔法棒光标"""
    global _wand_angle
    _wand_angle += 0.08
    try:
        mx, my = pygame.mouse.get_pos()
        # 杖杆
        wand_len = 30
        a = -0.3 + math.sin(_wand_angle * 0.5) * 0.03
        ex = mx + math.cos(a) * wand_len
        ey = my + math.sin(a) * wand_len
        pygame.draw.line(surface, (200, 150, 255), (mx, my), (ex, ey), 4)
        pygame.draw.line(surface, (255, 255, 255), (mx, my), (ex, ey), 2)
        # 杖尖星星
        sz = 8 + math.sin(_wand_angle) * 2
        pts = []
        for i in range(5):
            ai = -1.5708 + i * 1.2566 - _wand_angle * 0.3
            pts.append((mx + math.cos(ai) * sz, my + math.sin(ai) * sz))
            ai2 = -1.5708 + (i + 0.5) * 1.2566 - _wand_angle * 0.3
            pts.append((mx + math.cos(ai2) * sz * 0.4, my + math.sin(ai2) * sz * 0.4))
        if len(pts) >= 3:
            pygame.draw.polygon(surface, (255, 220, 80), pts)
            pygame.draw.polygon(surface, (255, 255, 200), pts, 2)
    except:
        pass  # 魔法棒只是装饰，不影响游戏

# ──────────────────────────────────────
#  粒子系统
# ──────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, life=30, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.life -= 1

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, surface, camera):
        t = self.life / self.max_life
        alpha = int(t * 255)
        r, g, b = self.color
        sz = self.size * (0.3 + 0.7*t)
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        surf = pygame.Surface((int(sz*2), int(sz*2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (r, g, b, alpha), (int(sz), int(sz)), int(sz))
        surface.blit(surf, (sx-sz, sy-sz))

# ──────────────────────────────────────
#  天赋系统
# ──────────────────────────────────────
TALENTS = [
    # (id, 名字, 描述, 稀有度, 效果函数, 最大堆叠)
    ('atk',    '攻击强化',   '伤害 +25%',       1, lambda p: setattr(p, 'dmg', p.dmg * 1.25), 5),
    ('spd',    '攻速提升',   '攻速 +20%',       1, lambda p: setattr(p, 'atk_speed', p.atk_speed / 1.2), 4),
    ('move',   '移速提升',   '移速 +25%',       1, lambda p: setattr(p, 'move_speed', p.move_speed * 1.25), 3),
    ('hp_up',  '生命强化',   '最大生命 +40',    1, lambda p: p._set_max_hp(p.max_hp + 40), 5),
    ('armor',  '护甲提升',   '受伤 -15%',       1, lambda p: setattr(p, 'armor', p.armor * 1.15), 3),
    ('regen',  '生命恢复',   '每秒 +2 HP',      2, lambda p: setattr(p, 'regen', p.regen + 2), 3),
    ('multi',  '多重射击',   '子弹 +1',         2, lambda p: setattr(p, 'multi', p.multi + 1), 3),
    ('pierce', '穿透弹',     '穿透 +1 敌人',    2, lambda p: setattr(p, 'pierce', p.pierce + 1), 3),
    ('range',  '射程延伸',   '射程 +30%',       2, lambda p: setattr(p, 'atk_range', p.atk_range * 1.3), 3),
    ('fire',   '烈焰附魔',   '30% 燃烧 3 秒',   3, lambda p: setattr(p, 'fire_chance', min(p.fire_chance + 0.30, 0.90)), 2),
    ('ice',    '冰霜附魔',   '子弹减速敌人 40%', 3, lambda p: setattr(p, 'ice_chance', min(p.ice_chance + 0.40, 0.90)), 2),
    ('lifesteal','生命偷取', '伤害 8% 回血',    3, lambda p: setattr(p, 'lifesteal', p.lifesteal + 0.08), 2),
    ('chain',  '闪电链',     '20% 连锁 3 敌人', 3, lambda p: setattr(p, 'chain_chance', min(p.chain_chance + 0.20, 0.80)), 2),
    ('berserk', '狂暴',      '击杀 +3% 攻速 5s',4, lambda p: setattr(p, 'berserk', p.berserk + 0.03), 2),
    ('shield', '护盾',       '每 12s 挡一次伤', 4, lambda p: setattr(p, 'shield_cd', max(p.shield_cd - 3, 3)), 2),
]

def talent_weight(tier):
    """根据稀有度返回权重"""
    weights = {1: 50, 2: 30, 3: 15, 4: 5}
    return weights.get(tier, 10)

# ──────────────────────────────────────
#  玩家
# ──────────────────────────────────────
class Player:
    def __init__(self):
        self.x, self.y = WORLD_CENTER
        self.radius = 18
        self.vx = self.vy = 0

        # 基础属性
        self.max_hp = 100
        self.hp = self.max_hp
        self.base_dmg = 12
        self.dmg = self.base_dmg
        self.base_atk_speed = 30    # 帧间隔
        self.atk_speed = self.base_atk_speed
        self.move_speed = 4.0
        self.atk_range = 420
        self.armor = 1.0               # 伤害 = 原始 / armor
        self.regen = 0

        # 特殊属性
        self.multi = 1                 # 子弹数量
        self.pierce = 0               # 穿透数
        self.fire_chance = 0.0
        self.ice_chance = 0.0
        self.chain_chance = 0.0
        self.lifesteal = 0.0
        self.berserk = 0.0             # 每层攻速加成
        self.shield_cd = 12            # 秒
        self.shield_timer = 0

        # 状态
        self.level = 1
        self.xp = 0
        self.xp_to_next = 20
        self.kills = 0
        self.total_dmg_dealt = 0
        self.atk_timer = 0
        self.berserk_stacks = 0
        self.berserk_timer = 0
        self.invincible = 0
        self.talents_taken = []

        # 移动状态（由 handle_event 事件驱动更新）
        self.move_x = 0
        self.move_y = 0

        # inv
        self.inv_timer = 0

    def _set_max_hp(self, val):
        ratio = self.hp / self.max_hp
        self.max_hp = val
        self.hp = self.max_hp * ratio

    @property
    def effective_atk_speed(self):
        bonus = 1 + self.berserk_stacks * self.berserk
        return max(5, self.atk_speed / bonus)

    @property
    def xp_percent(self):
        return self.xp / self.xp_to_next

    def gain_xp(self, amt):
        self.xp += amt
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(20 + self.level * 12)
            return True     # 升级了
        return False

    def take_damage(self, dmg):
        if self.invincible > 0:
            return 0
        actual = dmg / self.armor
        # 护盾
        if self.shield_timer <= 0 and self.shield_cd < 12:
            self.shield_timer = self.shield_cd * 60
            return 0
        self.hp -= actual
        self.inv_timer = 12
        if self.hp <= 0:
            self.hp = 0
        return actual

    def update(self):
        # 移动（由事件驱动，move_x/move_y 在 handle_event 中更新）
        mx, my = self.move_x, self.move_y
        if mx != 0 and my != 0:     # 对角线减速
            mx *= 0.707; my *= 0.707
        self.x += mx * self.move_speed
        self.y += my * self.move_speed
        self.x = clamp(self.x, self.radius, WORLD_W - self.radius)
        self.y = clamp(self.y, self.radius, WORLD_H - self.radius)

        # 攻击计时
        if self.atk_timer > 0:
            self.atk_timer -= 1

        # 无敌计时
        if self.inv_timer > 0:
            self.inv_timer -= 1

        # 护盾计时
        if self.shield_timer > 0:
            self.shield_timer -= 1

        # 生命恢复 (每秒60帧)
        if self.regen > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen / 60)

        # 狂暴衰减
        if self.berserk > 0:
            if self.berserk_timer > 0:
                self.berserk_timer -= 1
            else:
                self.berserk_stacks = 0

    def draw(self, surface, camera=None):
        if camera:
            sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        else:
            sx, sy = int(self.x), int(self.y)

        # 光环
        glow = pygame.Surface((self.radius*6, self.radius*6), pygame.SRCALPHA)
        for i in range(4):
            r = self.radius * (1 + i*0.6)
            alpha = 30 - i*6
            pygame.draw.circle(glow, (*C['player'], alpha), (self.radius*3, self.radius*3), int(r))
        surface.blit(glow, (sx - self.radius*3, sy - self.radius*3))

        # 身体
        c = C['player_hl'] if self.inv_timer % 6 < 3 else C['player']
        pygame.draw.circle(surface, (20, 20, 40), (sx, sy), self.radius + 4)
        pygame.draw.circle(surface, c, (sx, sy), self.radius)

        # 护盾指示
        if self.shield_timer > 0:
            pygame.draw.circle(surface, (100, 200, 255, 60), (sx, sy), self.radius + 8, 2)

        # 眼睛
        pygame.draw.circle(surface, (255,255,255), (sx-5, sy-3), 4)
        pygame.draw.circle(surface, (255,255,255), (sx+5, sy-3), 4)
        pygame.draw.circle(surface, (10,10,30), (sx-5, sy-3), 2)
        pygame.draw.circle(surface, (10,10,30), (sx+5, sy-3), 2)

    def can_attack(self):
        return self.atk_timer <= 0

    def reset_attack(self):
        self.atk_timer = int(self.effective_atk_speed)

    def add_berserk_stack(self):
        if self.berserk > 0:
            self.berserk_stacks = min(self.berserk_stacks + 1, 20)
            self.berserk_timer = 300  # 5秒

    def get_stat_texts(self):
        return [
            f"等级 {self.level}",
            f"攻击 {self.dmg:.0f}  (+{((self.dmg/self.base_dmg)-1)*100:.0f}%)",
            f"攻速 {60/self.effective_atk_speed:.1f}/s",
            f"移速 {self.move_speed:.0f}",
            f"射程 {self.atk_range:.0f}",
            f"护甲 {self.armor:.1f}x",
            f"恢复 {self.regen:.1f}/s",
        ]

# ──────────────────────────────────────
#  子弹
# ──────────────────────────────────────
class Bullet:
    def __init__(self, x, y, target, dmg, pierce=0, fire_chance=0, ice_chance=0, chain_chance=0):
        self.x, self.y = x, y
        self.target = target
        self.dmg = dmg
        self.pierce_left = pierce
        self.fire_chance = fire_chance
        self.ice_chance = ice_chance
        self.chain_chance = chain_chance
        self.speed = 12
        self.radius = 5
        self.hit = set()
        a = angle((x, y), (target.x, target.y))
        self.vx = math.cos(a) * self.speed
        self.vy = math.sin(a) * self.speed
        self.life = 120
        self.trail = []

    @property
    def dead(self):
        return self.life <= 0

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface, camera):
        # 轨迹
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(100 * i / len(self.trail))
            r = self.radius * (0.3 + 0.7 * i / len(self.trail))
            sx, sy = int(tx - camera.x), int(ty - camera.y)
            surf = pygame.Surface((int(r*2), int(r*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*C['bullet'][:3], alpha), (int(r), int(r)), int(r))
            surface.blit(surf, (sx-r, sy-r))

        # 主体
        color = C['bullet_fire'] if self.fire_chance > 0 else C['bullet_ice'] if self.ice_chance > 0 else C['bullet']
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        glow = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color[:3], 60), (self.radius*2, self.radius*2), self.radius*2)
        surface.blit(glow, (sx-self.radius*2, sy-self.radius*2))
        pygame.draw.circle(surface, color, (sx, sy), self.radius)
        pygame.draw.circle(surface, (255,255,255), (sx, sy), self.radius*0.5)

    def on_hit(self, enemy):
        self.hit.add(id(enemy))

# ──────────────────────────────────────
#  XP 球
# ──────────────────────────────────────
class XPOrb:
    def __init__(self, x, y, value):
        self.x, self.y = x, y
        self.value = value
        self.radius = 4 + value
        self.vy = -2
        self.bob_timer = random.random() * 100
        self.collected = False
        self.pull_speed = 0

    @property
    def dead(self):
        return self.collected

    def update(self, px, py):
        self.bob_timer += 0.05
        d = dist((self.x, self.y), (px, py))
        if d < 250:
            self.pull_speed = min(self.pull_speed + 0.3, 8 + 200/d)
            a = angle((self.x, self.y), (px, py))
            self.x += math.cos(a) * self.pull_speed
            self.y += math.sin(a) * self.pull_speed
            if d < 20:
                self.collected = True
        else:
            self.pull_speed = 0
        self.y += math.sin(self.bob_timer) * 0.3

    def draw(self, surface, camera):
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        r = self.radius

        glow = pygame.Surface((int(r*5), int(r*5)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C['xp_orb'][:3], 40), (int(r*2.5), int(r*2.5)), int(r*2))
        surface.blit(glow, (sx-r*2.5, sy-r*2.5))

        # 菱形
        pts = [(sx, sy-r), (sx+r, sy), (sx, sy+r), (sx-r, sy)]
        pygame.draw.polygon(surface, C['xp_orb'], pts)
        pygame.draw.polygon(surface, (200, 255, 220), pts, 1)

# ──────────────────────────────────────
#  敌人
# ──────────────────────────────────────
class Enemy:
    TYPES = {
        'normal': {'hp': 30, 'dmg': 8, 'speed': 1.8, 'radius': 15, 'color': C['enemy_n'], 'xp': 5},
        'fast':   {'hp': 15, 'dmg': 5, 'speed': 3.5, 'radius': 11, 'color': C['enemy_f'], 'xp': 4},
        'tank':   {'hp': 80, 'dmg': 12, 'speed': 0.9, 'radius': 22, 'color': C['enemy_t'], 'xp': 10},
        'ranged': {'hp': 20, 'dmg': 7, 'speed': 1.2, 'radius': 13, 'color': C['enemy_r'], 'xp': 6},
    }

    def __init__(self, etype, x, y, wave_scale=1.0):
        cfg = self.TYPES[etype]
        self.etype = etype
        self.x, self.y = x, y
        self.max_hp = cfg['hp'] * (1 + (wave_scale-1)*0.15)
        self.hp = self.max_hp
        self.dmg = cfg['dmg'] * (1 + (wave_scale-1)*0.08)
        self.base_speed = cfg['speed'] * (1 + (wave_scale-1)*0.03)
        self.radius = cfg['radius']
        self.xp_value = cfg['xp']
        self.atk_cooldown = 60
        self.atk_timer = 0
        self.color = cfg['color']
        self.dead = False

        # 状态效果
        self.burn_timer = 0
        self.burn_dmg = 0
        self.slow_timer = 0
        self.slow_amount = 0
        self.stun_timer = 0

    @property
    def speed(self):
        s = self.base_speed
        if self.slow_timer > 0:
            s *= (1 - self.slow_amount)
        if self.stun_timer > 0:
            s = 0
        return s

    def take_damage(self, dmg, bullet=None):
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def apply_burn(self, chance, dmg_per_tick=3, duration=180):
        if random.random() < chance and self.burn_timer <= 0:
            self.burn_timer = duration
            self.burn_dmg = dmg_per_tick

    def apply_slow(self, chance, amount=0.4, duration=120):
        if random.random() < chance:
            self.slow_timer = duration
            self.slow_amount = amount

    def stun(self, duration=30):
        self.stun_timer = duration

    def update(self, px, py):
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if self.slow_timer > 0:
            self.slow_timer -= 1
        if self.burn_timer > 0:
            self.burn_timer -= 1
            self.hp -= self.burn_dmg / 60 * 3  # 每帧烧
            if self.hp <= 0:
                self.dead = True

        if self.atk_timer > 0:
            self.atk_timer -= 1

        # 移向玩家
        if self.etype != 'ranged':
            a = angle((self.x, self.y), (px, py))
            self.x += math.cos(a) * self.speed
            self.y += math.sin(a) * self.speed

    def draw(self, surface, camera):
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        r = self.radius

        # 光环
        glow = pygame.Surface((r*5, r*5), pygame.SRCALPHA)
        c = self.color
        pygame.draw.circle(glow, (*c[:3], 25), (r*2.5, r*2.5), r*2)
        surface.blit(glow, (sx-r*2.5, sy-r*2.5))

        # 身体
        color = (min(255, c[0]+60), *c[1:]) if self.burn_timer > 0 else \
                (c[0]//2, c[1], c[2]+60) if self.slow_timer > 0 else c
        pygame.draw.circle(surface, (15, 10, 25), (sx, sy), r+3)
        pygame.draw.circle(surface, color, (sx, sy), r)

        # 眼睛 (朝向玩家)
        ex, ey = sx, sy

        # 血条
        if self.hp < self.max_hp:
            bw = r * 2
            bh = 4
            bx, by = sx - bw//2, sy - r - 8
            pygame.draw.rect(surface, (40, 20, 20), (bx, by, bw, bh))
            pygame.draw.rect(surface, C['hp'], (bx, by, int(bw * self.hp/self.max_hp), bh))

class RangedEnemy(Enemy):
    """远程敌人 - 保持距离射击"""
    def __init__(self, x, y, wave_scale=1.0):
        super().__init__('ranged', x, y, wave_scale)
        self.preferred_dist = 250

    def update(self, px, py):
        super().update(px, py)
        d = dist((self.x, self.y), (px, py))
        if d < self.preferred_dist * 0.8:
            # 后退
            a = angle((px, py), (self.x, self.y))
            self.x += math.cos(a) * self.speed
            self.y += math.sin(a) * self.speed
        elif d > self.preferred_dist * 1.3:
            # 靠近
            a = angle((self.x, self.y), (px, py))
            self.x += math.cos(a) * self.speed * 0.5
            self.y += math.sin(a) * self.speed * 0.5

# ──────────────────────────────────────
#  Boss 类
# ──────────────────────────────────────
class Boss:
    def __init__(self, is_mini=False, wave=5, px=None, py=None):
        self.is_mini = is_mini
        self.wave = wave
        scale = 1 + (wave // 10) * 0.5

        if is_mini:
            self.max_hp = 500 * scale
            self.dmg = 18 * (1 + (wave-5)*0.05)
            self.radius = 40
            self.base_speed = 1.5
            self.color = C['boss_m']
            self.xp_value = 50
            self.name = f"小Boss · 第{wave}关"
        else:
            self.max_hp = 1500 * scale
            self.dmg = 30 * (1 + (wave-10)*0.05)
            self.radius = 55
            self.base_speed = 1.2
            self.color = C['boss_b']
            self.xp_value = 200
            self.name = f"大Boss · 第{wave}关"

        self.hp = self.max_hp
        if px is not None:
            self.x = px + random.choice([-1, 1]) * random.randint(300, 500)
            self.y = py + random.choice([-1, 1]) * random.randint(200, 400)
        else:
            self.x = WORLD_CENTER[0] + random.choice([-1, 1]) * 500
            self.y = WORLD_CENTER[1] + random.choice([-1, 1]) * 400
        self.dead = False
        self.atk_timer = 0
        self.special_timer = 0
        self.phase = 1  # 1 或 2 (半血以下)
        self.burn_timer = 0
        self.slow_timer = 0
        self.stun_timer = 0
        self.atk_cooldown = 40
        self.special_cooldown = 180
        self.charge_target = None
        self.charging = False
        self.charge_speed = 0

    @property
    def speed(self):
        if self.stun_timer > 0:
            return 0
        s = self.base_speed
        if self.charging:
            return self.charge_speed
        if self.slow_timer > 0:
            s *= 0.5
        return s

    def take_damage(self, dmg, bullet=None):
        self.hp -= dmg
        ratio = self.hp / self.max_hp
        if ratio <= 0.5 and self.phase == 1:
            self.phase = 2
            self.base_speed *= 1.3
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def update(self, px, py):
        if self.stun_timer > 0: self.stun_timer -= 1
        if self.slow_timer > 0: self.slow_timer -= 1
        if self.burn_timer > 0:
            self.burn_timer -= 1
            self.hp -= 2
            if self.hp <= 0:
                self.dead = True

        if self.atk_timer > 0: self.atk_timer -= 1
        if self.special_timer > 0: self.special_timer -= 1

        # 冲刺攻击
        if self.charging:
            a = angle((self.x, self.y), (px, py))
            self.x += math.cos(a) * self.charge_speed
            self.y += math.sin(a) * self.charge_speed
            d = dist((self.x, self.y), (px, py))
            if d < self.radius + 25:
                self.charging = False
                self.special_timer = self.special_cooldown
            return

        # 靠近玩家
        a = angle((self.x, self.y), (px, py))
        self.x += math.cos(a) * self.speed
        self.y += math.sin(a) * self.speed

        # BOSS特殊技能
        if self.special_timer <= 0 and not self.charging:
            d = dist((self.x, self.y), (px, py))
            if d < 500:
                if random.random() < 0.4:
                    # 冲刺
                    self.charging = True
                    self.charge_speed = 8 + self.phase * 2
                else:
                    # AOE震波
                    self.special_timer = self.special_cooldown

    def draw(self, surface, camera):
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        r = self.radius

        # 大光环
        for i in range(5):
            gr = r + i * 15 + 10
            alpha = max(0, 20 - i * 3)
            glow = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            c = self.color
            pygame.draw.circle(glow, (*c[:3], alpha), (gr, gr), gr)
            surface.blit(glow, (sx-gr, sy-gr))

        # 身体
        c = self.color
        pygame.draw.circle(surface, (10, 5, 20), (sx, sy), r+6)
        pygame.draw.circle(surface, c, (sx, sy), r)

        # 愤怒纹路 (二阶段)
        if self.phase == 2:
            for i in range(8):
                a = i * math.pi/4 + pygame.time.get_ticks()/1000
                ex = sx + math.cos(a) * r * 0.7
                ey = sy + math.sin(a) * r * 0.7
                pygame.draw.line(surface, (255, 100, 100), (sx, sy), (ex, ey), 2)

        # 眼睛
        for dx in [-8, 8]:
            pygame.draw.circle(surface, (255, 60, 60), (sx+dx, sy-5), 6)
            pygame.draw.circle(surface, (255, 255, 200), (sx+dx, sy-5), 3)

        # 名字
        txt = font_small.render(self.name, True, C['gold'])
        surface.blit(txt, (sx - txt.get_width()//2, sy - r - 30))

        # 顶部血条 (全局)
        bw = 400
        bh = 16
        bx = W//2 - bw//2
        by = 20
        pygame.draw.rect(surface, (40, 20, 20), (bx, by, bw, bh))
        pygame.draw.rect(surface, (230, 60, 60) if not self.is_mini else (200, 100, 200),
                         (bx, by, int(bw * self.hp/self.max_hp), bh))
        pygame.draw.rect(surface, C['gold'], (bx, by, bw, bh), 2)

        name_txt = font_small.render(self.name, True, C['gold'])
        surface.blit(name_txt, (bx + bw//2 - name_txt.get_width()//2, by - 24))

# ──────────────────────────────────────
#  波次管理
# ──────────────────────────────────────
class WaveManager:
    MAX_WAVE = 100

    def __init__(self):
        self.wave = 0
        self.enemies_left = 0
        self.spawn_timer = 0
        self.spawn_count = 0
        self.max_spawns = 5
        self.between_waves = False
        self.wave_delay = 120
        self.wave_timer = 0
        self.boss_active = False
        self.boss = None
        self.is_mini_boss_wave = False
        self.is_boss_wave = False
        self.game_complete = False

    def start_next_wave(self):
        self.wave += 1
        if self.wave > self.MAX_WAVE:
            self.game_complete = True
            return
        self.is_mini_boss_wave = (self.wave % 5 == 0) and not (self.wave % 10 == 0)
        self.is_boss_wave = (self.wave % 10 == 0)

        base_count = 4 + self.wave
        self.max_spawns = min(base_count, 25)
        self.spawn_count = 0
        self.spawn_timer = 0
        self.enemies_left = self.max_spawns + (5 if self.is_mini_boss_wave else 10 if self.is_boss_wave else 0)
        self.between_waves = False
        self.boss_active = self.is_mini_boss_wave or self.is_boss_wave

    def get_enemy_types(self):
        """根据波次决定敌人类别"""
        types = ['normal']
        if self.wave >= 3:
            types.append('fast')
        if self.wave >= 5:
            types.append('tank')
        if self.wave >= 7:
            types.append('ranged')
        return types

    def spawn_enemy(self, enemies, px=W//2, py=H//2):
        if self.spawn_count >= self.max_spawns:
            return None

        etypes = self.get_enemy_types()
        etype = random.choice(etypes)

        # 在世界空间中，在玩家视野外生成
        side = random.randint(0, 3)
        margin = 60
        view_w, view_h = W, H
        if side == 0:  # 上
            x = random.randint(int(px - view_w), int(px + view_w))
            y = py - view_h//2 - margin
        elif side == 1:  # 下
            x = random.randint(int(px - view_w), int(px + view_w))
            y = py + view_h//2 + margin
        elif side == 2:  # 左
            x = px - view_w//2 - margin
            y = random.randint(int(py - view_h), int(py + view_h))
        else:  # 右
            x = px + view_w//2 + margin
            y = random.randint(int(py - view_h), int(py + view_h))
        # 确保不超出世界边界
        x = clamp(x, 10, WORLD_W - 10)
        y = clamp(y, 10, WORLD_H - 10)

        if etype == 'ranged':
            enemy = RangedEnemy(x, y, self.wave)
        else:
            enemy = Enemy(etype, x, y, self.wave)

        self.spawn_count += 1
        return enemy

    def spawn_boss(self, px=None, py=None):
        if self.is_boss_wave:
            self.boss = Boss(is_mini=False, wave=self.wave, px=px, py=py)
        else:
            self.boss = Boss(is_mini=True, wave=self.wave, px=px, py=py)
        return self.boss

    def update(self, enemies, player):
        if self.between_waves:
            self.wave_timer -= 1
            if self.wave_timer <= 0:
                self.start_next_wave()
            return

        # 生怪
        self.spawn_timer -= 1
        if self.spawn_timer <= 0 and self.spawn_count < self.max_spawns:
            self.spawn_timer = max(10, 40 - self.wave * 2)
            enemy = self.spawn_enemy(enemies, player.x, player.y)
            if enemy:
                enemies.append(enemy)

        # Boss
        if self.boss_active and self.spawn_count >= self.max_spawns and not self.boss:
            self.boss = self.spawn_boss(player.x, player.y)

        # 检查波次结束
        alive_enemies = [e for e in enemies if not e.dead]
        if self.boss:
            has_boss_alive = not self.boss.dead
        else:
            has_boss_alive = False

        if len(alive_enemies) == 0 and not has_boss_alive and self.spawn_count >= self.max_spawns:
            self.between_waves = True
            self.wave_timer = self.wave_delay
            self.boss = None
            self.boss_active = False

# ──────────────────────────────────────
#  UI 绘制
# ──────────────────────────────────────
def draw_ui(surface, player, wave_mgr, orbs, vx=0, vy=0):
    # ── HUD 左下 ──
    mx, my = 20, H - 20

    # 头像
    pygame.draw.circle(surface, C['player'], (mx+22, my-22), 20)
    pygame.draw.circle(surface, (255,255,255), (mx+22, my-22), 20, 2)

    # HP 条
    hp_x, hp_y = mx+50, my-34
    hp_w, hp_h = 200, 16
    pygame.draw.rect(surface, C['hp_bg'], (hp_x, hp_y, hp_w, hp_h))
    pygame.draw.rect(surface, C['hp'], (hp_x, hp_y, int(hp_w * player.hp/player.max_hp), hp_h))
    pygame.draw.rect(surface, (255,255,255,30), (hp_x, hp_y, hp_w, hp_h), 1)
    hp_txt = font_small.render(f"{player.hp:.0f}/{player.max_hp:.0f}", True, (255,255,255))
    surface.blit(hp_txt, (hp_x + hp_w//2 - hp_txt.get_width()//2, hp_y + 1))

    # XP 条
    xp_x, xp_y = hp_x, hp_y + 22
    xp_w, xp_h = hp_w, 10
    pygame.draw.rect(surface, C['xp_bg'], (xp_x, xp_y, xp_w, xp_h))
    pygame.draw.rect(surface, C['xp'], (xp_x, xp_y, int(xp_w * player.xp_percent), xp_h))
    xp_txt = font_small.render(f"Lv.{player.level}", True, (200,200,255))
    surface.blit(xp_txt, (xp_x - 50, xp_y - 2))

    # ── 波次信息 ──
    wave_txt = font_med.render(f"第 {wave_mgr.wave} 关", True, C['gold'] if wave_mgr.between_waves else C['text'])
    surface.blit(wave_txt, (W//2 - wave_txt.get_width()//2, 10))

    # 击杀数
    kill_txt = font_small.render(f"击杀 {player.kills} | 天赋 {len(player.talents_taken)}", True, C['text_dim'])
    surface.blit(kill_txt, (W//2 - kill_txt.get_width()//2, 50))

    # ── 右上 属性面板 ──
    stats = player.get_stat_texts()
    for i, txt in enumerate(stats):
        s = font_small.render(txt, True, C['text_dim'])
        surface.blit(s, (W - s.get_width() - 15, 15 + i*26))

    # ── 波次公告 ──
    if wave_mgr.wave_timer > 0 and wave_mgr.between_waves:
        alpha = min(255, max(0, wave_mgr.wave_timer * 4))
        txt = font_huge.render(f"第 {wave_mgr.wave+1} 关", True, C['gold'])
        txt.set_alpha(alpha if alpha <= 255 else 255)
        sub = font_med.render("准备迎战!", True, C['text_dim'])
        sub.set_alpha(alpha if alpha <= 255 else 255)
        surface.blit(txt, (W//2 - txt.get_width()//2, H//2 - 80))
        surface.blit(sub, (W//2 - sub.get_width()//2, H//2 + 10))

    # ── 调试：按键状态（红色表示按键被检测到） ──
    dc = (100,255,100) if player.move_x == 0 and player.move_y == 0 else (255,255,100)
    debug = font_small.render(f"移动:({player.move_x},{player.move_y}) 位置:({player.x:.0f},{player.y:.0f}) [按 WASD 试试]", True, dc)
    surface.blit(debug, (W//2 - debug.get_width()//2, H - 30))

# ──────────────────────────────────────
#  天赋选择面板
# ──────────────────────────────────────
class TalentPanel:
    def __init__(self):
        self.active = False
        self.options = []
        self.hovered = -1
        self.fade_in = 0

    def show(self, player):
        self.active = True
        self.fade_in = 0
        self.options = self._pick_options(player)
        self.hovered = -1

    def _pick_options(self, player):
        """挑选3个天赋"""
        taken_ids = [t[0] for t in player.talents_taken]
        available = []

        for t in TALENTS:
            tid, name, desc, tier, fn, max_stack = t
            count = taken_ids.count(tid)
            if count < max_stack:
                # 根据等级解锁稀有度
                if tier == 1:
                    available.append(t)
                elif tier == 2 and player.level >= 2:
                    available.append(t)
                elif tier == 3 and player.level >= 5:
                    available.append(t)
                elif tier == 4 and player.level >= 10:
                    available.append(t)

        if len(available) <= 3:
            return available

        # 按权重随机选，优先选没拿过的
        weights = []
        for t in available:
            tid = t[0]
            count = taken_ids.count(tid)
            w = talent_weight(t[3])
            if count == 0:
                w *= 2  # 新天赋权重翻倍
            weights.append(w)

        chosen = []
        pool = list(range(len(available)))
        for _ in range(3):
            if not pool:
                break
            total = sum(weights[i] for i in pool)
            r = random.random() * total
            acc = 0
            for i in pool:
                acc += weights[i]
                if r <= acc:
                    chosen.append(available[i])
                    pool.remove(i)
                    break
        return chosen

    def handle_click(self, pos, player):
        if not self.active:
            return False
        self.hovered = -1
        bx, by = W//2 - 300, H//2 + 50
        gap = 220
        for i in range(len(self.options)):
            rx, ry = bx + i*gap, by
            rect = pygame.Rect(rx, ry, 190, 260)
            if rect.collidepoint(pos):
                self._apply_talent(i, player)
                self.active = False
                return True
        return False

    def _apply_talent(self, idx, player):
        if idx >= len(self.options):
            return
        tid, name, desc, tier, fn, max_stack = self.options[idx]
        fn(player)
        player.talents_taken.append(self.options[idx])

    def update(self):
        if self.active:
            self.fade_in = min(self.fade_in + 12, 255)
            mx, my = pygame.mouse.get_pos()
            self.hovered = -1
            bx, by = W//2 - 300, H//2 + 50
            gap = 220
            for i in range(len(self.options)):
                rx, ry = bx + i*gap, by
                rect = pygame.Rect(rx, ry, 190, 260)
                if rect.collidepoint(mx, my):
                    self.hovered = i
                    break

    def draw(self, surface):
        if not self.active:
            return
        a = self.fade_in

        # 遮罩
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(180, a)))
        surface.blit(overlay, (0, 0))

        # 标题
        title = font_large.render("🆙 升级！选择天赋", True, C['gold'])
        title.set_alpha(a)
        surface.blit(title, (W//2 - title.get_width()//2, H//2 - 160))

        sub = font_small.render(f"等级 {pygame.font.Font(None, 28)} — 选一个天赋变强", True, C['text_dim'])
        sub_t = font_small.render("点击选择天赋", True, C['text_dim'])
        sub_t.set_alpha(a)
        surface.blit(sub_t, (W//2 - sub_t.get_width()//2, H//2 - 110))

        # 天赋卡片
        bx, by = W//2 - 300, H//2 + 20
        gap = 220
        tier_colors = {1: (100, 150, 255), 2: (140, 80, 255), 3: (255, 150, 50), 4: (255, 215, 0)}
        tier_names = {1: '普通', 2: '稀有', 3: '史诗', 4: '传说'}

        for i, t in enumerate(self.options):
            tid, name, desc, tier, fn, max_stack = t
            rx, ry = bx + i*gap, by

            # 卡片背景
            is_hover = i == self.hovered
            bg_color = C['talent_hov'] if is_hover else C['talent_bg']
            bdr_color = C['talent_bdr'] if not is_hover else tier_colors.get(tier, C['gold'])

            card = pygame.Surface((190, 260), pygame.SRCALPHA)
            card.fill((*bg_color, a))
            pygame.draw.rect(card, (*bdr_color, a), card.get_rect(), 2)

            surface.blit(card, (rx, ry))

            # 稀有度标记
            tc = tier_colors.get(tier, (200, 200, 200))
            tier_txt = font_small.render(tier_names.get(tier, ''), True, tc)
            tier_txt.set_alpha(a)
            surface.blit(tier_txt, (rx + 95 - tier_txt.get_width()//2, ry + 8))

            # 天赋图标 (简单的形状)
            icon_y = ry + 40
            pygame.draw.circle(surface, tc, (rx + 95, icon_y + 25), 22)
            pygame.draw.circle(surface, (255,255,255, min(200, a)), (rx + 95, icon_y + 25), 18)
            icon_txt = font_med.render(tid[:2].upper(), True, tc)
            icon_txt.set_alpha(a)
            surface.blit(icon_txt, (rx + 95 - icon_txt.get_width()//2, icon_y + 16))

            # 名字
            name_txt = font_med.render(name, True, (255,255,255))
            name_txt.set_alpha(a)
            surface.blit(name_txt, (rx + 95 - name_txt.get_width()//2, icon_y + 60))

            # 描述
            desc_lines = [desc[j:j+10] for j in range(0, len(desc), 10)]
            for k, line in enumerate(desc_lines):
                d = font_small.render(line, True, C['text_dim'])
                d.set_alpha(a)
                surface.blit(d, (rx + 12, icon_y + 95 + k*22))

            # 堆叠数
            if max_stack > 1:
                stack_txt = font_small.render(f"可堆叠 {max_stack} 次", True, (150,150,150))
                stack_txt.set_alpha(a)
                surface.blit(stack_txt, (rx + 95 - stack_txt.get_width()//2, ry + 230))

# ──────────────────────────────────────
#  游戏结束界面
# ──────────────────────────────────────
class GameOver:
    def __init__(self):
        self.active = False
        self.player = None
        self.wave = 0
        self.timer = 0

    def show(self, player, wave):
        self.active = True
        self.player = player
        self.wave = wave
        self.timer = 0

    def update(self):
        if self.active:
            self.timer += 1

    def handle_click(self, pos, game):
        if not self.active or self.timer < 60:
            return False
        # 再来一次
        bx, by = W//2 - 130, H//2 + 150
        r1 = pygame.Rect(bx, by, 120, 50)
        if r1.collidepoint(pos):
            game.reset()
            return True
        # 返回主菜单
        r2 = pygame.Rect(bx + 140, by, 120, 50)
        if r2.collidepoint(pos):
            self.active = False
            game.state = 'menu'
            game.main_menu.active = True
            # 魔法棒鼠标，始终隐藏系统光标
# pygame.mouse.set_visible(True)
            return True
        return False

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title = font_huge.render("💀 轮回终结", True, (255, 80, 80))
        surface.blit(title, (W//2 - title.get_width()//2, H//2 - 150))

        if self.player:
            texts = [
                f"存活至：第 {self.wave} 关",
                f"等级：{self.player.level}",
                f"击杀：{self.player.kills}",
                f"天赋：{len(self.player.talents_taken)} 个",
                f"伤害输出：{self.player.total_dmg_dealt:.0f}",
            ]
            for i, t in enumerate(texts):
                txt = font_med.render(t, True, C['text'])
                surface.blit(txt, (W//2 - txt.get_width()//2, H//2 - 30 + i*45))

        if self.timer > 60:
            # 再来一次
            r1 = pygame.Rect(W//2 - 130, H//2 + 150, 120, 50)
            pygame.draw.rect(surface, (60, 40, 80), r1)
            pygame.draw.rect(surface, C['gold'], r1, 2)
            retry = font_med.render("再来一次", True, C['gold'])
            surface.blit(retry, (r1.centerx - retry.get_width()//2, r1.centery - retry.get_height()//2))
            # 返回主菜单
            r2 = pygame.Rect(W//2 + 10, H//2 + 150, 120, 50)
            pygame.draw.rect(surface, (40, 30, 60), r2)
            pygame.draw.rect(surface, C['gold'], r2, 2)
            menu = font_med.render("返回菜单", True, C['gold'])
            surface.blit(menu, (r2.centerx - menu.get_width()//2, r2.centery - menu.get_height()//2))

# ──────────────────────────────────────
#  伤害数字
# ──────────────────────────────────────
class DamageText:
    def __init__(self, x, y, dmg, color=(255, 100, 80)):
        self.x, self.y = x, y
        self.dmg = dmg
        self.color = color
        self.life = 40
        self.vy = -2

    @property
    def dead(self):
        return self.life <= 0

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surface, camera):
        alpha = min(255, self.life * 8)
        txt = font_small.render(f"-{self.dmg:.0f}", True, self.color)
        txt.set_alpha(alpha)
        sx, sy = int(self.x - camera.x), int(self.y - camera.y)
        surface.blit(txt, (sx - txt.get_width()//2, sy - txt.get_height()//2))

# ──────────────────────────────────────
#  主菜单
# ──────────────────────────────────────
# 图鉴数据
BESTIARY_TALENTS = [
    ('atk',    '攻击强化',   '伤害 +25%',       1),
    ('spd',    '攻速提升',   '攻速 +20%',       1),
    ('move',   '移速提升',   '移速 +25%',       1),
    ('hp_up',  '生命强化',   '最大生命 +40',    1),
    ('armor',  '护甲提升',   '受伤 -15%',       1),
    ('regen',  '生命恢复',   '每秒 +2 HP',      2),
    ('multi',  '多重射击',   '子弹 +1',         2),
    ('pierce', '穿透弹',     '穿透 +1 敌人',    2),
    ('range',  '射程延伸',   '射程 +30%',       2),
    ('fire',   '烈焰附魔',   '30% 燃烧 3s',     3),
    ('ice',    '冰霜附魔',   '子弹减速敌人 40%',3),
    ('lifesteal','生命偷取', '伤害 8% 回血',    3),
    ('chain',  '闪电链',     '20% 连锁 3 敌人', 3),
    ('berserk', '狂暴',      '击杀 +3% 攻速',   4),
    ('shield', '护盾',       '每 12s 挡一次伤', 4),
]

BESTIARY_ENEMIES = [
    ('normal', '普通小怪',  '近战 · 属性均衡',     C['enemy_n']),
    ('fast',   '快速小怪',  '高速 · 低血量',       C['enemy_f']),
    ('tank',   '重装小怪',  '高血量 · 低速度',     C['enemy_t']),
    ('ranged', '远程小怪',  '远程 · 保持距离射击',  C['enemy_r']),
]

BESTIARY_BOSSES = [
    ('mini',   '小Boss',    '每 5 关出现',           C['boss_m']),
    ('big',    '大Boss',    '每 10 关出现',          C['boss_b']),
]

tier_names_b = {1: '普通', 2: '稀有', 3: '史诗', 4: '传说'}
tier_colors_b = {1: (100, 150, 255), 2: (140, 80, 255), 3: (255, 150, 50), 4: (255, 215, 0)}

class Bestiary:
    def __init__(self):
        self.active = False
        self.tab = 0  # 0=天赋, 1=怪物, 2=Boss
        self.scroll = 0
        self.timer = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.active = False; return
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.tab = (self.tab - 1) % 3; self.scroll = 0
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.tab = (self.tab + 1) % 3; self.scroll = 0
            if event.key == pygame.K_DOWN:
                self.scroll = min(self.scroll + 1, max(0, self._max_scroll()))
            if event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 1)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 标签切换
            for i in range(3):
                if pygame.Rect(W//2-180 + i*120, 85, 110, 35).collidepoint(event.pos):
                    self.tab = i; self.scroll = 0; return
            # 关闭
            if pygame.Rect(W-80, 15, 60, 30).collidepoint(event.pos):
                self.active = False; return

    def _max_scroll(self):
        if self.tab == 0: return max(0, len(BESTIARY_TALENTS) - 7)
        if self.tab == 1: return max(0, len(BESTIARY_ENEMIES) - 5)
        return max(0, len(BESTIARY_BOSSES) - 4)

    def update(self):
        self.timer += 1

    def draw(self, surface):
        if not self.active: return
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 2, 15, 240))
        surface.blit(overlay, (0, 0))

        # 标题
        title = font_large.render("📖 图鉴系统", True, C['gold'])
        surface.blit(title, (W//2 - title.get_width()//2, 20))

        # 关闭按钮
        close = font_small.render("✕ 关闭", True, (150,140,170))
        pygame.draw.rect(surface, (40,30,55), (W-85, 12, 70, 35), border_radius=4)
        surface.blit(close, (W-75, 18))

        # 标签
        tab_names = ['天赋', '怪物', 'Boss']
        for i, tn in enumerate(tab_names):
            tx = W//2 - 180 + i*120
            rect = pygame.Rect(tx, 85, 110, 35)
            sel = i == self.tab
            pygame.draw.rect(surface, (50,35,70) if sel else (25,18,40), rect, border_radius=5)
            if sel: pygame.draw.rect(surface, C['gold'], rect, 2, border_radius=5)
            t = font_med.render(tn, True, C['gold'] if sel else C['text_dim'])
            surface.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

        # 内容
        yy = 140 - self.scroll * 70

        if self.tab == 0:  # 天赋
            for i, t in enumerate(BESTIARY_TALENTS):
                tid, name, desc, tier = t
                y = yy + i * 68
                if y < 130 or y > H-20: continue
                c = tier_colors_b.get(tier, (200,200,200))
                tn = tier_names_b.get(tier, '')
                # 卡片
                pygame.draw.rect(surface, (22,15,38), (80, y, W-160, 60), border_radius=6)
                pygame.draw.rect(surface, (*c, 60), (80, y, W-160, 60), 1, border_radius=6)
                # 图标
                pygame.draw.circle(surface, c, (115, y+30), 18)
                pygame.draw.circle(surface, (255,255,255), (115, y+30), 14)
                ic = font_med.render(tid[:2].upper(), True, c)
                surface.blit(ic, (115-ic.get_width()//2, y+22))
                # 名称
                nm = font_med.render(name, True, (240,240,255))
                surface.blit(nm, (145, y+8))
                # 描述
                ds = font_small.render(desc, True, C['text_dim'])
                surface.blit(ds, (145, y+34))
                # 稀有度标签
                rt = font_small.render(tn, True, c)
                surface.blit(rt, (W-140, y+16))

        elif self.tab == 1:  # 怪物
            for i, e in enumerate(BESTIARY_ENEMIES):
                eid, name, desc, color = e
                y = yy + i * 68
                if y < 130 or y > H-20: continue
                pygame.draw.rect(surface, (22,15,38), (80, y, W-160, 60), border_radius=6)
                pygame.draw.rect(surface, (*color[:3], 60), (80, y, W-160, 60), 1, border_radius=6)
                pygame.draw.circle(surface, color, (115, y+30), 16)
                pygame.draw.circle(surface, (255,255,255,80), (115, y+30), 8)
                nm = font_med.render(name, True, (240,240,255))
                surface.blit(nm, (145, y+12))
                ds = font_small.render(desc, True, C['text_dim'])
                surface.blit(ds, (145, y+34))

        else:  # Boss
            for i, b in enumerate(BESTIARY_BOSSES):
                bid, name, desc, color = b
                y = yy + i * 68
                if y < 130 or y > H-20: continue
                pygame.draw.rect(surface, (22,15,38), (80, y, W-160, 60), border_radius=6)
                pygame.draw.rect(surface, (*color[:3], 60), (80, y, W-160, 60), 1, border_radius=6)
                pygame.draw.circle(surface, color, (115, y+30), 16)
                nm = font_med.render(name, True, (240,240,255))
                surface.blit(nm, (145, y+12))
                ds = font_small.render(desc, True, C['text_dim'])
                surface.blit(ds, (145, y+34))

        # 底部提示
        footer = font_small.render("← → 切换标签 · ↑↓ 滚动 · ESC 关闭", True, (70,60,90))
        surface.blit(footer, (W//2 - footer.get_width()//2, H-30))


# ──────────────────────────────────────
#  胜利界面
# ──────────────────────────────────────
class VictoryScreen:
    def __init__(self):
        self.active = False
        self.player = None
        self.wave = 0
        self.timer = 0
        self.particles = []

    def show(self, player, wave):
        self.active = True
        self.player = player
        self.wave = wave
        self.timer = 0
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, W), 'y': random.randint(-H, 0),
                'vx': random.uniform(-1, 1), 'vy': random.uniform(1, 4),
                'size': random.randint(3, 8),
                'color': random.choice([(255,215,0),(255,100,100),(255,200,100),(200,150,255)]),
                'alpha': random.uniform(0.3, 1.0),
            })

    def update(self):
        if not self.active: return
        self.timer += 1
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.02
            p['alpha'] -= 0.003
            if p['alpha'] <= 0 or p['y'] > H+10:
                p['x'] = random.randint(0, W)
                p['y'] = -10
                p['alpha'] = random.uniform(0.3, 1.0)
                p['vy'] = random.uniform(1, 4)

    def handle_click(self, pos, game):
        if not self.active or self.timer < 90: return False
        # 返回菜单
        r1 = pygame.Rect(W//2-130, H//2+140, 120, 45)
        r2 = pygame.Rect(W//2+10, H//2+140, 120, 45)
        if r1.collidepoint(pos):
            game.state = 'menu'
            game.main_menu.active = True
            self.active = False
            return True
        if r2.collidepoint(pos):
            game.reset()
            self.active = False
            return True
        return False

    def draw(self, surface):
        if not self.active: return
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 花瓣雨
        for p in self.particles:
            alpha = max(0, int(p['alpha'] * 255))
            if alpha < 1: continue
            s = pygame.Surface((int(p['size']*2), int(p['size']*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], alpha), (int(p['size']), int(p['size'])), int(p['size']))
            surface.blit(s, (p['x']-p['size'], p['y']-p['size']))

        # 主标题
        if self.timer > 30:
            a = min(255, (self.timer-30)*8)
            title = font_huge.render("🎉 恭喜通关！", True, C['gold'])
            title.set_alpha(a)
            surface.blit(title, (W//2 - title.get_width()//2, H//2 - 170))

        # 副标题
        if self.timer > 50:
            a = min(255, (self.timer-50)*8)
            sub = font_med.render("你成功闯过了全部 100 关！", True, (255, 215, 100))
            sub.set_alpha(a)
            surface.blit(sub, (W//2 - sub.get_width()//2, H//2 - 100))
            sub2 = font_med.render("轮回之巅，当之无愧！", True, C['text_dim'])
            sub2.set_alpha(a)
            surface.blit(sub2, (W//2 - sub2.get_width()//2, H//2 - 60))

        # 战绩
        if self.timer > 70 and self.player:
            a = min(255, (self.timer-70)*6)
            texts = [
                f"最终等级：{self.player.level}",
                f"击杀数：{self.player.kills}",
                f"天赋数：{len(self.player.talents_taken)}",
                f"总伤害：{self.player.total_dmg_dealt:.0f}",
            ]
            for i, t in enumerate(texts):
                txt = font_med.render(t, True, C['text'])
                txt.set_alpha(a)
                surface.blit(txt, (W//2 - txt.get_width()//2, H//2 - 15 + i*40))

        # 按钮
        if self.timer > 90:
            r1 = pygame.Rect(W//2-130, H//2+140, 120, 45)
            r2 = pygame.Rect(W//2+10, H//2+140, 120, 45)
            for r, txt, col in [(r1, '返回菜单', (60,40,80)), (r2, '再来一次', (80,40,60))]:
                pygame.draw.rect(surface, col, r, border_radius=6)
                pygame.draw.rect(surface, C['gold'], r, 2, border_radius=6)
                t = font_med.render(txt, True, C['gold'])
                surface.blit(t, (r.centerx - t.get_width()//2, r.centery - t.get_height()//2))


# ──────────────────────────────────────
#  主菜单
# ──────────────────────────────────────
class MainMenu:
    def __init__(self):
        self.active = True
        self.selected = 0  # 0=开始, 1=退出
        self.options = [
            {"text": "开始游戏", "action": "start"},
            {"text": "图鉴系统", "action": "bestiary"},
            {"text": "退出游戏", "action": "quit"},
        ]
        self.floating_hearts = []
        for _ in range(20):
            self.floating_hearts.append({
                'x': random.randint(0, W), 'y': random.randint(0, H),
                'size': random.randint(4, 14), 'speed': random.uniform(0.3, 1.2),
                'alpha': random.uniform(0.1, 0.4), 'phase': random.random() * math.pi * 2,
                'hue': random.uniform(320, 360),
            })
        self.timer = 0
        self.bg_particles = []
        for _ in range(50):
            self.bg_particles.append({
                'x': random.randint(0, W), 'y': random.randint(0, H),
                'r': random.uniform(0.5, 2), 'speed': random.uniform(0.1, 0.5),
                'alpha': random.uniform(0.1, 0.5),
            })

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                action = self.options[self.selected]['action']
                if action == 'start':
                    self.active = False
                    return 'start'
                elif action == 'bestiary':
                    return 'bestiary'
                elif action == 'quit':
                    return 'quit'
        if event.type == pygame.MOUSEMOTION:
            bx, by = W // 2 - 120, H // 2 + 40
            for i, opt in enumerate(self.options):
                if pygame.Rect(bx, by + i * 70, 240, 50).collidepoint(event.pos):
                    self.selected = i; break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            bx, by = W // 2 - 120, H // 2 + 40
            for i, opt in enumerate(self.options):
                if pygame.Rect(bx, by + i * 70, 240, 50).collidepoint(event.pos):
                    if opt['action'] == 'start': self.active = False; return 'start'
                    elif opt['action'] == 'bestiary': return 'bestiary'
                    elif opt['action'] == 'quit': return 'quit'
        return None

    def update(self):
        self.timer += 1
        for h in self.floating_hearts:
            h['y'] -= h['speed']
            h['x'] += math.sin(self.timer * 0.01 + h['phase']) * 0.3
            if h['y'] < -20: h['y'] = H + 20; h['x'] = random.randint(0, W)
        for p in self.bg_particles:
            p['y'] -= p['speed']
            if p['y'] < -5: p['y'] = H + 5; p['x'] = random.randint(0, W)

    def draw(self, surface):
        # 渐变背景
        for y in range(H):
            t = y / H; r = int(8 + t*8); g = int(3 + t*6); b = int(18 + t*16)
            pygame.draw.line(surface, (r, g, b), (0, y), (W, y))
        # 网格
        for x in range(0, W, 50):
            a = int(8 + math.sin(self.timer*0.005 + x*0.01)*4)
            pygame.draw.line(surface, (25,18,40,a), (x,0), (x,H))
        for y in range(0, H, 50):
            a = int(8 + math.sin(self.timer*0.005 + y*0.01)*4)
            pygame.draw.line(surface, (25,18,40,a), (0,y), (W,y))
        # 星光
        for p in self.bg_particles:
            a = int(p['alpha'] * 255 * (0.5 + 0.5*math.sin(self.timer*0.02 + p['x'])))
            if a > 0:
                s = pygame.Surface((int(p['r']*2),int(p['r']*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (200,180,255,a), (int(p['r']),int(p['r'])), int(p['r']))
                surface.blit(s, (p['x']-p['r'], p['y']-p['r']))
        # 浮动爱心
        for h in self.floating_hearts:
            a = int(h['alpha'] * 255 * (0.6 + 0.4*math.sin(self.timer*0.03 + h['phase'])))
            if a < 1: continue
            s = h['size']; sx, sy = int(h['x']), int(h['y'])
            clr = (255, int(100+50*math.sin(self.timer*0.01+h['phase'])), int(180+50*math.cos(self.timer*0.01+h['phase'])), a)
            surf = pygame.Surface((s*2,s*2), pygame.SRCALPHA)
            pts = [(s + s*0.8*math.sin(i/12*math.pi*2)**3,
                    s - s*(0.7*math.cos(i/12*math.pi*2) - 0.3*math.cos(2*i/12*math.pi*2) - 0.1*math.cos(3*i/12*math.pi*2)))
                   for i in range(12)]
            pygame.draw.polygon(surf, clr, pts)
            surface.blit(surf, (sx-s, sy-s))
        # 标题
        ty = H // 2 - 140
        sh = font_huge.render("轮回之战", True, (20,10,40)); sh.set_alpha(100)
        for dx, dy in [(3,3),(-1,2),(2,-1)]: surface.blit(sh, (W//2 - sh.get_width()//2 + dx, ty + dy))
        title = font_huge.render("轮回之战", True, C['gold'])
        ga = int(60 + 40*math.sin(self.timer*0.03))
        gs = pygame.Surface((title.get_width()+60, title.get_height()+30), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (255,215,0,ga), gs.get_rect().inflate(-10,-10), 3)
        surface.blit(gs, (W//2 - gs.get_width()//2, ty-15))
        surface.blit(title, (W//2 - title.get_width()//2, ty))
        st = font_med.render("— Roguelike 生存 —", True, C['text_dim'])
        surface.blit(st, (W//2 - st.get_width()//2, ty+80))
        ly = ty + 115; la = int(100 + 80*math.sin(self.timer*0.02))
        ln = pygame.Surface((300,2), pygame.SRCALPHA); ln.fill((255,215,0,la))
        surface.blit(ln, (W//2-150, ly))
        # 按钮
        bx, by = W // 2 - 120, H // 2 + 40
        for i, opt in enumerate(self.options):
            r = pygame.Rect(bx, by + i*70, 240, 50)
            if i == self.selected:
                pygame.draw.rect(surface, (40,25,60), r, border_radius=6)
                ba = int(180 + 60*math.sin(self.timer*0.06))
                bs = pygame.Surface((r.w,r.h), pygame.SRCALPHA)
                pygame.draw.rect(bs, (255,215,0,ba), bs.get_rect(), 2, border_radius=6)
                surface.blit(bs, (r.x, r.y))
                arrow = font_med.render("▶", True, C['gold'])
                surface.blit(arrow, (r.x-35, r.y+10))
            else:
                pygame.draw.rect(surface, (20,12,35), r, border_radius=6)
                pygame.draw.rect(surface, (50,35,80), r, 1, border_radius=6)
            c = C['gold'] if i == self.selected else C['text_dim']
            t = font_med.render(opt['text'], True, c)
            surface.blit(t, (r.centerx - t.get_width()//2, r.centery - t.get_height()//2))
        # 底部提示
        hint = font_small.render("↑↓ 选择 · Enter 确认 · ESC 退出", True, (70,60,90))
        surface.blit(hint, (W//2 - hint.get_width()//2, H-40))
        ver = font_small.render("v1.0", True, (40,35,55))
        surface.blit(ver, (15, H-30))


# ──────────────────────────────────────
#  作弊菜单
# ──────────────────────────────────────
class CheatMenu:
    def __init__(self):
        self.open = False
        self.tab = 0
        self.scroll = 0
        self.timer = 0
        self.btn_rect = pygame.Rect(8, 8, 48, 22)
        self.panel_w, self.panel_h = 260, 420
        self.item_h = 34
        self.visible = 9
        self.hovered_talent = -1
        self.hovered_talent_desc = ""
        # 作弊菜单专用小字体
        self.fnt = pygame.font.Font(_zh_font_path, 20) if _zh_font_path else pygame.font.SysFont('microsoftyahei,tahoma', 20)
        self.fnt_bold = pygame.font.Font(_zh_font_path, 22) if _zh_font_path else pygame.font.SysFont('microsoftyahei,tahoma', 22)
        self.fnt_tip = pygame.font.Font(_zh_font_path, 18) if _zh_font_path else pygame.font.SysFont('microsoftyahei,tahoma', 18)

    def toggle(self):
        self.open = not self.open
        self.scroll = 0

    def _list_y(self, panel_top):
        """可视列表区域的起始 Y"""
        return panel_top + 76

    def _item_pos(self, idx, panel_top):
        """第 idx 个天赋/关卡的屏幕 Y 坐标"""
        return self._list_y(panel_top) + (idx - self.scroll) * self.item_h

    def handle_event(self, event, game):
        px, py = 15, 35

        # 鼠标移动 → 检测悬停
        if event.type == pygame.MOUSEMOTION and self.open:
            mx, my = event.pos
            self.hovered_talent = -1
            self.hovered_talent_desc = ""
            if self.tab == 0 and game.player and self.open:
                for i, t in enumerate(TALENTS):
                    y = self._item_pos(i, py)
                    if pygame.Rect(px + 12, y, self.panel_w - 24, self.item_h - 2).collidepoint(mx, my):
                        self.hovered_talent = i
                        self.hovered_talent_desc = t[2]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.btn_rect.collidepoint(pos):
                self.toggle()
                return True
            if not self.open:
                return False

            # 关闭
            if pygame.Rect(px + self.panel_w - 34, py + 6, 26, 24).collidepoint(pos):
                self.open = False
                return True

            # 标签
            for i in range(2):
                tx = px + 16 + i * 96
                if pygame.Rect(tx, py + 38, 88, 28).collidepoint(pos):
                    self.tab = i; self.scroll = 0; return True

            # 天赋点击
            if self.tab == 0 and game.player:
                for i, t in enumerate(TALENTS):
                    y = self._item_pos(i, py)
                    if y < py + 76 or y > py + self.panel_h - 20:
                        continue
                    if pygame.Rect(px + 12, y, self.panel_w - 24, self.item_h - 2).collidepoint(pos):
                        t[4](game.player)
                        game.player.talents_taken.append(t)
                        return True

            # 关卡点击
            if self.tab == 1 and game.wave_mgr:
                for w in range(1, 101):
                    y = self._item_pos(w - 1, py)  # idx = w-1
                    if y < py + 76 or y > py + self.panel_h - 20:
                        continue
                    if pygame.Rect(px + 12, y, self.panel_w - 24, self.item_h - 2).collidepoint(pos):
                        # 减1因为 start_next_wave 会 +1
                        game.wave_mgr.wave = w - 1
                        game.wave_mgr.between_waves = True
                        game.wave_mgr.wave_timer = 30
                        game.wave_mgr.boss_active = False
                        game.wave_mgr.boss = None
                        game.wave_mgr.spawn_count = 0
                        game.wave_mgr.enemies_left = 0
                        if hasattr(game, 'enemies'): game.enemies.clear()
                        self.open = False
                        return True

        # 滚轮
        if self.open and event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            self.scroll = max(0, self.scroll - 1) if event.button == 4 else min(self.scroll + 1, self._max_scroll())
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1: self.toggle(); return True
            if self.open:
                if event.key == pygame.K_DOWN: self.scroll = min(self.scroll + 1, self._max_scroll()); return True
                if event.key == pygame.K_UP: self.scroll = max(0, self.scroll - 1); return True
                if event.key == pygame.K_ESCAPE: self.open = False; return True
        return False

    def _max_scroll(self):
        count = len(TALENTS) if self.tab == 0 else 100
        return max(0, count - self.visible)

    def update(self):
        self.timer += 1

    def draw(self, surface, game):
        px, py = 15, 35
        # 齿轮按钮
        cg = C['gold'] if self.open else (150, 140, 170)
        bg_gear = (40, 30, 55, 180) if self.open else (25, 18, 40, 120)
        s = pygame.Surface((self.btn_rect.w, self.btn_rect.h), pygame.SRCALPHA)
        s.fill(bg_gear)
        pygame.draw.rect(s, (*cg[:3], 80), s.get_rect(), 1, 3)
        surface.blit(s, (self.btn_rect.x, self.btn_rect.y))
        surface.blit(font_small.render("⚙", True, cg), (self.btn_rect.x + 3, self.btn_rect.y - 2))
        if not self.open:
            return

        # 面板
        panel = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        panel.fill((8, 4, 18, 240))
        pygame.draw.rect(panel, (80, 60, 120, 200), panel.get_rect(), 2, 8)
        surface.blit(panel, (px, py))

        surface.blit(self.fnt_bold.render("⚡ 作弊", True, C['gold']), (px + 12, py + 8))
        surface.blit(self.fnt.render("✕", True, (180, 140, 160)), (px + self.panel_w - 28, py + 9))

        # 标签
        for i, tn in enumerate(['天赋', '关卡']):
            tx = px + 16 + i * 96
            sel = i == self.tab
            s2 = pygame.Surface((88, 26), pygame.SRCALPHA)
            s2.fill((50, 35, 70, 200) if sel else (25, 18, 40, 180))
            if sel: pygame.draw.rect(s2, (*C['gold'][:3], 200), s2.get_rect(), 1, 5)
            surface.blit(s2, (tx, py + 38))
            t2 = self.fnt.render(tn, True, C['gold'] if sel else C['text_dim'])
            surface.blit(t2, (tx + 44 - t2.get_width()//2, py + 43))

        cx, cy = px + 12, py + 76
        list_w, list_h = self.panel_w - 24, self.panel_h - 100

        # === 天赋标签 ===
        if self.tab == 0 and game.player:
            for i, t in enumerate(TALENTS):
                y = self._item_pos(i, py)
                if y < cy - self.item_h or y > cy + list_h:
                    continue
                tc = tier_colors_b.get(t[3], (200, 200, 200))
                bg2 = pygame.Surface((list_w, self.item_h - 2), pygame.SRCALPHA)
                bg2.fill((30, 20, 48, 200))
                pygame.draw.rect(bg2, (*tc[:3], 50), bg2.get_rect(), 1, 4)
                surface.blit(bg2, (cx, y))
                pygame.draw.circle(surface, tc, (cx + 12, y + self.item_h//2), 4)
                surface.blit(self.fnt.render(t[1], True, (230, 230, 255)), (cx + 22, y + 7))
                rt2 = self.fnt.render(tier_names_b.get(t[3], ''), True, tc)
                surface.blit(rt2, (cx + list_w - rt2.get_width() - 6, y + 7))

            # 悬停提示
            if self.hovered_talent >= 0 and self.hovered_talent < len(TALENTS):
                mx, my = pygame.mouse.get_pos()
                desc = self.hovered_talent_desc
                tip = self.fnt.render(desc, True, (255, 255, 200))
                tw, th = tip.get_width() + 14, 26
                tx2 = min(mx + 16, W - tw - 10)
                ty2 = my - 13
                tip_surf = pygame.Surface((tw, th), pygame.SRCALPHA)
                tip_surf.fill((20, 12, 35, 230))
                pygame.draw.rect(tip_surf, C['gold'], tip_surf.get_rect(), 1, 4)
                surface.blit(tip_surf, (tx2, ty2))
                surface.blit(tip, (tx2 + 7, ty2 + 4))

        # === 关卡标签 ===
        elif self.tab == 1 and game.wave_mgr:
            for w in range(1, 101):
                i = w - 1
                y = self._item_pos(i, py)
                if y < cy - self.item_h or y > cy + list_h:
                    continue
                is_cur = w == game.wave_mgr.wave
                bg2 = pygame.Surface((list_w, self.item_h - 2), pygame.SRCALPHA)
                bg2.fill((35, 22, 55, 200) if is_cur else (20, 12, 35, 180))
                if is_cur: pygame.draw.rect(bg2, (*C['gold'][:3], 150), bg2.get_rect(), 1, 4)
                surface.blit(bg2, (cx, y))
                mk = "👑" if w % 10 == 0 else "⭐" if w % 5 == 0 else "  "
                wt = self.fnt.render(f"{mk} 第 {w} 关", True, C['gold'] if is_cur else C['text'])
                surface.blit(wt, (cx + 12, y + 7))
                if is_cur:
                    surface.blit(self.fnt.render("◀", True, C['gold']), (cx + list_w - 18, y + 7))

        # 滚动条
        if self._max_scroll() > 0:
            bar_h = list_h * self.visible / (len(TALENTS) if self.tab == 0 else 100)
            bar_y = cy + (self.scroll / self._max_scroll()) * (list_h - bar_h)
            bar = pygame.Surface((4, int(bar_h)), pygame.SRCALPHA)
            bar.fill((120, 100, 160, 150))
            surface.blit(bar, (px + self.panel_w - 11, int(bar_y)))

        surface.blit(self.fnt_tip.render("滚轮 · F1 开关", True, (70, 60, 90)),
                     (px + 12, py + self.panel_h - 22))


# ──────────────────────────────────────
#  游戏主类
# ──────────────────────────────────────
class Game:
    def __init__(self):
        self.state = 'menu'
        self.main_menu = MainMenu()
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.xp_orbs = []
        self.particles = []
        self.dmg_texts = []
        self.wave_mgr = None
        self.talent_panel = None
        self.game_over = None
        self.running = True
        self.paused = False
        self.camera = type('obj', (object,), {'x': 0, 'y': 0})()
        self.font_small = font_small
        self.font_med = font_med
        self.font_large = font_large
        self.font_huge = font_huge
        self.bestiary = Bestiary()
        self.cheat_menu = CheatMenu()
        self.victory_screen = VictoryScreen()
        self._last_vx = 0
        self._last_vy = 0
        self.wave_announce = 0
        self.wave_announce_text = ""

    def reset(self):
        self._last_vx = 0
        self._last_vy = 0
        self.state = 'playing'
        # 魔法棒鼠标，始终隐藏系统光标
# pygame.mouse.set_visible(False)
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.xp_orbs = []
        self.particles = []
        self.dmg_texts = []
        self.wave_mgr = WaveManager()
        self.talent_panel = TalentPanel()
        self.game_over = GameOver()
        self.victory_screen = VictoryScreen()
        self.paused = False
        self.wave_announce = 0
        self.wave_announce_text = ""
        self.shake_x = 0
        self.shake_y = 0
        self.shake_timer = 0
        self.wave_mgr.between_waves = True
        self.wave_mgr.wave_timer = 60

    def shake(self, intensity=5, duration=10):
        self.shake_timer = duration
        self.shake_amount = intensity

    def spawn_xp(self, x, y, value):
        # 分裂成小球
        total = value
        while total > 0:
            v = min(total, random.randint(2, 6))
            total -= v
            ox = x + random.uniform(-15, 15)
            oy = y + random.uniform(-15, 15)
            self.xp_orbs.append(XPOrb(ox, oy, v))

    def find_nearest_enemy(self, x, y, max_dist):
        nearest = None
        nd = max_dist
        for e in self.enemies:
            if e.dead:
                continue
            d = dist((x, y), (e.x, e.y))
            if d < nd:
                nd = d
                nearest = e
        # 也搜索Boss
        boss = self.wave_mgr.boss if self.wave_mgr else None
        if boss and not boss.dead:
            d = dist((x, y), (boss.x, boss.y))
            if d < nd:
                nd = d
                nearest = boss
        return nearest

    def add_particles(self, x, y, color, count=10, speed=3):
        for _ in range(count):
            a = random.random() * math.pi * 2
            sp = random.random() * speed
            self.particles.append(Particle(x, y, math.cos(a)*sp, math.sin(a)*sp, color, random.randint(15, 30)))

    def fire_bullets(self, target):
        p = self.player
        base_angle = angle((p.x, p.y), (target.x, target.y))
        spread = 0.1

        for i in range(p.multi):
            a = base_angle + (i - (p.multi-1)/2) * spread
            # 从玩家位置偏移发射
            ox = p.x + math.cos(a) * p.radius
            oy = p.y + math.sin(a) * p.radius
            b = Bullet(ox, oy, target, p.dmg, p.pierce, p.fire_chance, p.ice_chance, p.chain_chance)
            b.vx = math.cos(a) * b.speed
            b.vy = math.sin(a) * b.speed
            self.bullets.append(b)

    def process_talent_selection(self):
        self.talent_panel.show(self.player)
        self.paused = True

    def update(self):
        # ── 图鉴 ──
        if self.bestiary.active:
            self.bestiary.update()
            return

        # ── 胜利画面 ──
        if self.victory_screen.active:
            self.victory_screen.update()
            return

        # ── 主菜单 ──
        if self.state == 'menu':
            self.main_menu.update()
            return

        # ── 游戏结束 ──
        if self.state == 'game_over':
            self.game_over.update()
            return

        if self.paused and self.talent_panel.active:
            self.talent_panel.update()
            return

        # 震屏
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_x = random.randint(-self.shake_amount, self.shake_amount)
            self.shake_y = random.randint(-self.shake_amount, self.shake_amount)
        else:
            self.shake_x = self.shake_y = 0

        # 玩家移动 — pygame.key.get_pressed() 是可靠的
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        self.player.move_x, self.player.move_y = dx, dy
        self.player.update()
        self._last_vx = dx * self.player.move_speed
        self._last_vy = dy * self.player.move_speed

        # 相机跟随玩家（平滑追踪）
        target_cx = self.player.x - W//2
        target_cy = self.player.y - H//2
        self.camera.x += (target_cx - self.camera.x) * 0.1
        self.camera.y += (target_cy - self.camera.y) * 0.1
        self.camera.x = clamp(self.camera.x, 0, WORLD_W - W)
        self.camera.y = clamp(self.camera.y, 0, WORLD_H - H)

        # 波次管理
        self.wave_mgr.update(self.enemies, self.player)

        # ── 检测通关 ──
        if self.wave_mgr.game_complete:
            self.state = 'victory'
            self.victory_screen.show(self.player, self.wave_mgr.wave - 1)
            self.wave_mgr.game_complete = False

        # 自动索敌攻击
        if self.player.can_attack():
            target = self.find_nearest_enemy(self.player.x, self.player.y, self.player.atk_range)
            if target:
                self.fire_bullets(target)
                self.player.reset_attack()

        # ── 子弹更新 ──
        for b in self.bullets[:]:
            b.update()
            if b.dead:
                self.bullets.remove(b)
                continue

            # 碰撞检测
            if b.target and not b.target.dead:
                d = dist((b.x, b.y), (b.target.x, b.target.y))
                if d < b.target.radius + 5 and id(b.target) not in b.hit:
                    dmg = b.dmg
                    b.target.take_damage(dmg, b)
                    b.on_hit(b.target)
                    self.player.total_dmg_dealt += dmg

                    # 伤害数字
                    self.dmg_texts.append(DamageText(b.target.x, b.target.y - 10, dmg))

                    # 粒子
                    self.add_particles(b.target.x, b.target.y, (255, 200, 100), 5)

                    # 效果
                    if b.fire_chance > 0:
                        b.target.apply_burn(b.fire_chance, 3, 180)
                    if b.ice_chance > 0:
                        b.target.apply_slow(b.ice_chance, 0.4, 120)

                    # 闪电链
                    if b.chain_chance > 0 and random.random() < b.chain_chance:
                        others = [e for e in self.enemies if not e.dead and e is not b.target
                                 and dist((b.x, b.y), (e.x, e.y)) < 200][:3]
                        for e in others:
                            e.take_damage(dmg * 0.5)
                            self.dmg_texts.append(DamageText(e.x, e.y - 10, dmg * 0.5, (100, 200, 255)))
                            self.add_particles(e.x, e.y, (100, 200, 255), 4)

                    # 生命偷取
                    if self.player.lifesteal > 0:
                        heal = dmg * self.player.lifesteal
                        self.player.hp = min(self.player.max_hp, self.player.hp + heal)

                    # 穿透
                    if b.pierce_left > 0:
                        b.pierce_left -= 1
                        # 找下一个目标
                        b.target = self.find_nearest_enemy(b.x, b.y, 300)
                        if not b.target:
                            b.life = 0
                    else:
                        b.life = 0

            # 边界删除
            if (b.x < -100 or b.x > WORLD_W+100 or b.y < -100 or b.y > WORLD_H+100):
                b.life = 0

        # ── 敌人更新 ──
        for e in self.enemies[:]:
            if e.dead:
                # 掉落 XP
                self.spawn_xp(e.x, e.y, e.xp_value)
                self.add_particles(e.x, e.y, e.color, 15, 4)
                self.player.kills += 1
                self.player.add_berserk_stack()
                self.enemies.remove(e)
                continue
            e.update(self.player.x, self.player.y)

            # 碰撞伤害
            d = dist((e.x, e.y), (self.player.x, self.player.y))
            if d < e.radius + self.player.radius:
                e.atk_timer = e.atk_cooldown
                actual = self.player.take_damage(e.dmg)
                if actual > 0:
                    self.dmg_texts.append(DamageText(self.player.x, self.player.y - 20, actual, (255, 100, 100)))
                    self.add_particles(self.player.x, self.player.y, (255, 80, 80), 8)
                    self.shake(4, 8)

        # ── Boss 更新 ──
        boss = self.wave_mgr.boss
        if boss and not boss.dead:
            boss.update(self.player.x, self.player.y)

            # Boss 碰撞伤害
            d = dist((boss.x, boss.y), (self.player.x, self.player.y))
            if d < boss.radius + self.player.radius:
                if boss.atk_timer <= 0:
                    boss.atk_timer = 30
                    actual = self.player.take_damage(boss.dmg)
                    if actual > 0:
                        self.dmg_texts.append(DamageText(self.player.x, self.player.y - 20, actual, (255, 50, 50)))
                        self.add_particles(self.player.x, self.player.y, (255, 50, 50), 12)
                        self.shake(8, 12)

            # Boss 冲刺伤害
            if boss.charging:
                d = dist((boss.x, boss.y), (self.player.x, self.player.y))
                if d < boss.radius + self.player.radius:
                    actual = self.player.take_damage(boss.dmg * 1.5)
                    self.shake(10, 15)
                    boss.charging = False
                    boss.special_timer = boss.special_cooldown

            # Boss 子弹碰撞
            for b in self.bullets[:]:
                if boss.dead:
                    break
                d = dist((b.x, b.y), (boss.x, boss.y))
                if d < boss.radius + b.radius and id(boss) not in b.hit:
                    dmg = b.dmg
                    boss.take_damage(dmg, b)
                    b.on_hit(boss)
                    self.player.total_dmg_dealt += dmg
                    self.dmg_texts.append(DamageText(boss.x + random.uniform(-30, 30), boss.y - 20, dmg, C['gold']))
                    self.add_particles(b.x, b.y, (255, 200, 50), 8)

                    if self.player.lifesteal > 0:
                        self.player.hp = min(self.player.max_hp, self.player.hp + dmg * self.player.lifesteal)

                    if b.pierce_left > 0:
                        b.pierce_left -= 1
                    else:
                        b.life = 0
                    break

        # Boss 死亡
        if boss and boss.dead:
            self.spawn_xp(boss.x, boss.y, boss.xp_value)
            self.add_particles(boss.x, boss.y, boss.color, 40, 8)
            self.shake(8, 15)
            self.wave_mgr.boss = None
            self.wave_mgr.boss_active = False  # ← 防止 Boss 无限复活！

        # ── XP 球更新 ──
        for orb in self.xp_orbs[:]:
            orb.update(self.player.x, self.player.y)
            if orb.collected:
                if self.player.gain_xp(orb.value):
                    # 升级！
                    self.process_talent_selection()
                self.xp_orbs.remove(orb)

        # ── 粒子更新 ──
        for p in self.particles[:]:
            p.update()
            if p.dead:
                self.particles.remove(p)

        # ── 伤害数字更新 ──
        for dt in self.dmg_texts[:]:
            dt.update()
            if dt.dead:
                self.dmg_texts.remove(dt)

        # ── 检查死亡 ──
        if self.player.hp <= 0:
            self.state = 'game_over'
            # 魔法棒鼠标，始终隐藏系统光标
# pygame.mouse.set_visible(True)
            self.add_particles(self.player.x, self.player.y, C['player'], 30, 6)
            self.game_over.show(self.player, self.wave_mgr.wave)

        # ── 作弊菜单更新 ──
        self.cheat_menu.update()

    def draw(self):
        # ── 图鉴 ──
        if self.bestiary.active:
            self.bestiary.draw(screen)
            draw_magic_wand(screen)
            pygame.display.flip()
            return

        # ── 胜利画面 ──
        if self.victory_screen.active:
            self.victory_screen.draw(screen)
            draw_magic_wand(screen)
            pygame.display.flip()
            return

        # ── 主菜单 ──
        if self.state == 'menu':
            self.main_menu.draw(screen)
            draw_magic_wand(screen)
            pygame.display.flip()
            return

        # 背景
        screen.fill(C['bg'])

        # 随相机滚动的网格
        gs = 60
        cam_x, cam_y = int(self.camera.x), int(self.camera.y)
        start_x = -(cam_x % gs)
        start_y = -(cam_y % gs)
        for x in range(start_x, W + gs, gs):
            wx = cam_x + x
            if 0 <= wx <= WORLD_W:
                pygame.draw.line(screen, C['grid'], (x, 0), (x, H))
        for y in range(start_y, H + gs, gs):
            wy = cam_y + y
            if 0 <= wy <= WORLD_H:
                pygame.draw.line(screen, C['grid'], (0, y), (W, y))

        # 世界边界（红色发光边框，在屏幕边缘可见时显示）
        v_left = cam_x; v_right = cam_x + W; v_top = cam_y; v_bottom = cam_y + H
        if v_left < 0:
            pygame.draw.line(screen, (255, 50, 50), (-cam_x, 0), (-cam_x, H), 3)
        if v_right > WORLD_W:
            pygame.draw.line(screen, (255, 50, 50), (WORLD_W - cam_x, 0), (WORLD_W - cam_x, H), 3)
        if v_top < 0:
            pygame.draw.line(screen, (255, 50, 50), (0, -cam_y), (W, -cam_y), 3)
        if v_bottom > WORLD_H:
            pygame.draw.line(screen, (255, 50, 50), (0, WORLD_H - cam_y), (W, WORLD_H - cam_y), 3)

        # 绘制所有对象到屏幕（带相机偏移）
        for orb in self.xp_orbs:
            orb.draw(screen, self.camera)
        for e in self.enemies:
            if not e.dead:
                e.draw(screen, self.camera)
        boss = self.wave_mgr.boss
        if boss and not boss.dead:
            boss.draw(screen, self.camera)
        for b in self.bullets:
            b.draw(screen, self.camera)
        for p in self.particles:
            p.draw(screen, self.camera)
        for dt in self.dmg_texts:
            dt.draw(screen, self.camera)
        self.player.draw(screen, self.camera)

        # UI（不受震屏影响）
        draw_ui(screen, self.player, self.wave_mgr, self.xp_orbs, self._last_vx, self._last_vy)

        # 天赋面板
        if self.talent_panel.active:
            self.talent_panel.draw(screen)

        # 游戏结束
        self.game_over.draw(screen)

        # Boss血条在UI里已经画了

        # 作弊菜单（最上层绘制）
        self.cheat_menu.draw(screen, self)

        draw_magic_wand(screen)
        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        # ── 图鉴事件 ──
        if self.bestiary.active:
            self.bestiary.handle_event(event)
            return

        # ── 胜利画面事件 ──
        if self.victory_screen.active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = 'menu'
                self.main_menu.active = True
                self.victory_screen.active = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.victory_screen.handle_click(event.pos, self)
                return
            return

        # ── 主菜单事件 ──
        if self.state == 'menu':
            result = self.main_menu.handle_event(event)
            if result == 'quit':
                self.running = False
            elif result == 'bestiary':
                self.bestiary.active = True
            elif result == 'start':
                self.reset()
            return

        # ── 作弊菜单（游戏中） ──
        if self.state == 'playing':
            if self.cheat_menu.handle_event(event, self):
                return

        # ── 游戏中按键处理（仅处理单次按键，移动用 get_pressed）──
        if self.state == 'playing' and self.player:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = 'menu'
                self.main_menu.active = True
                self.player.move_x = 0
                self.player.move_y = 0
                return

        # ── 游戏结束按键 ──
        if self.state == 'game_over':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = 'menu'
                    self.main_menu.active = True
                    # 魔法棒鼠标，始终隐藏系统光标
# pygame.mouse.set_visible(True)
                    return
                if event.key == pygame.K_r:
                    self.reset()
                    return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 天赋选择
            if self.talent_panel and self.talent_panel.active:
                if self.talent_panel.handle_click(event.pos, self.player):
                    self.paused = False
                return

            # 游戏结束
            if self.state == 'game_over':
                self.game_over.handle_click(event.pos, self)
                return

    def run(self):
        while self.running:
            try:
                for event in pygame.event.get():
                    self.handle_event(event)

                self.update()
                self.draw()
                clock.tick(60)
            except Exception as e:
                import traceback
                with open('crash_log.txt', 'w', encoding='utf-8') as f:
                    traceback.print_exc(file=f)
                # 写入屏幕
                crash_surf = font_small.render(f'崩溃: {e}', True, (255,50,50))
                screen.blit(crash_surf, (10, 10))
                pygame.display.flip()
                pygame.time.wait(5000)

        pygame.quit()
        sys.exit()

# ──────────────────────────────────────
#  入口
# ──────────────────────────────────────
if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    except Exception as e:
        import traceback
        with open('D:\\游戏\\roguelike\\startup_crash.txt', 'w', encoding='utf-8') as f:
            traceback.print_exc(file=f)
        # 尝试显示错误
        try:
            crash_surf = font_small.render(f'启动失败: {e}', True, (255,50,50))
            screen.blit(crash_surf, (10, 10))
            pygame.display.flip()
            pygame.time.wait(10000)
        except: pass
        print(f'CRASH: {e}')
        traceback.print_exc()
