import pygame
import math
import heapq
import random
import json
import os
from collections import deque

# --- CONFIGURATION ---
pygame.init()
WIDTH, HEIGHT = 1000, 600
SIDEBAR_W = 350
MAP_W = WIDTH - SIDEBAR_W
FPS = 60

# Constants
POISON_DAMAGE = 8
VILLAGE_HEAL = 8
IDLE_HEAL = 2
BASE_UPKEEP_FREE = 1
BASE_ARMY_BONUS = 4
MAX_TURNS = 30

COLORS = {
    "GRASS": (100, 180, 90), "FOREST": (40, 100, 40), "MOUNTAIN": (130, 130, 130),
    "SHALLOW_WATER": (80, 140, 220), "DEEP_WATER": (40, 80, 160), "VILLAGE_P": (200, 180, 80), 
    "VILLAGE_E": (180, 80, 80), "VILLAGE_N": (150, 150, 150), "CASTLE": (180, 180, 180), "KEEP": (220, 220, 100),
    "ROAD": (200, 180, 140),
    "WHITE": (255, 255, 255), "BLACK": (0, 0, 0), "RED": (220, 50, 50),
    "BLUE": (50, 50, 220), "YELLOW": (255, 255, 0), "GREY": (150, 150, 150),
    "PANEL": (40, 40, 40), "LIGHT_BLUE": (173, 216, 230), "PINK": (255, 150, 150),
    "GREEN_BAR": (50, 200, 50), "YELLOW_BAR": (200, 200, 50), "RED_BAR": (200, 50, 50),
    "PURPLE": (150, 50, 200), "GREEN_POISON": (50, 200, 50), "FOG": (20, 20, 20), "EXPLORED": (60, 60, 60),
    "TROLL_GREEN": (50, 150, 50), "SKELETON_WHITE": (220, 220, 200), "HEALER_PINK": (220, 180, 200),
    "SLOW_BLUE": (100, 150, 255), "THIEF_GREY": (100, 100, 110), "CORPSE_GREEN": (90, 130, 70),
    "GHOUL_PURPLE": (120, 80, 130), "BAT_BLACK": (40, 40, 40), "GRYPHON_BROWN": (160, 120, 60),
    "SHOCK_SILVER": (180, 180, 200), "MERMAN_TEAL": (60, 180, 170), "NECRO_DARK": (70, 50, 80),
    "BERSERKER_ORANGE": (220, 120, 40), "DWARF_BROWN": (120, 80, 50), "SORCERESS_MAGENTA": (180, 80, 180)
}

HEX_SIZE = 35
HEX_WIDTH = math.sqrt(3) * HEX_SIZE
HEX_HEIGHT = 2 * HEX_SIZE
MAP_OFFSET_X = 30
MAP_OFFSET_Y = 30

# Pre-calculate hex vertices for performance
HEX_VERTICES = [
    (HEX_SIZE * math.cos(math.pi/180 * (60*i - 30)),
     HEX_SIZE * math.sin(math.pi/180 * (60*i - 30)))
    for i in range(6)
]

TERRAIN_TYPES = {
    "GRASS": {"cost": 1, "def": 20, "color": COLORS["GRASS"]},
    "FOREST": {"cost": 2, "def": 40, "color": COLORS["FOREST"]},
    "MOUNTAIN": {"cost": 3, "def": 50, "color": COLORS["MOUNTAIN"]},
    "SHALLOW_WATER": {"cost": 3, "def": 20, "color": COLORS["SHALLOW_WATER"]},
    "DEEP_WATER": {"cost": 99, "def": 10, "color": COLORS["DEEP_WATER"]},
    "VILLAGE": {"cost": 1, "def": 50, "color": COLORS["VILLAGE_N"]},
    "CASTLE": {"cost": 1, "def": 40, "color": COLORS["CASTLE"]},
    "KEEP": {"cost": 1, "def": 40, "color": COLORS["KEEP"]},
    "ROAD": {"cost": 1, "def": 0, "color": COLORS["ROAD"]}
}

TIME_OF_DAY = {
    "Morning": {"lawful": 0.0, "chaotic": 0.0, "color": (255, 200, 100, 40)},
    "Day":     {"lawful": 0.25, "chaotic": -0.25, "color": (255, 255, 200, 20)},
    "Evening": {"lawful": 0.0, "chaotic": 0.0, "color": (255, 150, 100, 40)},
    "Night":   {"lawful": -0.25, "chaotic": 0.25, "color": (50, 50, 150, 80)}
}

UNIT_COLORS = {
    "Troll": COLORS["TROLL_GREEN"], "Skeleton": COLORS["SKELETON_WHITE"], 
    "Revenant": COLORS["SKELETON_WHITE"], "Deathblade": COLORS["SKELETON_WHITE"],
    "Mage of Light": COLORS["HEALER_PINK"], "White Mage": COLORS["HEALER_PINK"],
    "Thief": COLORS["THIEF_GREY"], "Rogue": COLORS["THIEF_GREY"], "Assassin": COLORS["THIEF_GREY"],
    "Ghoul": COLORS["GHOUL_PURPLE"], "Necrophage": COLORS["GHOUL_PURPLE"], "Ghast": COLORS["GHOUL_PURPLE"],
    "Vampire Bat": COLORS["BAT_BLACK"], "Blood Bat": COLORS["BAT_BLACK"], "Dread Bat": COLORS["BAT_BLACK"],
    "Walking Corpse": COLORS["CORPSE_GREEN"], "Soulless": COLORS["CORPSE_GREEN"],
    "Gryphon Rider": COLORS["GRYPHON_BROWN"], "Gryphon Master": COLORS["GRYPHON_BROWN"],
    "Shock Trooper": COLORS["SHOCK_SILVER"], "Iron Mauler": COLORS["SHOCK_SILVER"],
    "Merman Fighter": COLORS["MERMAN_TEAL"], "Merman Warrior": COLORS["MERMAN_TEAL"], "Merman Hoplite": COLORS["MERMAN_TEAL"],
    "Necromancer": COLORS["NECRO_DARK"], "Lich": COLORS["NECRO_DARK"], "Ancient Lich": COLORS["NECRO_DARK"],
    "Berserker": COLORS["BERSERKER_ORANGE"], "Warrior of Light": COLORS["BERSERKER_ORANGE"],
    "Dwarvish Guardsman": COLORS["DWARF_BROWN"], "Dwarvish Stalwart": COLORS["DWARF_BROWN"], "Dwarvish Sentinel": COLORS["DWARF_BROWN"],
    "Sorceress": COLORS["SORCERESS_MAGENTA"], "Enchantress": COLORS["SORCERESS_MAGENTA"], "Hag": COLORS["SORCERESS_MAGENTA"],
    "Archer": COLORS["GREEN_BAR"], "Ranger": COLORS["GREEN_BAR"], "Sharpshooter": COLORS["GREEN_BAR"],
}

# --- HEX MATH ---
def hex_to_pixel(q, r):
    x = HEX_WIDTH * (q + r / 2) + MAP_OFFSET_X
    y = HEX_HEIGHT * 3/4 * r + MAP_OFFSET_Y
    return x, y

def pixel_to_hex(x, y):
    x -= MAP_OFFSET_X
    y -= MAP_OFFSET_Y
    q = (math.sqrt(3)/3 * x - 1./3 * y) / HEX_SIZE
    r = (2./3 * y) / HEX_SIZE
    return axial_round(q, r)

def axial_round(q, r):
    s = -q - r
    rq = round(q); rr = round(r); rs = round(s)
    q_diff = abs(rq - q); r_diff = abs(rr - r); s_diff = abs(rs - s)
    if q_diff > r_diff and q_diff > s_diff: rq = -rr - rs
    elif r_diff > s_diff: rr = -rq - rs
    return rq, rr

HEX_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

_NEIGHBOR_CACHE = {}
def get_neighbors(q, r):
    key = (q, r)
    if key not in _NEIGHBOR_CACHE:
        _NEIGHBOR_CACHE[key] = [(q+dq, r+dr) for dq, dr in HEX_DIRECTIONS]
    return _NEIGHBOR_CACHE[key]

def hex_distance(q1, r1, q2, r2):
    return int((abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) / 2)

# --- LEVEL DATA ---
LEVEL_DATA = {
    "Knight": {"next": "Lancer", "hp": 45, "dmg": 8, "xp_req": 20},
    "Lancer": {"next": "Paladin", "hp": 55, "dmg": 9, "xp_req": 30},
    "Paladin": {"next": None, "hp": 65, "dmg": 11, "xp_req": 999},
    
    "Archer": {"next": "Ranger", "hp": 35, "dmg": 6, "xp_req": 20},
    "Ranger": {"next": "Sharpshooter", "hp": 45, "dmg": 7, "xp_req": 30},
    "Sharpshooter": {"next": None, "hp": 55, "dmg": 9, "xp_req": 999},
    
    "Mage": {"next": "Arch Mage", "hp": 30, "dmg": 10, "xp_req": 20},
    "Arch Mage": {"next": "Great Mage", "hp": 40, "dmg": 12, "xp_req": 30},
    "Great Mage": {"next": None, "hp": 50, "dmg": 15, "xp_req": 999},
    
    "White Mage": {"next": "Mage of Light", "hp": 34, "dmg": 8, "xp_req": 20},
    "Mage of Light": {"next": None, "hp": 44, "dmg": 10, "xp_req": 999},
    
    "Thief": {"next": "Rogue", "hp": 30, "dmg": 6, "xp_req": 20},
    "Rogue": {"next": "Assassin", "hp": 40, "dmg": 7, "xp_req": 30},
    "Assassin": {"next": None, "hp": 50, "dmg": 9, "xp_req": 999},
    
    "Shock Trooper": {"next": "Iron Mauler", "hp": 55, "dmg": 15, "xp_req": 20},
    "Iron Mauler": {"next": None, "hp": 70, "dmg": 17, "xp_req": 999},
    
    "Gryphon Rider": {"next": "Gryphon Master", "hp": 45, "dmg": 8, "xp_req": 20},
    "Gryphon Master": {"next": None, "hp": 55, "dmg": 10, "xp_req": 999},
    
    "Merman Fighter": {"next": "Merman Warrior", "hp": 40, "dmg": 8, "xp_req": 20},
    "Merman Warrior": {"next": "Merman Hoplite", "hp": 50, "dmg": 9, "xp_req": 30},
    "Merman Hoplite": {"next": None, "hp": 60, "dmg": 11, "xp_req": 999},
    
    "Berserker": {"next": "Warrior of Light", "hp": 40, "dmg": 7, "xp_req": 20},
    "Warrior of Light": {"next": None, "hp": 50, "dmg": 8, "xp_req": 999},
    
    "Dwarvish Guardsman": {"next": "Dwarvish Stalwart", "hp": 50, "dmg": 6, "xp_req": 20},
    "Dwarvish Stalwart": {"next": "Dwarvish Sentinel", "hp": 60, "dmg": 7, "xp_req": 30},
    "Dwarvish Sentinel": {"next": None, "hp": 70, "dmg": 8, "xp_req": 999},
    
    "Sorceress": {"next": "Enchantress", "hp": 30, "dmg": 9, "xp_req": 20},
    "Enchantress": {"next": "Hag", "hp": 40, "dmg": 11, "xp_req": 30},
    "Hag": {"next": None, "hp": 50, "dmg": 13, "xp_req": 999},
    
    "Skeleton": {"next": "Revenant", "hp": 40, "dmg": 8, "xp_req": 20},
    "Revenant": {"next": "Deathblade", "hp": 50, "dmg": 10, "xp_req": 30},
    "Deathblade": {"next": None, "hp": 60, "dmg": 12, "xp_req": 999},
    
    "Troll": {"next": "Troll Warrior", "hp": 55, "dmg": 11, "xp_req": 20},
    "Troll Warrior": {"next": "Troll Champion", "hp": 65, "dmg": 13, "xp_req": 30},
    "Troll Champion": {"next": None, "hp": 75, "dmg": 15, "xp_req": 999},
    
    "Ghoul": {"next": "Necrophage", "hp": 35, "dmg": 8, "xp_req": 20},
    "Necrophage": {"next": "Ghast", "hp": 45, "dmg": 10, "xp_req": 30},
    "Ghast": {"next": None, "hp": 55, "dmg": 12, "xp_req": 999},
    
    "Vampire Bat": {"next": "Blood Bat", "hp": 25, "dmg": 6, "xp_req": 20},
    "Blood Bat": {"next": "Dread Bat", "hp": 35, "dmg": 8, "xp_req": 30},
    "Dread Bat": {"next": None, "hp": 45, "dmg": 10, "xp_req": 999},
    
    "Walking Corpse": {"next": "Soulless", "hp": 24, "dmg": 5, "xp_req": 20},
    "Soulless": {"next": None, "hp": 30, "dmg": 6, "xp_req": 999},
    
    "Necromancer": {"next": "Lich", "hp": 35, "dmg": 10, "xp_req": 20},
    "Lich": {"next": "Ancient Lich", "hp": 45, "dmg": 12, "xp_req": 30},
    "Ancient Lich": {"next": None, "hp": 55, "dmg": 15, "xp_req": 999}
}

CORPSE_LINE = {"Walking Corpse", "Soulless"}

# --- ENTITIES ---
class Unit:
    def __init__(self, base_name, name, hp, attacks, move_range, faction, q, r, alignment, shape="circle", cost=0, is_leader=False, regen=0, vision=4, resistances=None, terrain_mods=None, heals=0, level=1, xp_req=10, abilities=None, poison_immune=False):
        self.base_name = base_name
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attacks = attacks
        self.move_range = move_range
        self.faction = faction
        self.alignment = alignment
        self.shape = shape
        self.cost = cost
        self.is_leader = is_leader
        self.regen = regen
        self.vision = vision
        self.q = q
        self.r = r
        self.current_moves = move_range
        self.is_selected = False
        
        self.resistances = resistances if resistances else {}
        self.terrain_mods = terrain_mods if terrain_mods else {}
        self.heals = heals
        self.level = level
        self.xp = 0
        self.xp_req = xp_req
        self.abilities = abilities if abilities else []
        self.poison_immune = poison_immune
        
        self.pixel_x, self.pixel_y = hex_to_pixel(q, r)
        self.move_path = []
        self.damage_flash = 0
        self.level_up_flash = 0
        self.is_poisoned = False
        self.is_slowed = False
        self.has_acted = False
        self.moved_this_turn = False
        self.attacked_this_turn = False
        self.prev_q, self.prev_r = q, r
        self.prev_pixel_x, self.prev_pixel_y = self.pixel_x, self.pixel_y
        self.prev_moves = move_range
        self.prev_village_owner = "NEUTRAL"
        self.was_poisoned_before_move = False

    def _base_color(self):
        # Fix fragile matching by checking exact names first
        if self.name in UNIT_COLORS: return UNIT_COLORS[self.name]
        if self.base_name in UNIT_COLORS: return UNIT_COLORS[self.base_name]
        for key, color in UNIT_COLORS.items():
            if key in self.base_name or key in self.name:
                return color
        return COLORS["BLUE"] if self.faction == "PLAYER" else COLORS["RED"]

    def get_damage_modifier(self, current_time, all_units):
        mod = 1.0
        if self.alignment != "neutral":
            mod += TIME_OF_DAY[current_time][self.alignment]
            
        if not self.is_leader:
            for u in all_units:
                if u.faction == self.faction and u.is_leader:
                    if hex_distance(self.q, self.r, u.q, u.r) <= 1 and u.level >= self.level:
                        mod += 0.25
                        break
                        
        if self.is_slowed:
            mod *= 0.5
            
        return mod

    def get_defense(self, terrain_type):
        if terrain_type in self.terrain_mods:
            return self.terrain_mods[terrain_type]["def"]
        return TERRAIN_TYPES[terrain_type]["def"]

    def get_move_cost(self, terrain_type):
        if "flying" in self.abilities: return 1
        if terrain_type in self.terrain_mods:
            return self.terrain_mods[terrain_type]["cost"]
        return TERRAIN_TYPES[terrain_type]["cost"]

    def get_vision_radius(self, current_time):
        v = self.vision
        if self.alignment == "chaotic" and current_time == "Night": v += 2
        elif self.alignment == "lawful" and current_time == "Day": v += 1
        return v

    def is_visible_to(self, viewer_faction, all_units, game_map):
        if self.faction == viewer_faction: return True
        if "ambush" in self.abilities and game_map.get((self.q, self.r)) == "FOREST":
            for u in all_units:
                if u.faction == viewer_faction and hex_distance(u.q, u.r, self.q, self.r) <= 1:
                    return True
            return False
        return True

    def draw(self, screen, font, current_time, all_units):
        x, y = int(self.pixel_x), int(self.pixel_y)
        
        if self.level_up_flash > 0:
            color = COLORS["YELLOW"]
            self.level_up_flash -= 1
        elif self.damage_flash > 0:
            color = COLORS["WHITE"]
            self.damage_flash -= 1
        else:
            color = self._base_color()
        
        size = int(HEX_SIZE * 0.45)
        if self.shape == "circle":
            pygame.draw.circle(screen, color, (x, y), size)
        elif self.shape == "square":
            sq_size = size * (1.2 if "Troll" in self.base_name else 1.0)
            pygame.draw.rect(screen, color, (x-sq_size, y-sq_size, sq_size*2, sq_size*2))
        elif self.shape == "triangle":
            points = [(x, y-size), (x-size, y+size), (x+size, y+size)]
            pygame.draw.polygon(screen, color, points)
            
        if self.is_leader:
            pygame.draw.polygon(screen, COLORS["YELLOW"], [(x, y-size-11), (x-5, y-size-2), (x+5, y-size-2)])
            pygame.draw.circle(screen, COLORS["YELLOW"], (x, y - size - 6), 5, 2)
        
        ring_color = COLORS["WHITE"] if self.alignment == "lawful" else COLORS["BLACK"] if self.alignment == "chaotic" else COLORS["GREY"]
        pygame.draw.circle(screen, ring_color, (x, y), int(HEX_SIZE * 0.55), 2)
        
        if self.is_poisoned:
            pygame.draw.circle(screen, COLORS["GREEN_POISON"], (x, y), int(HEX_SIZE * 0.65), 2)
        if self.is_slowed:
            pygame.draw.circle(screen, COLORS["SLOW_BLUE"], (x, y), int(HEX_SIZE * 0.75), 2)
            
        if not self.is_leader and self.get_damage_modifier(current_time, all_units) > 1.0 and self.alignment != "neutral":
            if (TIME_OF_DAY[current_time][self.alignment] + 1.25) >= self.get_damage_modifier(current_time, all_units):
                 pygame.draw.circle(screen, COLORS["YELLOW"], (x+size, y-size), 3)
                 
        if self.heals > 0:
            pygame.draw.line(screen, COLORS["BLACK"], (x-3, y-size-5), (x+3, y-size-5), 2)
            pygame.draw.line(screen, COLORS["BLACK"], (x, y-size-8), (x, y-size-2), 2)
            
        if "flying" in self.abilities:
            pygame.draw.polygon(screen, COLORS["WHITE"], [(x-size+2, y+size-2), (x+size-2, y+size-2), (x, y+size-6)])
        elif "teleport" in self.abilities:
            pygame.draw.circle(screen, COLORS["WHITE"], (x, y+size+2), 3)
            pygame.draw.circle(screen, COLORS["WHITE"], (x-4, y+size+2), 2)
            pygame.draw.circle(screen, COLORS["WHITE"], (x+4, y+size+2), 2)
        
        bar_width = 30
        bar_x = x - bar_width//2
        bar_y = y - HEX_SIZE//2 - 8
        hp_ratio = self.hp / self.max_hp
        hp_color = COLORS["GREEN_BAR"] if hp_ratio > 0.6 else COLORS["YELLOW_BAR"] if hp_ratio > 0.3 else COLORS["RED_BAR"]
        pygame.draw.rect(screen, COLORS["BLACK"], (bar_x, bar_y, bar_width, 5))
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_width * hp_ratio), 5))
        
        pygame.draw.rect(screen, COLORS["GREY"], (bar_x, y+15, bar_width, 3))
        pygame.draw.rect(screen, COLORS["YELLOW"], (bar_x, y+15, bar_width * (self.xp/self.xp_req), 3))
        
        if self.is_selected:
            pygame.draw.circle(screen, COLORS["YELLOW"], (x, y), int(HEX_SIZE * 0.65), 3)
            
    def to_dict(self):
        return {
            "base_name": self.base_name, "name": self.name, "level": self.level, "xp": self.xp, "xp_req": self.xp_req,
            "hp": self.hp, "max_hp": self.max_hp, "q": self.q, "r": self.r, "faction": self.faction,
            "is_poisoned": self.is_poisoned, "is_slowed": self.is_slowed, "current_moves": self.current_moves, "has_acted": self.has_acted
        }

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x; self.y = y; self.text = text; self.color = color; self.life = 40
        
    def update(self):
        self.y -= 1; self.life -= 1
        
    def draw(self, screen, font):
        if self.life > 0:
            txt = font.render(self.text, True, self.color)
            txt.set_alpha(int(255 * (self.life / 40)))
            screen.blit(txt, (self.x - txt.get_width()//2, self.y))

# --- GAME ENGINE ---
class GameEngine:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Wesnoth Engine - Improved")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans,arial,helvetica", 14)
        self.font_big = pygame.font.SysFont("dejavusans,arial,helvetica", 18, bold=True)
        self._time_overlay = pygame.Surface((MAP_W, HEIGHT), pygame.SRCALPHA)
        
        self.end_turn_rect = pygame.Rect(WIDTH - 120, HEIGHT - 50, 100, 30)
        self.ai_vs_ai = False
        
        # Init state to prevent AttributeErrors if AI triggers before main loop
        self.floating_texts = []
        self.state = "WAITING_INPUT"
        self.weapon_menu = None
        self.selected_unit = None
        self.reachable_tiles = {}
        self.attack_targets = []
        self.hovered_hex = None
        self._hex_polygons = {}
        
        self.unit_templates = {
            "Knight": {"name": "Knight", "hp": 35, "attacks": [{"name":"Sword", "damage":6, "strikes":3, "range":1, "type":"Blade"}], "move": 5, "align": "lawful", "shape": "circle", "cost": 14, "mods": {"FOREST": {"cost": 3, "def": 30}, "MOUNTAIN": {"cost": 99, "def": 40}}},
            "Archer": {"name": "Archer", "hp": 25, "attacks": [{"name":"Bow", "damage":4, "strikes":3, "range":2, "type":"Pierce"}], "move": 6, "align": "lawful", "shape": "circle", "cost": 15, "mods": {"FOREST": {"cost": 1, "def": 70}}, "abilities": ["ambush"]},
            "Mage": {"name": "Mage", "hp": 20, "attacks": [{"name":"Fireball", "damage":7, "strikes":2, "range":2, "type":"Fire", "magical":True}], "move": 5, "align": "neutral", "shape": "triangle", "cost": 20},
            "White Mage": {"name": "White Mage", "hp": 24, "attacks": [{"name":"Staff", "damage":5, "strikes":2, "range":1, "type":"Impact"}, {"name":"Light", "damage":6, "strikes":2, "range":2, "type":"Arcane", "slow":True, "magical":True}], "move": 5, "align": "lawful", "shape": "triangle", "cost": 20, "heals": 4},
            "Thief": {"name": "Thief", "hp": 20, "attacks": [{"name":"Dagger", "damage":4, "strikes":3, "range":1, "type":"Pierce", "first_strike":True, "backstab":True}], "move": 6, "align": "neutral", "shape": "circle", "cost": 16, "mods": {"FOREST": {"cost": 1, "def": 60}}, "abilities": ["skirmisher", "ambush"]},
            "Shock Trooper": {"name": "Shock Trooper", "hp": 45, "attacks": [{"name":"Mace", "damage":10, "strikes":2, "range":1, "type":"Impact", "charge":True}], "move": 4, "align": "lawful", "shape": "square", "cost": 19, "res": {"Blade": 10, "Pierce": 20, "Impact": 10}},
            "Gryphon Rider": {"name": "Gryphon Rider", "hp": 35, "attacks": [{"name":"Talons", "damage":6, "strikes":3, "range":1, "type":"Blade"}], "move": 8, "align": "lawful", "shape": "triangle", "cost": 22, "abilities": ["flying", "skirmisher"]},
            "Merman Fighter": {"name": "Merman Fighter", "hp": 32, "attacks": [{"name":"Spear", "damage":5, "strikes":3, "range":1, "type":"Pierce"}], "move": 6, "align": "lawful", "shape": "circle", "cost": 18, "mods": {"SHALLOW_WATER": {"cost": 1, "def": 50}, "DEEP_WATER": {"cost": 2, "def": 40}}},
            "Berserker": {"name": "Berserker", "hp": 30, "attacks": [{"name":"Axe", "damage":5, "strikes":2, "range":1, "type":"Blade", "berserk":True}], "move": 5, "align": "neutral", "shape": "square", "cost": 19},
            "Dwarvish Guardsman": {"name": "Dwarvish Guardsman", "hp": 40, "attacks": [{"name":"Spear", "damage":4, "strikes":1, "range":1, "type":"Pierce"}], "move": 4, "align": "lawful", "shape": "square", "cost": 14, "mods": {"MOUNTAIN": {"cost": 2, "def": 50}, "FOREST": {"cost": 2, "def": 40}}, "abilities": ["steadfast"]},
            "Sorceress": {"name": "Sorceress", "hp": 24, "attacks": [{"name":"Magic Missile", "damage":6, "strikes":2, "range":2, "type":"Arcane", "magical":True}], "move": 5, "align": "neutral", "shape": "triangle", "cost": 24, "abilities": ["teleport"]},
            
            "Skeleton": {"name": "Skeleton", "hp": 30, "attacks": [{"name":"Axe", "damage":6, "strikes":2, "range":1, "type":"Blade"}], "move": 5, "align": "chaotic", "shape": "square", "cost": 12, "res": {"Blade": 50, "Pierce": 50, "Impact": -20, "Fire": -50, "Arcane": -50, "Cold": 20}, "poison_immune": True},
            "Troll": {"name": "Troll", "hp": 45, "attacks": [{"name":"Club", "damage":8, "strikes":2, "range":1, "type":"Impact"}], "move": 4, "align": "chaotic", "shape": "square", "cost": 18, "regen": 8, "res": {"Cold": -20}},
            "Ghoul": {"name": "Ghoul", "hp": 26, "attacks": [{"name":"Claws", "damage":4, "strikes":2, "range":1, "type":"Blade", "poison":True, "plague":True}], "move": 5, "align": "chaotic", "shape": "square", "cost": 14, "res": {"Blade": 0, "Pierce": 0, "Impact": 0, "Fire": 0, "Arcane": -50}, "poison_immune": True},
            "Vampire Bat": {"name": "Vampire Bat", "hp": 18, "attacks": [{"name":"Fangs", "damage":3, "strikes":3, "range":1, "type":"Pierce", "drain":True}], "move": 7, "align": "chaotic", "shape": "triangle", "cost": 15, "abilities": ["flying", "skirmisher"]},
            "Necromancer": {"name": "Necromancer", "hp": 28, "attacks": [{"name":"Shadow Wave", "damage":5, "strikes":3, "range":2, "type":"Cold", "magical":True}], "move": 5, "align": "chaotic", "shape": "triangle", "cost": 20, "res": {"Cold": 50, "Arcane": -20}},
            "Walking Corpse": {"name": "Walking Corpse", "hp": 18, "attacks": [{"name":"Touch", "damage":3, "strikes":2, "range":1, "type":"Impact", "plague":True}], "move": 4, "align": "chaotic", "shape": "square", "cost": 8, "res": {"Blade": 0, "Pierce": 0, "Impact": 0, "Fire": 0, "Arcane": -50}, "poison_immune": True}
        }
        
        self.units = []
        self.player_units = []
        self.enemy_units = []
        
        self.load_game()
        
    def add_unit(self, unit):
        self.units.append(unit)
        if unit.faction == "PLAYER":
            self.player_units.append(unit)
        else:
            self.enemy_units.append(unit)

    def remove_unit(self, unit):
        if unit in self.units: self.units.remove(unit)
        if unit in self.player_units: self.player_units.remove(unit)
        if unit in self.enemy_units: self.enemy_units.remove(unit)

    def generate_new_game(self):
        self.map, self.villages, self.keep_locations = self.generate_map()
        self._cache_hex_polygons()
        self.units = []
        self.player_units = []
        self.enemy_units = []
        
        self.add_unit(self.create_unit("General", "General", 45, [{"name":"Sword", "damage":7, "strikes":3, "range":1, "type":"Blade"}], 5, "PLAYER", 0, 0, "lawful", "square", is_leader=True))
        self.add_unit(self.create_unit("Knight", "Knight", 35, [{"name":"Sword", "damage":6, "strikes":3, "range":1, "type":"Blade"}], 5, "PLAYER", 1, 0, "lawful", "circle", terrain_mods={"FOREST": {"cost": 3, "def": 30}, "MOUNTAIN": {"cost": 99, "def": 40}}))
        self.add_unit(self.create_unit("Archer", "Archer", 25, [{"name":"Bow", "damage":4, "strikes":3, "range":2, "type":"Pierce"}], 6, "PLAYER", 0, 1, "lawful", "circle", terrain_mods={"FOREST": {"cost": 1, "def": 70}}, abilities=["ambush"]))
        self.add_unit(self.create_unit("Thief", "Thief", 20, [{"name":"Dagger", "damage":4, "strikes":3, "range":1, "type":"Pierce", "first_strike":True, "backstab":True}], 6, "PLAYER", -1, 1, "neutral", "circle", terrain_mods={"FOREST": {"cost": 1, "def": 60}}, abilities=["skirmisher", "ambush"]))
        
        self.add_unit(self.create_unit("Orc Warlord", "Orc Warlord", 50, [{"name":"Axe", "damage":8, "strikes":2, "range":1, "type":"Blade"}], 4, "ENEMY", 9, 8, "chaotic", "square", is_leader=True))
        self.add_unit(self.create_unit("Skeleton", "Skeleton", 30, [{"name":"Axe", "damage":6, "strikes":2, "range":1, "type":"Blade"}], 5, "ENEMY", 8, 9, "chaotic", "square", resistances={"Blade": 50, "Pierce": 50, "Impact": -20, "Fire": -50, "Arcane": -50, "Cold": 20}, poison_immune=True))
        self.add_unit(self.create_unit("Necromancer", "Necromancer", 28, [{"name":"Shadow Wave", "damage":5, "strikes":3, "range":2, "type":"Cold", "magical":True}], 5, "ENEMY", 9, 7, "chaotic", "triangle", resistances={"Cold": 50, "Arcane": -20}))
        self.add_unit(self.create_unit("Vampire Bat", "Vampire Bat", 18, [{"name":"Fangs", "damage":3, "strikes":3, "range":1, "type":"Pierce", "drain":True}], 7, "ENEMY", 8, 8, "chaotic", "triangle", abilities=["flying", "skirmisher"]))
        
        self.gold = {"PLAYER": 100, "ENEMY": 100}
        self.turn = "PLAYER"
        self.current_time = "Day"
        self.time_index = 0
        self.turn_count = 1
        self.game_over = False
        self.log_messages = deque(["New game started!"], maxlen=6)
        self.visible_tiles = set()
        self.explored_tiles = set()
        self.calculate_vision()
        
    def create_unit(self, base_name, name, hp, attacks, move, faction, q, r, align, shape, is_leader=False, regen=0, res=None, mods=None, heals=0, level=1, xp_req=10, abilities=None, poison_immune=False):
        return Unit(base_name, name, hp, attacks, move, faction, q, r, align, shape, is_leader=is_leader, regen=regen, resistances=res, terrain_mods=mods, heals=heals, level=level, xp_req=xp_req, abilities=abilities, poison_immune=poison_immune)

    def log(self, msg):
        self.log_messages.append(msg)

    def generate_map(self):
        game_map = {}; villages = {}; keeps = {}
        for q in range(-1, 11):
            for r in range(-1, 10):
                game_map[(q,r)] = "GRASS"
        game_map[(0,0)] = "KEEP"; keeps[(0,0)] = "PLAYER"
        for nq, nr in get_neighbors(0,0): game_map[(nq,nr)] = "CASTLE"
        game_map[(9,8)] = "KEEP"; keeps[(9,8)] = "ENEMY"
        for nq, nr in get_neighbors(9,8): game_map[(nq,nr)] = "CASTLE"
        
        for i in range(-1, 10):
            game_map[(4, i)] = "SHALLOW_WATER"
        game_map[(4, 4)] = "DEEP_WATER"
        game_map[(4, 5)] = "DEEP_WATER"
        
        for i in range(1, 4): game_map[(i, 0)] = "ROAD"
        for i in range(5, 9): game_map[(i, 8)] = "ROAD"
            
        protected = {"KEEP", "CASTLE", "ROAD", "SHALLOW_WATER", "DEEP_WATER", "VILLAGE"}
        candidates = [k for k, v in game_map.items() if v not in protected]
        for _ in range(20):
            if candidates: game_map[random.choice(candidates)] = "FOREST"
        for _ in range(10):
            if candidates: game_map[random.choice(candidates)] = "MOUNTAIN"
        for _ in range(8): 
            v = random.choice(candidates)
            if game_map[v] == "GRASS": game_map[v] = "VILLAGE"; villages[v] = "NEUTRAL"
        return game_map, villages, keeps

    def get_unit_at(self, q, r):
        for unit in self.units:
            if unit.q == q and unit.r == r: return unit
        return None

    def is_in_zoc(self, q, r, faction, unit):
        if "skirmisher" in unit.abilities or "flying" in unit.abilities: return False
        for nq, nr in get_neighbors(q, r):
            u = self.get_unit_at(nq, nr)
            if u and u.faction != faction: return True
        return False

    def _cache_hex_polygons(self):
        self._hex_polygons.clear()
        for (q, r) in self.map.keys():
            x, y = hex_to_pixel(q, r)
            self._hex_polygons[(q, r)] = [(x + vx, y + vy) for vx, vy in HEX_VERTICES]

    def draw_hex(self, q, r, color, outline=True):
        points = self._hex_polygons.get((q, r))
        if not points:
            x, y = hex_to_pixel(q, r)
            points = [(x + vx, y + vy) for vx, vy in HEX_VERTICES]
            self._hex_polygons[(q, r)] = points
        pygame.draw.polygon(self.screen, color, points)
        if outline: 
            pygame.draw.polygon(self.screen, COLORS["BLACK"], points, 1)
        if self.map.get((q,r)) == "KEEP":
            x, y = hex_to_pixel(q, r)
            pygame.draw.circle(self.screen, COLORS["BLACK"], (int(x), int(y)), 5)
            pygame.draw.circle(self.screen, COLORS["WHITE"], (int(x), int(y)), 3)

    def calculate_reachable(self, unit):
        pq = [(0, unit.q, unit.r)]; visited = set(); paths = {(unit.q, unit.r): []}
        max_moves = unit.move_range // 2 if unit.is_slowed else unit.move_range
        
        if "teleport" in unit.abilities:
            for (vq, vr), owner in self.villages.items():
                if owner == unit.faction and (vq, vr) != (unit.q, unit.r):
                    if not self.get_unit_at(vq, vr):
                        heapq.heappush(pq, (0, vq, vr))
                        paths[(vq, vr)] = [(vq, vr)] 
                        
        while pq:
            cost, q, r = heapq.heappop(pq)
            if (q, r) in visited: continue
            visited.add((q, r))
            if self.is_in_zoc(q, r, unit.faction, unit) and (q, r) != (unit.q, unit.r): continue
            if cost <= max_moves:
                for nq, nr in get_neighbors(q, r):
                    if (nq, nr) in self.map and (nq, nr) not in visited:
                        if self.get_unit_at(nq, nr): continue
                        terrain_type = self.map[(nq, nr)]
                        terrain_cost = unit.get_move_cost(terrain_type)
                        if terrain_cost < 99:
                            new_cost = cost + terrain_cost
                            if new_cost <= max_moves:
                                heapq.heappush(pq, (new_cost, nq, nr))
                                paths[(nq, nr)] = paths[(q, r)] + [(nq, nr)]
        return paths

    def calculate_attack_targets(self, unit):
        targets = []
        ranges = set([atk["range"] for atk in unit.attacks])
        for rng in ranges:
            for nq, nr in self.get_hexes_within_distance(unit.q, unit.r, rng):
                target = self.get_unit_at(nq, nr)
                if target and target.faction != unit.faction and target.is_visible_to(unit.faction, self.units, self.map):
                    targets.append(target)
        return list(set(targets))

    def get_hexes_within_distance(self, q, r, distance):
        results = []
        for dq in range(-distance, distance + 1):
            for dr in range(-distance, distance + 1):
                if abs(dq + dr) <= distance and (dq != 0 or dr != 0): results.append((q+dq, r+dr))
        return results

    def get_valid_attacks(self, attacker, defender):
        dist = hex_distance(attacker.q, attacker.r, defender.q, defender.r)
        return [atk for atk in attacker.attacks if atk["range"] >= dist]

    def calculate_vision(self):
        self.visible_tiles = set()
        for u in self.units:
            if u.faction == "PLAYER":
                v = u.get_vision_radius(self.current_time)
                for dq in range(-v, v + 1):
                    for dr in range(-v, v + 1):
                        if abs(dq + dr) <= v:
                            self.visible_tiles.add((u.q + dq, u.r + dr))
        self.explored_tiles.update(self.visible_tiles)

    def get_hit_chance(self, attacker, defender, attack):
        if attack.get("magical"): return 0.70
        ter_def = defender.get_defense(self.map[(defender.q, defender.r)])
        chance = max(0.1, 1.0 - (ter_def / 100.0))
        if attack.get("marksman"):
            chance = max(0.60, chance)
        return chance

    def is_backstab(self, attacker, defender):
        dq = attacker.q - defender.q
        dr = attacker.r - defender.r
        opp_q = defender.q - dq
        opp_r = defender.r - dr
        ally = self.get_unit_at(opp_q, opp_r)
        if ally and ally.faction == attacker.faction:
            return True
        return False

    def get_actual_damage(self, attacker, defender, attack):
        def_mod_atk = attacker.get_damage_modifier(self.current_time, self.units)
        base_dmg = max(1, int(attack["damage"] * def_mod_atk))
        resist = defender.resistances.get(attack["type"], 0)
        actual_dmg = max(1, int(base_dmg * (1 - (resist / 100.0))))
        
        if "steadfast" in defender.abilities and attack["type"] in ["Blade", "Pierce", "Impact"]:
            actual_dmg = max(1, actual_dmg // 2)
            
        if attack.get("charge"):
            actual_dmg *= 2
        if attack.get("backstab") and self.is_backstab(attacker, defender):
            actual_dmg *= 2
        return actual_dmg

    def predict_combat(self, attacker, defender, attack):
        hit_chance_atk = self.get_hit_chance(attacker, defender, attack)
        hit_chance_def = max(0.1, 1.0 - (attacker.get_defense(self.map[(attacker.q, attacker.r)]) / 100.0))
        
        atk_dmg = self.get_actual_damage(attacker, defender, attack)
        atk_max = atk_dmg * attack["strikes"]
        def_max = 0
        def_attacks = [a for a in defender.attacks if a["range"] == attack["range"]]
        if def_attacks:
            def_dmg = self.get_actual_damage(defender, attacker, def_attacks[0])
            if def_attacks[0].get("charge"): def_dmg *= 2
            if def_attacks[0].get("backstab") and self.is_backstab(defender, attacker): def_dmg *= 2
            def_max = def_dmg * def_attacks[0]["strikes"]
            
        is_berserk = attack.get("berserk", False) or (def_attacks and def_attacks[0].get("berserk", False))
        if is_berserk:
            atk_dps = atk_max * hit_chance_atk
            def_dps = def_max * hit_chance_def
            turns_to_kill_def = defender.hp / atk_dps if atk_dps > 0 else 999
            turns_to_kill_atk = attacker.hp / def_dps if def_dps > 0 else 999
            
            exp_def_hp = 0 if turns_to_kill_def <= turns_to_kill_atk else defender.hp
            exp_atk_hp = 0 if turns_to_kill_atk < turns_to_kill_def else attacker.hp
        else:
            # Proper expected damage calculation
            exp_dmg_to_def = int(atk_max * hit_chance_atk)
            exp_dmg_to_atk = int(def_max * hit_chance_def)
            
            exp_def_hp = max(0, defender.hp - exp_dmg_to_def)
            exp_atk_hp = max(0, attacker.hp - exp_dmg_to_atk)
            
        return exp_atk_hp, exp_def_hp, (0, atk_max), (0, def_max), int(hit_chance_atk*100), int(hit_chance_def*100)

    def get_attack_specs(self, atk):
        spec = []
        if atk.get("first_strike"): spec.append("First Strike")
        if atk.get("magical"): spec.append("Magical")
        if atk.get("marksman"): spec.append("Marksman")
        if atk.get("poison"): spec.append("Poison")
        if atk.get("slow"): spec.append("Slow")
        if atk.get("drain"): spec.append("Drain")
        if atk.get("plague"): spec.append("Plague")
        if atk.get("charge"): spec.append("Charge")
        if atk.get("backstab"): spec.append("Backstab")
        if atk.get("berserk"): spec.append("Berserk")
        return f" ({', '.join(spec)})" if spec else ""

    def handle_click(self, pos, button):
        if self.state != "WAITING_INPUT" or self.game_over or self.ai_vs_ai: return
        
        if button == 3: # Right click cancels
            self.weapon_menu = None
            if self.selected_unit:
                self.selected_unit.is_selected = False
                self.selected_unit = None
                self.reachable_tiles.clear()
                self.attack_targets.clear()
            return

        if self.weapon_menu:
            target, attacks, rects = self.weapon_menu
            for i, rect in enumerate(rects):
                if rect.collidepoint(pos):
                    self.initiate_combat(self.selected_unit, target, attacks[i])
                    self.weapon_menu = None
                    return
            self.weapon_menu = None
            return

        # End Turn Button
        if self.end_turn_rect.collidepoint(pos) and self.turn == "PLAYER":
            self.end_turn()
            return

        q, r = pixel_to_hex(pos[0], pos[1])
        if (q, r) not in self.map: return
        clicked_unit = self.get_unit_at(q, r)

        if self.turn == "PLAYER":
            if self.selected_unit:
                if clicked_unit in self.attack_targets:
                    valid_attacks = self.get_valid_attacks(self.selected_unit, clicked_unit)
                    if valid_attacks:
                        if len(valid_attacks) > 1:
                            menu_rects = []
                            x = min(pos[0], WIDTH - 170)
                            y = min(pos[1], HEIGHT - len(valid_attacks) * 45 - 5)
                            for i in range(len(valid_attacks)):
                                menu_rects.append(pygame.Rect(x, y + (i*45), 160, 40))
                            self.weapon_menu = (clicked_unit, valid_attacks, menu_rects)
                        else:
                            self.initiate_combat(self.selected_unit, clicked_unit, valid_attacks[0])
                    return
                if (q, r) in self.reachable_tiles and not clicked_unit:
                    path = self.reachable_tiles[(q, r)]
                    if path:
                        self.selected_unit.prev_q = self.selected_unit.q
                        self.selected_unit.prev_r = self.selected_unit.r
                        self.selected_unit.prev_pixel_x = self.selected_unit.pixel_x
                        self.selected_unit.prev_pixel_y = self.selected_unit.pixel_y
                        self.selected_unit.prev_moves = self.selected_unit.current_moves
                        self.selected_unit.prev_village_owner = self.villages.get((q, r), "NEUTRAL")
                        self.selected_unit.was_poisoned_before_move = self.selected_unit.is_poisoned
                        
                        self.selected_unit.move_path = path
                        self.selected_unit.moved_this_turn = True
                        self.state = "ANIMATING_MOVE"
                    return
                
                # Clicked on another friendly unit: switch selection
                if clicked_unit and clicked_unit.faction == "PLAYER" and (clicked_unit.current_moves > 0 or clicked_unit.is_leader) and not clicked_unit.has_acted:
                    self.selected_unit.is_selected = False
                    self.selected_unit = clicked_unit
                    self.selected_unit.is_selected = True
                    self.reachable_tiles = self.calculate_reachable(clicked_unit)
                    self.attack_targets = self.calculate_attack_targets(clicked_unit)
                    return
                
                # Clicked empty space or invalid target: deselect
                self.selected_unit.is_selected = False
                self.selected_unit = None
                self.reachable_tiles.clear()
                self.attack_targets.clear()
            else:
                if clicked_unit and clicked_unit.faction == "PLAYER" and (clicked_unit.current_moves > 0 or clicked_unit.is_leader) and not clicked_unit.has_acted:
                    self.selected_unit = clicked_unit
                    self.selected_unit.is_selected = True
                    self.reachable_tiles = self.calculate_reachable(clicked_unit)
                    self.attack_targets = self.calculate_attack_targets(clicked_unit)

    def undo_move(self):
        if self.ai_vs_ai: return
        u = self.selected_unit
        if not (u and u.moved_this_turn and not u.attacked_this_turn): return
        
        if (u.q, u.r) in self.villages:
            self.villages[(u.q, u.r)] = u.prev_village_owner
            # Restore poison state if village cured it
            if u.prev_village_owner != u.faction:
                u.is_poisoned = u.was_poisoned_before_move
                
        u.q = u.prev_q
        u.r = u.prev_r
        u.pixel_x = u.prev_pixel_x
        u.pixel_y = u.prev_pixel_y
        u.current_moves = u.prev_moves
        u.moved_this_turn = False
        self.reachable_tiles = self.calculate_reachable(u)
        self.attack_targets = self.calculate_attack_targets(u)
        self.calculate_vision()
        self.log("Move undone.")

    def select_next_unit(self):
        if self.ai_vs_ai: return
        available = [u for u in self.player_units if u.current_moves > 0 and not u.has_acted]
        if not available: return
        if self.selected_unit:
            current_idx = available.index(self.selected_unit) if self.selected_unit in available else -1
            next_idx = (current_idx + 1) % len(available)
        else:
            next_idx = 0
            
        if self.selected_unit:
            self.selected_unit.is_selected = False
        self.selected_unit = available[next_idx]
        self.selected_unit.is_selected = True
        self.reachable_tiles = self.calculate_reachable(self.selected_unit)
        self.attack_targets = self.calculate_attack_targets(self.selected_unit)

    def wait_unit(self):
        if not self.selected_unit or self.ai_vs_ai: return
        u = self.selected_unit
        if u in self.player_units:
            self.player_units.remove(u)
            self.player_units.append(u)
        u.is_selected = False
        self.selected_unit = None
        self.reachable_tiles.clear()
        self.attack_targets.clear()
        self.select_next_unit()

    def attempt_recruit(self, unit_key):
        if self.ai_vs_ai: return
        if not self.selected_unit or not self.selected_unit.is_leader: return
        leader = self.selected_unit
        if self.map[(leader.q, leader.r)] != "KEEP": return
        if leader.has_acted: 
            self.log("Leader already acted this turn.")
            return
            
        template = self.unit_templates[unit_key]
        if self.gold["PLAYER"] < template["cost"]:
            self.log("Not enough gold!")
            return
            
        # Check Dynamic Army Limit
        p_villages = list(self.villages.values()).count("PLAYER")
        max_army_size = p_villages + BASE_ARMY_BONUS
        if len(self.player_units) >= max_army_size:
            self.log(f"Army limit reached! Capture more villages. (Max: {max_army_size})")
            return

        for nq, nr in get_neighbors(leader.q, leader.r):
            if self.map.get((nq,nr)) == "CASTLE" and not self.get_unit_at(nq, nr):
                self.gold["PLAYER"] -= template["cost"]
                new_unit = self.create_unit(unit_key, template["name"], template["hp"], template["attacks"], template["move"], "PLAYER", nq, nr, template["align"], template["shape"], regen=template.get("regen", 0), res=template.get("res"), mods=template.get("mods"), heals=template.get("heals", 0), abilities=template.get("abilities"), poison_immune=template.get("poison_immune", False))
                new_unit.current_moves = 0
                new_unit.has_acted = True
                self.add_unit(new_unit)
                
                leader.current_moves = 0
                leader.has_acted = True
                leader.is_selected = False
                self.selected_unit = None
                self.reachable_tiles.clear()
                self.attack_targets.clear()
                
                self.log(f"Recruited {unit_key}!")
                self.calculate_vision()
                return
        self.log("No empty castle tiles!")

    def update_animations(self):
        if self.state != "ANIMATING_MOVE" or self.selected_unit is None:
            return
        unit = self.selected_unit
        if not unit.move_path:
            self.state = "WAITING_INPUT"
            unit.current_moves = 0
            unit.is_selected = False
            if (unit.q, unit.r) in self.villages:
                self.villages[(unit.q, unit.r)] = unit.faction
                if unit.is_poisoned:
                    unit.is_poisoned = False
                    self.log(f"{unit.name} cured at village!")
            self.selected_unit = None
            self.reachable_tiles.clear()
            self.attack_targets.clear()
            self.calculate_vision()
            return
        
        if "teleport" in unit.abilities and len(unit.move_path) == 1 and hex_distance(unit.q, unit.r, *unit.move_path[0]) > 1:
            tx, ty = hex_to_pixel(*unit.move_path[0])
            unit.pixel_x, unit.pixel_y = tx, ty
            unit.q, unit.r = unit.move_path[0]
            unit.move_path.pop(0)
            self.calculate_vision()
            return

        target_q, target_r = unit.move_path[0]
        tx, ty = hex_to_pixel(target_q, target_r)
        speed = 4.0
        dx, dy = tx - unit.pixel_x, ty - unit.pixel_y
        dist = math.hypot(dx, dy)
        if dist < speed:
            unit.pixel_x, unit.pixel_y = tx, ty
            unit.q, unit.r = target_q, target_r
            unit.move_path.pop(0)
            self.calculate_vision()
        else:
            unit.pixel_x += (dx/dist) * speed
            unit.pixel_y += (dy/dist) * speed

    def _move_ai_step(self, unit):
        if not unit.move_path:
            return False
        target_q, target_r = unit.move_path[0]
        tx, ty = hex_to_pixel(target_q, target_r)
        speed = 4.0
        dx, dy = tx - unit.pixel_x, ty - unit.pixel_y
        dist = math.hypot(dx, dy)
        if dist < speed:
            unit.pixel_x, unit.pixel_y = tx, ty
            unit.q, unit.r = target_q, target_r
            unit.move_path.pop(0)
            self.calculate_vision()
        else:
            unit.pixel_x += dx / dist * speed
            unit.pixel_y += dy / dist * speed
        return True

    def execute_strike(self, attacker, defender, attack):
        hit_chance = self.get_hit_chance(attacker, defender, attack)
        dmg = self.get_actual_damage(attacker, defender, attack)
        
        base_x, base_y = attacker.pixel_x, attacker.pixel_y
        dx = (defender.pixel_x - base_x) * 0.3
        dy = (defender.pixel_y - base_y) * 0.3
        
        for i in range(attack["strikes"]):
            if defender.hp <= 0: break
            
            for f in range(4):
                t = f / 4
                attacker.pixel_x = base_x + dx * (1 - abs(2*t - 1))
                attacker.pixel_y = base_y + dy * (1 - abs(2*t - 1))
                self.draw()
                pygame.display.flip()
                self.clock.tick(60)
                pygame.event.pump() 
            attacker.pixel_x, attacker.pixel_y = base_x, base_y
            
            if random.random() < hit_chance:
                defender.hp -= dmg
                defender.damage_flash = 5
                attacker.xp += 1
                self.floating_texts.append(FloatingText(defender.pixel_x, defender.pixel_y, f"-{dmg}", COLORS["RED"]))
                
                if attack.get("drain"):
                    heal = dmg // 2
                    attacker.hp = min(attacker.max_hp, attacker.hp + heal)
                    self.floating_texts.append(FloatingText(attacker.pixel_x, attacker.pixel_y, f"+{heal}", COLORS["GREEN_BAR"]))
            else:
                self.floating_texts.append(FloatingText(defender.pixel_x, defender.pixel_y, "Miss!", COLORS["WHITE"]))

    def initiate_combat(self, attacker, defender, attack):
        self.state = "ANIMATING_COMBAT"
        attacker.has_acted = True
        attacker.attacked_this_turn = True
        self.log(f"{attacker.name} attacks {defender.name}!")
        
        def_attack = None
        for atk in defender.attacks:
            if atk["range"] == attack["range"]:
                def_attack = atk
                break
                
        atk_first = attack.get("first_strike", False)
        def_first = def_attack.get("first_strike", False) if def_attack else False

        is_berserk = attack.get("berserk", False) or (def_attack and def_attack.get("berserk", False))
        
        if is_berserk:
            self.log("Berserk combat initiated! Fight to the death!")
            rounds = 0
            while attacker.hp > 0 and defender.hp > 0 and rounds < 30:
                if atk_first or not def_first:
                    self.execute_strike(attacker, defender, attack)
                    if defender.hp > 0 and def_attack:
                        self.execute_strike(defender, attacker, def_attack)
                else:
                    self.execute_strike(defender, attacker, def_attack)
                    if attacker.hp > 0:
                        self.execute_strike(attacker, defender, attack)
                rounds += 1
        else:
            if def_first and not atk_first:
                self.execute_strike(defender, attacker, def_attack)
                if attacker.hp > 0:
                    self.execute_strike(attacker, defender, attack)
            else:
                self.execute_strike(attacker, defender, attack)
                if defender.hp > 0 and def_attack:
                    self.execute_strike(defender, attacker, def_attack)

        if defender.hp <= 0:
            attacker.xp += 8
            self.remove_unit(defender)
            self.log(f"{defender.name} defeated!")
            
            if attack.get("plague") and defender.base_name not in CORPSE_LINE:
                corpse = self.create_unit("Walking Corpse", "Walking Corpse", 18, self.unit_templates["Walking Corpse"]["attacks"], 4, attacker.faction, defender.q, defender.r, "chaotic", "square", res={"Blade": 0, "Pierce": 0, "Impact": 0, "Fire": 0, "Arcane": -50}, poison_immune=True)
                corpse.has_acted = True
                self.add_unit(corpse)
                self.log(f"{defender.name} raised as a Walking Corpse!")
        else:
            if attack.get("poison") and not defender.is_poisoned and not defender.poison_immune:
                defender.is_poisoned = True
                self.log(f"{defender.name} poisoned!")
            elif attack.get("poison") and defender.poison_immune:
                self.log(f"{defender.name} is immune to poison!")
                
            if attack.get("slow") and not defender.is_slowed:
                defender.is_slowed = True
                self.log(f"{defender.name} slowed!")

        if attacker.hp <= 0:
            if defender in self.units:
                defender.xp += 8
            self.remove_unit(attacker)
            self.log(f"{attacker.name} defeated!")

        self.check_level_up(attacker)
        self.check_level_up(defender)

        self.state = "WAITING_INPUT"
        if self.selected_unit:
            self.selected_unit.current_moves = 0
            self.selected_unit.is_selected = False
            self.selected_unit = None
            self.reachable_tiles.clear()
            self.attack_targets.clear()
        self.check_win_condition()

    def check_level_up(self, unit):
        if unit in self.units and unit.xp >= unit.xp_req:
            advance = LEVEL_DATA.get(unit.base_name)
            if advance and advance["next"]:
                old_dmg = LEVEL_DATA[unit.base_name]["dmg"]
                new_dmg = advance["dmg"]
                ratio = new_dmg / old_dmg if old_dmg else 1.0
                for atk in unit.attacks:
                    atk["damage"] = max(1, round(atk["damage"] * ratio))
                
                unit.level += 1
                unit.base_name = advance["next"]
                unit.name = advance["next"]
                unit.max_hp = advance["hp"]
                unit.hp = unit.max_hp
                unit.xp = 0
                unit.xp_req = advance["xp_req"]
                unit.level_up_flash = 20
                self.floating_texts.append(FloatingText(unit.pixel_x, unit.pixel_y-15, "LEVEL UP!", COLORS["YELLOW"]))
            else:
                unit.xp = unit.xp_req

    def check_win_condition(self):
        if self.turn_count > MAX_TURNS:
            self.game_over = "DEFEAT (Turn Limit)"
        if not self.player_units or not any(u.is_leader for u in self.player_units): 
            self.game_over = "DEFEAT"
        elif not self.enemy_units or not any(u.is_leader for u in self.enemy_units): 
            self.game_over = "VICTORY"

    def end_turn(self):
        if self.game_over: return
        if self.turn == "PLAYER":
            self.turn = "ENEMY"
            for u in self.units:
                if u.faction == "ENEMY": 
                    u.current_moves = u.move_range
                    u.is_slowed = False
                    u.has_acted = False
                    u.moved_this_turn = False
                    u.attacked_this_turn = False
                    
                    if u.is_poisoned:
                        u.hp = max(1, u.hp - POISON_DAMAGE)
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, f"-{POISON_DAMAGE}", COLORS["GREEN_POISON"]))
                    elif u.regen > 0 and u.hp < u.max_hp:
                        u.hp = min(u.max_hp, u.hp + u.regen)
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, f"+{u.regen}", COLORS["GREEN_BAR"]))
        else:
            self.turn = "PLAYER"
            self.turn_count += 1
            for u in self.units:
                if u.faction == "PLAYER":
                    u.current_moves = u.move_range
                    u.is_slowed = False
                    u.has_acted = False
                    u.moved_this_turn = False
                    u.attacked_this_turn = False
                    
                    cured = False
                    if (u.q, u.r) in self.villages and self.villages[(u.q, u.r)] == "PLAYER":
                        cured = True
                    for ally in self.units:
                        if ally.faction == "PLAYER" and ally.heals > 0 and hex_distance(u.q, u.r, ally.q, ally.r) <= 1:
                            cured = True
                            break
                    if cured and (u.is_poisoned or u.is_slowed):
                        u.is_poisoned = False
                        u.is_slowed = False
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, "Cured!", COLORS["WHITE"]))

                    heal_amt = 0
                    if not u.has_acted and u.hp < u.max_hp:
                        heal_amt = max(heal_amt, IDLE_HEAL)
                    if (u.q, u.r) in self.villages and self.villages[(u.q, u.r)] == "PLAYER":
                        heal_amt = max(heal_amt, VILLAGE_HEAL)
                    for ally in self.units:
                        if ally.faction == "PLAYER" and ally.heals > 0 and hex_distance(u.q, u.r, ally.q, ally.r) == 1:
                            heal_amt = max(heal_amt, ally.heals)
                            
                    if heal_amt > 0 and u.hp < u.max_hp and not u.is_poisoned:
                        u.hp = min(u.max_hp, u.hp + heal_amt)
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, f"+{heal_amt}", COLORS["GREEN_BAR"]))
                        
                    if u.is_poisoned:
                        u.hp = max(1, u.hp - POISON_DAMAGE)
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, f"-{POISON_DAMAGE}", COLORS["GREEN_POISON"]))
                    elif u.regen > 0 and u.hp < u.max_hp:
                        u.hp = min(u.max_hp, u.hp + u.regen)
                        self.floating_texts.append(FloatingText(u.pixel_x, u.pixel_y, f"+{u.regen}", COLORS["GREEN_BAR"]))
                    
            p_villages = list(self.villages.values()).count("PLAYER")
            p_units = len(self.player_units)
            free_upkeep = p_villages + BASE_UPKEEP_FREE
            upkeep = max(0, p_units - free_upkeep)
            income = p_villages - upkeep
            self.gold["PLAYER"] += income
            
            e_villages = list(self.villages.values()).count("ENEMY")
            e_units = len(self.enemy_units)
            e_upkeep = max(0, e_units - (e_villages + BASE_UPKEEP_FREE))
            self.gold["ENEMY"] += (e_villages - e_upkeep)
            
            times = list(TIME_OF_DAY.keys())
            self.time_index = (self.time_index + 1) % len(times)
            self.current_time = times[self.time_index]
            self.calculate_vision()
            self.check_win_condition()

    # --- GENERALIZED AI LOGIC ---
    def evaluate_combat(self, attacker, defender, attack, exp_a, exp_d):
        """Scores an attack action. Higher is better."""
        if exp_a <= 0 and exp_d > 0: return -1000 # Suicide
        score = (defender.hp - exp_d) * 2 - (attacker.hp - exp_a)
        if exp_d <= 0: # Kill
            score += 500 + defender.level * 50
            if defender.is_leader: score += 1000
        # Target prioritization
        if "Mage" in defender.base_name or "Archer" in defender.base_name or "Necromancer" in defender.base_name:
            score += 40
        if self.is_backstab(attacker, defender): score += 60
        if attack.get("plague") and exp_d <= 0 and defender.base_name not in CORPSE_LINE: 
            score += 200
        # Ranged advantage
        if attack["range"] == 2 and not any(a["range"] >= 2 for a in defender.attacks):
            score += 50
        return score

    def evaluate_move(self, unit, tile, opp_units, leader, opp_leader):
        """Scores a movement tile when no attacks are made. Higher is better."""
        score = 0
        eq, er = unit.q, unit.r
        unit.q, unit.r = tile
        try:
            # 1. Retreat logic if wounded
            if unit.hp < unit.max_hp * 0.4:
                if tile in self.villages and self.villages[tile] == unit.faction:
                    score += 150 # Go heal at village
                elif not unit.is_leader and leader:
                    score -= hex_distance(tile[0], tile[1], leader.q, leader.r) * 10
                elif unit.is_leader:
                    # Leader retreats toward own keep / safest village
                    safe = [v for v, o in self.villages.items() if o == unit.faction]
                    if safe:
                        nearest = min(safe, key=lambda v: hex_distance(tile[0], tile[1], v[0], v[1]))
                        score -= hex_distance(tile[0], tile[1], nearest[0], nearest[1]) * 8
                return score

            # 2. Leader protection
            if leader and not unit.is_leader and opp_units:
                closest_opp_to_leader = min(opp_units, key=lambda p: hex_distance(leader.q, leader.r, p.q, p.r))
                dist_to_threat = hex_distance(tile[0], tile[1], closest_opp_to_leader.q, closest_opp_to_leader.r)
                if hex_distance(leader.q, leader.r, closest_opp_to_leader.q, closest_opp_to_leader.r) <= 3:
                    score += max(0, 5 - dist_to_threat) * 30 # Intercept
            
            # 3. Aggression / Advance
            if opp_units:
                closest_opp = min(opp_units, key=lambda p: hex_distance(tile[0], tile[1], p.q, p.r))
                score -= hex_distance(tile[0], tile[1], closest_opp.q, closest_opp.r) * 5
            
            # 4. Formation cohesion (don't wander alone)
            friends = [u for u in self.units if u != unit and u.faction == unit.faction and u.hp > u.max_hp * 0.4]
            if friends:
                closest_friend = min(friends, key=lambda f: hex_distance(tile[0], tile[1], f.q, f.r))
                dist_to_friend = hex_distance(tile[0], tile[1], closest_friend.q, closest_friend.r)
                if dist_to_friend > 3:
                    score -= (dist_to_friend - 3) * 15

            # 5. Terrain defense bonus for holding ground
            score += unit.get_defense(self.map.get(tile, "GRASS")) // 5

            # 6. Village capture/recapture
            if tile in self.villages and self.villages[tile] != unit.faction:
                score += 120 if unit.hp > unit.max_hp * 0.5 else 40
        finally:
            unit.q, unit.r = eq, er
        return score

    def run_ai(self, faction):
        opp_faction = "ENEMY" if faction == "PLAYER" else "PLAYER"
        units = self.player_units if faction == "PLAYER" else self.enemy_units
        opp_units = self.enemy_units if faction == "PLAYER" else self.player_units
        
        leader = next((u for u in units if u.is_leader), None)
        opp_leader = next((u for u in opp_units if u.is_leader), None)
        
        for unit in units[:]:
            if unit.has_acted: continue
            
            # 1. Recruitment
            if unit.is_leader and self.map[(unit.q, unit.r)] == "KEEP":
                villages_count = list(self.villages.values()).count(faction)
                max_army_size = villages_count + BASE_ARMY_BONUS
                if len(units) < max_army_size and self.gold[faction] >= 20:
                    choices = ["Knight", "Archer", "Mage", "White Mage", "Thief", "Shock Trooper"] if faction == "PLAYER" else ["Skeleton", "Troll", "Ghoul", "Vampire Bat", "Necromancer"]
                    choice = random.choice(choices)
                    cost = self.unit_templates[choice]["cost"]
                    if self.gold[faction] - cost >= 10:
                        for nq, nr in get_neighbors(unit.q, unit.r):
                            if self.map.get((nq,nr)) == "CASTLE" and not self.get_unit_at(nq, nr):
                                self.gold[faction] -= cost
                                template = self.unit_templates[choice]
                                new_unit = self.create_unit(choice, template["name"], template["hp"], template["attacks"], template["move"], faction, nq, nr, template["align"], template["shape"], regen=template.get("regen", 0), res=template.get("res"), mods=template.get("mods"), heals=template.get("heals", 0), abilities=template.get("abilities"), poison_immune=template.get("poison_immune", False))
                                new_unit.current_moves = 0
                                new_unit.has_acted = True
                                self.add_unit(new_unit)
                                self.log(f"{faction} recruited {choice}!")
                                break

            visible_targets = [u for u in opp_units if u.is_visible_to(faction, self.units, self.map)]
            if not visible_targets: 
                # No visible targets, move toward opponent's general starting area
                visible_targets = opp_units 
                if not visible_targets: continue
            
            paths = self.calculate_reachable(unit)
            best_action = None # (score, type, data)
            
            # 2. Evaluate Move-Then-Attack options
            orig_q, orig_r = unit.q, unit.r
            for tile, path in paths.items():
                unit.q, unit.r = tile
                targets = self.calculate_attack_targets(unit)
                for t in targets:
                    for atk in self.get_valid_attacks(unit, t):
                        exp_a, exp_d, *_ = self.predict_combat(unit, t, atk)
                        score = self.evaluate_combat(unit, t, atk, exp_a, exp_d)
                        # Slight penalty for moving before attacking (exposes unit)
                        if tile != (orig_q, orig_r): score -= 5 
                        if best_action is None or score > best_action[0]:
                            best_action = (score, "attack", (path, t, atk))
            unit.q, unit.r = orig_q, orig_r
            
            # 3. Execute Best Attack
            if best_action and best_action[0] > 0:
                path, t, atk = best_action[2]
                if path:
                    unit.move_path = path
                    while unit.move_path:
                        self._move_ai_step(unit)
                        self.draw(); pygame.display.flip(); self.clock.tick(FPS); pygame.event.pump()
                    pygame.time.delay(150)
                self.initiate_combat(unit, t, atk)
                pygame.time.delay(300) 
                continue
                
            # 4. Evaluate Pure Movement (if no good attacks)
            best_tile = max(paths.keys(), key=lambda tile: self.evaluate_move(unit, tile, visible_targets, leader, opp_leader))
            
            if best_tile != (unit.q, unit.r):
                unit.move_path = paths[best_tile]
                while unit.move_path:
                    self._move_ai_step(unit)
                    self.draw(); pygame.display.flip(); self.clock.tick(FPS); pygame.event.pump()
                pygame.time.delay(150)
            
            unit.has_acted = True
            
        self.end_turn()

    def save_game(self):
        data = {
            "version": 1,
            "map": self.map, "villages": self.villages, "keeps": self.keep_locations,
            "units": [u.to_dict() for u in self.units], "gold": self.gold,
            "turn": self.turn, "time_index": self.time_index, "turn_count": self.turn_count
        }
        # Atomic save to prevent corruption
        with open("savegame.tmp", "w") as f:
            json.dump(data, f)
        os.replace("savegame.tmp", "savegame.json")
        self.log("Game Saved!")

    def load_game(self):
        if not os.path.exists("savegame.json"):
            self.generate_new_game()
            return
            
        with open("savegame.json", "r") as f:
            data = json.load(f)
            
        self.map = {tuple(k): v for k, v in data["map"].items()}
        self._cache_hex_polygons()
        self.villages = {tuple(k): v for k, v in data["villages"].items()}
        self.keep_locations = {tuple(k): v for k, v in data["keeps"].items()}
        self.gold = data["gold"]
        self.turn = data["turn"]
        self.time_index = data["time_index"]
        self.turn_count = data["turn_count"]
        self.current_time = list(TIME_OF_DAY.keys())[self.time_index]
        
        self.units = []
        self.player_units = []
        self.enemy_units = []
        for u_data in data["units"]:
            base = u_data["base_name"]
            template = self.unit_templates.get(base)
            if base in ["General", "Orc Warlord"]:
                if base == "General":
                    template = {"name": "General", "hp": 45, "attacks": [{"name":"Sword", "damage":7, "strikes":3, "range":1, "type":"Blade"}], "move": 5, "align": "lawful", "shape": "square"}
                else:
                    template = {"name": "Orc Warlord", "hp": 50, "attacks": [{"name":"Axe", "damage":8, "strikes":2, "range":1, "type":"Blade"}], "move": 4, "align": "chaotic", "shape": "square"}
            if template:
                unit = self.create_unit(base, u_data["name"], u_data["max_hp"], template["attacks"], template["move"], u_data["faction"], u_data["q"], u_data["r"], template["align"], template["shape"], is_leader=(base in ["General", "Orc Warlord"]), regen=template.get("regen", 0), res=template.get("res"), mods=template.get("mods"), heals=template.get("heals", 0), level=u_data["level"], xp_req=u_data["xp_req"], abilities=template.get("abilities"), poison_immune=template.get("poison_immune", False))
                unit.hp = u_data["hp"]
                unit.xp = u_data["xp"]
                unit.is_poisoned = u_data["is_poisoned"]
                unit.is_slowed = u_data["is_slowed"]
                unit.current_moves = u_data["current_moves"]
                unit.has_acted = u_data.get("has_acted", False)
                self.add_unit(unit)
                
        self.game_over = False
        self.state = "WAITING_INPUT"
        self.log_messages = deque(["Game Loaded!"], maxlen=6)
        self.visible_tiles = set()
        self.explored_tiles = set()
        self.calculate_vision()

    def draw_ui(self):
        pygame.draw.rect(self.screen, COLORS["PANEL"], (MAP_W, 0, SIDEBAR_W, HEIGHT))
        time_text = self.font_big.render(f"Time: {self.current_time} (Turn: {self.turn_count}/{MAX_TURNS})", True, COLORS["WHITE"])
        self.screen.blit(time_text, (MAP_W + 10, 10))
        
        p_villages = list(self.villages.values()).count("PLAYER")
        p_units = len(self.player_units)
        free_upkeep = p_villages + BASE_UPKEEP_FREE
        upkeep = max(0, p_units - free_upkeep)
        income = p_villages - upkeep
        
        gold_text = self.font.render(f"Gold: {self.gold['PLAYER']} (Income: {income:+d})", True, COLORS["YELLOW"])
        self.screen.blit(gold_text, (MAP_W + 10, 35))
        
        up_color = COLORS["GREEN_BAR"] if upkeep == 0 else COLORS["RED_BAR"]
        army_text = self.font.render(f"Army: {p_units} (Upkeep: {upkeep}g)", True, up_color)
        self.screen.blit(army_text, (MAP_W + 10, 55))
        
        ai_color = COLORS["YELLOW"] if self.ai_vs_ai else COLORS["GREY"]
        ai_text = self.font.render(f"AI Control: {'ON' if self.ai_vs_ai else 'OFF'}", True, ai_color)
        self.screen.blit(ai_text, (MAP_W + 200, 55))
        
        tod = TIME_OF_DAY[self.current_time]
        tod_text = self.font.render(f"Lawful: {tod['lawful']:+.0%}  Chaotic: {tod['chaotic']:+.0%}", True, COLORS["WHITE"])
        self.screen.blit(tod_text, (MAP_W + 10, 75))
        
        if self.hovered_hex and self.hovered_hex in self.map:
            q, r = self.hovered_hex
            terrain = self.map[self.hovered_hex]
            info = TERRAIN_TYPES[terrain]
            text = self.font_big.render(f"Terrain: {terrain}", True, COLORS["WHITE"])
            self.screen.blit(text, (MAP_W + 10, 100))
            
            # Dynamic hover stats based on selected unit
            if self.selected_unit:
                move_cost = self.selected_unit.get_move_cost(terrain)
                def_val = self.selected_unit.get_defense(terrain)
                text = self.font.render(f"Unit Cost: {move_cost} | Unit Def: {def_val}%", True, COLORS["WHITE"])
            else:
                text = self.font.render(f"Base Move Cost: {info['cost']} | Base Defense: {info['def']}%", True, COLORS["WHITE"])
            self.screen.blit(text, (MAP_W + 10, 125))
            
            unit = self.get_unit_at(q, r)
            if unit:
                text = self.font_big.render(f"{unit.name} (Lvl {unit.level})", True, COLORS["WHITE"])
                self.screen.blit(text, (MAP_W + 10, 155))
                status = "POISONED" if unit.is_poisoned else "Healthy"
                if unit.is_slowed: status += ", SLOWED"
                if unit.regen > 0: status += f", Regen {unit.regen}"
                if unit.heals > 0: status += f", Heals {unit.heals}"
                text = self.font.render(f"HP: {unit.hp}/{unit.max_hp} | XP: {unit.xp}/{unit.xp_req} | {status}", True, COLORS["WHITE"])
                self.screen.blit(text, (MAP_W + 10, 180))
                text = self.font.render(f"Alignment: {unit.alignment}", True, COLORS["WHITE"])
                self.screen.blit(text, (MAP_W + 10, 200))
                res_str = "Res: " + " ".join([f"{k[:2]}:{v}%" for k, v in unit.resistances.items()]) if unit.resistances else "Res: None"
                text = self.font.render(res_str, True, COLORS["WHITE"])
                self.screen.blit(text, (MAP_W + 10, 220))
                ab_str = "Abilities: " + ", ".join(unit.abilities) if unit.abilities else "Abilities: None"
                text = self.font.render(ab_str, True, COLORS["WHITE"])
                self.screen.blit(text, (MAP_W + 10, 240))
                for i, atk in enumerate(unit.attacks):
                    spec_str = self.get_attack_specs(atk)
                    text = self.font.render(f"Atk: {atk['name']} ({atk['damage']}x{atk['strikes']}, Rng:{atk['range']}, {atk['type']}){spec_str}", True, COLORS["WHITE"])
                    self.screen.blit(text, (MAP_W + 10, 260 + (i*20)))

            if self.selected_unit and unit and unit.faction != self.selected_unit.faction:
                valid_attacks = self.get_valid_attacks(self.selected_unit, unit)
                if valid_attacks:
                    atk = valid_attacks[0]
                    exp_atk_hp, exp_def_hp, atk_range, def_range, atk_hit, def_hit = self.predict_combat(self.selected_unit, unit, atk)
                    pygame.draw.rect(self.screen, COLORS["BLACK"], (MAP_W + 10, 340, 330, 80))
                    pygame.draw.rect(self.screen, COLORS["WHITE"], (MAP_W + 10, 340, 330, 80), 1)
                    txt = self.font_big.render("Combat Prediction", True, COLORS["YELLOW"])
                    self.screen.blit(txt, (MAP_W + 20, 345))
                    txt = self.font.render(f"{self.selected_unit.name} HP: {self.selected_unit.hp} -> {exp_atk_hp} ({atk_hit}% hit, Takes {def_range[0]}-{def_range[1]})", True, COLORS["WHITE"])
                    self.screen.blit(txt, (MAP_W + 20, 370))
                    txt = self.font.render(f"{unit.name} HP: {unit.hp} -> {exp_def_hp} ({def_hit}% hit, Takes {atk_range[0]}-{atk_range[1]})", True, COLORS["WHITE"])
                    self.screen.blit(txt, (MAP_W + 20, 390))

        if self.selected_unit and self.selected_unit.is_leader and self.map[(self.selected_unit.q, self.selected_unit.r)] == "KEEP":
            pygame.draw.rect(self.screen, COLORS["BLACK"], (MAP_W + 10, 430, 330, 140))
            pygame.draw.rect(self.screen, COLORS["YELLOW"], (MAP_W + 10, 430, 330, 140), 1)
            txt = self.font_big.render("Recruitment (Keep)", True, COLORS["YELLOW"])
            self.screen.blit(txt, (MAP_W + 20, 435))
            txt = self.font.render("[1] Knight (14g)   [2] Archer (15g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 460))
            txt = self.font.render("[3] Mage (20g)     [4] White Mage (20g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 480))
            txt = self.font.render("[5] Thief (16g)    [6] Shock Trooper (19g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 500))
            txt = self.font.render("[7] Gryphon Rider (22g) [8] Merman (18g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 520))
            txt = self.font.render("[9] Berserker (19g) [0] Guardsman (14g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 540))
            txt = self.font.render("[O] Sorceress (24g)", True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 560))

        pygame.draw.rect(self.screen, COLORS["BLACK"], (MAP_W + 10, 580, 330, 40))
        pygame.draw.rect(self.screen, COLORS["WHITE"], (MAP_W + 10, 580, 330, 40), 1)
        txt = self.font_big.render("Log", True, COLORS["WHITE"])
        self.screen.blit(txt, (MAP_W + 20, 585))
        for i, msg in enumerate(list(self.log_messages)[-2:]):
            txt = self.font.render(msg, True, COLORS["WHITE"])
            self.screen.blit(txt, (MAP_W + 20, 605 + (i*12)))

        # End Turn Button
        pygame.draw.rect(self.screen, COLORS["LIGHT_BLUE"], self.end_turn_rect, border_radius=5)
        txt = self.font_big.render("End Turn", True, COLORS["BLACK"])
        self.screen.blit(txt, (self.end_turn_rect.x + 10, self.end_turn_rect.y + 5))
        
        inst = "LMB: Move/Menu | RMB: Cancel | U: Undo | TAB: Next | W: Wait | A: AI Toggle | F5/F9"
        text = self.font.render(inst, True, COLORS["WHITE"])
        self.screen.blit(text, (MAP_W + 10, HEIGHT - 20))
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0,0))
            txt = self.font_big.render(self.game_over, True, COLORS["YELLOW"])
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))
            txt = self.font.render("Press R to Restart", True, COLORS["WHITE"])
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 + 10))

    def draw_path_preview(self):
        if self.selected_unit and self.hovered_hex in self.reachable_tiles:
            path = self.reachable_tiles[self.hovered_hex]
            if path:
                if "teleport" in self.selected_unit.abilities and len(path) == 1 and hex_distance(self.selected_unit.q, self.selected_unit.r, path[0][0], path[0][1]) > 1:
                    px, py = hex_to_pixel(*path[-1])
                    pygame.draw.circle(self.screen, COLORS["YELLOW"], (int(px), int(py)), 10, 2)
                    pygame.draw.line(self.screen, COLORS["YELLOW"], (self.selected_unit.pixel_x, self.selected_unit.pixel_y), (px, py), 1)
                else:
                    pygame.draw.line(self.screen, COLORS["YELLOW"], (self.selected_unit.pixel_x, self.selected_unit.pixel_y), hex_to_pixel(*path[0]), 2)
                    for i in range(len(path)-1):
                        p1 = hex_to_pixel(*path[i])
                        p2 = hex_to_pixel(*path[i+1])
                        pygame.draw.line(self.screen, COLORS["YELLOW"], p1, p2, 2)
                    px, py = hex_to_pixel(*path[-1])
                    pygame.draw.circle(self.screen, COLORS["YELLOW"], (int(px), int(py)), 5, 1)
                
    def draw_weapon_menu(self):
        if not self.weapon_menu: return
        target, attacks, rects = self.weapon_menu
        for i, rect in enumerate(rects):
            pygame.draw.rect(self.screen, COLORS["BLACK"], rect)
            pygame.draw.rect(self.screen, COLORS["YELLOW"], rect, 1)
            atk = attacks[i]
            dmg = self.get_actual_damage(self.selected_unit, target, atk)
            hit = self.get_hit_chance(self.selected_unit, target, atk) * 100
            
            spec_str = self.get_attack_specs(atk)
            txt1 = self.font.render(f"{atk['name']} ({atk['damage']}x{atk['strikes']}, {atk['type']}){spec_str}", True, COLORS["WHITE"])
            txt2 = self.font.render(f"Dmg: {dmg} per strike | Hit: {int(hit)}%", True, COLORS["YELLOW"])
            self.screen.blit(txt1, (rect.x + 5, rect.y + 5))
            self.screen.blit(txt2, (rect.x + 5, rect.y + 22))

    def draw(self):
        self.screen.fill(COLORS["BLACK"])
        for (q, r), terrain in self.map.items():
            is_visible = (q, r) in self.visible_tiles
            is_explored = (q, r) in self.explored_tiles
            if not is_explored: continue
            color = TERRAIN_TYPES[terrain]["color"]
            if terrain == "VILLAGE":
                owner = self.villages.get((q,r), "NEUTRAL")
                color = COLORS["VILLAGE_P"] if owner == "PLAYER" else COLORS["VILLAGE_E"] if owner == "ENEMY" else COLORS["VILLAGE_N"]
            if not is_visible: color = tuple(c * 0.3 for c in color)
            self.draw_hex(q, r, color)
            
        if self.selected_unit:
            for rq, rr in self.reachable_tiles.keys():
                self.draw_hex(rq, rr, COLORS["LIGHT_BLUE"], outline=False)
            for target in self.attack_targets:
                self.draw_hex(target.q, target.r, COLORS["PINK"], outline=False)
            self.draw_path_preview()

        if self.hovered_hex and self.hovered_hex in self.map and self.hovered_hex in self.visible_tiles:
            self.draw_hex(self.hovered_hex[0], self.hovered_hex[1], COLORS["YELLOW"], outline=False)

        for unit in self.units:
            if unit.faction == "PLAYER" or (unit.q, unit.r) in self.visible_tiles:
                if unit.is_visible_to("PLAYER", self.units, self.map):
                    unit.draw(self.screen, self.font, self.current_time, self.units)
            
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font)
            
        self._time_overlay.fill(TIME_OF_DAY[self.current_time]["color"])
        self.screen.blit(self._time_overlay, (0,0))
        
        # Turn Indicator
        turn_color = COLORS["BLUE"] if self.turn == "PLAYER" else COLORS["RED"]
        turn_txt = self.font_big.render(f"{self.turn} TURN", True, turn_color)
        self.screen.blit(turn_txt, (MAP_W//2 - turn_txt.get_width()//2, 10))

        self.draw_ui()
        self.draw_weapon_menu()

    def run(self):
        self.state = "WAITING_INPUT"
        running = True
        while running:
            self.hovered_hex = pixel_to_hex(*pygame.mouse.get_pos())
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    self.handle_click(event.pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        if os.path.exists("savegame.json"): os.remove("savegame.json")
                        self.generate_new_game()
                        self.state = "WAITING_INPUT"
                    elif event.key == pygame.K_a:
                        self.ai_vs_ai = not self.ai_vs_ai
                        self.log(f"AI vs AI mode: {'ON' if self.ai_vs_ai else 'OFF'}")
                        if self.selected_unit:
                            self.selected_unit.is_selected = False
                            self.selected_unit = None
                            self.reachable_tiles.clear()
                            self.attack_targets.clear()
                    elif not self.game_over:
                        if event.key == pygame.K_SPACE and self.turn == "PLAYER" and self.state == "WAITING_INPUT" and not self.ai_vs_ai:
                            self.end_turn()
                        elif event.key == pygame.K_u: self.undo_move()
                        elif event.key == pygame.K_TAB: self.select_next_unit()
                        elif event.key == pygame.K_w and self.selected_unit:
                            self.wait_unit()
                        elif event.key == pygame.K_1: self.attempt_recruit("Knight")
                        elif event.key == pygame.K_2: self.attempt_recruit("Archer")
                        elif event.key == pygame.K_3: self.attempt_recruit("Mage")
                        elif event.key == pygame.K_4: self.attempt_recruit("White Mage")
                        elif event.key == pygame.K_5: self.attempt_recruit("Thief")
                        elif event.key == pygame.K_6: self.attempt_recruit("Shock Trooper")
                        elif event.key == pygame.K_7: self.attempt_recruit("Gryphon Rider")
                        elif event.key == pygame.K_8: self.attempt_recruit("Merman Fighter")
                        elif event.key == pygame.K_9: self.attempt_recruit("Berserker")
                        elif event.key == pygame.K_0: self.attempt_recruit("Dwarvish Guardsman")
                        elif event.key == pygame.K_o: self.attempt_recruit("Sorceress")
                        elif event.key == pygame.K_F5: self.save_game()
                        elif event.key == pygame.K_F9: self.load_game()

            for ft in self.floating_texts[:]:
                ft.update()
                if ft.life <= 0: self.floating_texts.remove(ft)

            self.update_animations()
            
            # Run AI if it's their turn, or if AI vs AI mode is active
            if self.state == "WAITING_INPUT" and not self.game_over:
                if self.turn == "ENEMY":
                    self.run_ai("ENEMY")
                elif self.turn == "PLAYER" and self.ai_vs_ai:
                    self.run_ai("PLAYER")
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    engine = GameEngine()
    engine.run()