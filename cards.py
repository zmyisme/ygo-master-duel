# -*- coding: utf-8 -*-
"""
娓告垙鐜嬪ぇ甯堝喅鏂?- 鍗＄墝鏁版嵁搴?涓诲崱缁?+ 棰濆鍗＄粍 鍏?10+寮犲崱鐗?"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Tuple
import random

class CardType(Enum):
    MONSTER = "鎬吔"
    SPELL = "榄旀硶"
    TRAP = "闄烽槺"

class MonsterType(Enum):
    NORMAL = "閫氬父"
    EFFECT = "鏁堟灉"
    TUNER = "璋冩暣"
    FUSION = "铻嶅悎"
    SYNCHRO = "鍚岃皟"
    XYZ = "瓒呴噺"

class Attribute(Enum):
    DARK = "鏆?
    LIGHT = "鍏?
    FIRE = "鐐?
    WATER = "姘?
    WIND = "椋?
    EARTH = "鍦?
    DIVINE = "绁?

class SpellType(Enum):
    NORMAL = "閫氬父"
    QUICK = "閫熸敾"
    CONTINUOUS = "姘哥画"
    EQUIP = "瑁呭"
    FIELD = "鍦哄湴"

class TrapType(Enum):
    NORMAL = "閫氬父"
    COUNTER = "鍙嶅嚮"
    CONTINUOUS = "姘哥画"

class Position(Enum):
    ATTACK = "鏀诲嚮琛ㄧず"
    DEFENSE = "瀹堝琛ㄧず"
    FACE_DOWN_DEFENSE = "閲屼晶瀹堝琛ㄧず"

@dataclass
class Card:
    id: int
    name: str
    card_type: CardType
    description: str
    # 鎬吔灞炴€?    level: int = 0          # 绛夌骇锛堣秴閲忔€吔姝ゅ€间负0锛屼娇鐢╮ank锛?    rank: int = 0           # 闃剁骇锛堜粎瓒呴噺锛?    atk: int = 0
    defense: int = 0
    attribute: Optional[Attribute] = None
    monster_type: Optional[MonsterType] = None
    is_tuner: bool = False  # 鏄惁璋冩暣锛堢敤浜庡悓璋冿級
    # 榄旀硶/闄烽槺灞炴€?    spell_type: Optional[SpellType] = None
    trap_type: Optional[TrapType] = None
    # 棰濆鍙敜绱犳潗
    materials: str = ""     # 鍙敜绱犳潗鎻忚堪
    # 鏁堟灉
    effect: Optional[Callable] = None
    effect_args: Dict[str, Any] = field(default_factory=dict)
    # 瓒呴噺绱犳潗
    xyz_materials: List['Card'] = field(default_factory=list)

    def __hash__(self):
        return self.id
    def __eq__(self, other):
        return isinstance(other, Card) and self.id == other.id
    def copy(self):
        import copy
        return copy.deepcopy(self)
    @property
    def is_extra_deck(self) -> bool:
        return self.monster_type in (MonsterType.FUSION, MonsterType.SYNCHRO, MonsterType.XYZ)
    @property
    def stars(self) -> int:
        return self.rank if self.rank > 0 else self.level

# ==================== 鏁堟灉鍑芥暟宸ュ巶 ====================
def damage_effect(amount: int):
    def effect(gs, player, target, card):
        opponent = gs.get_opponent(player)
        opponent.lp -= amount
        gs.log(f"銆恵card.name}銆戠粰浜堝鎵?{amount} 浼ゅ锛?)
        return True
    return effect

def heal_effect(amount: int):
    def effect(gs, player, target, card):
        player.lp = min(8000, player.lp + amount)
        gs.log(f"銆恵card.name}銆戞仮澶?{amount} LP锛?)
        return True
    return effect

def draw_effect(amount: int):
    def effect(gs, player, target, card):
        for _ in range(amount):
            player.draw()
        gs.log(f"銆恵card.name}銆戞娊 {amount} 寮犲崱锛?)
        return True
    return effect

def destroy_monster_effect(count: int = 1):
    def effect(gs, player, target, card):
        opponent = gs.get_opponent(player)
        destroyed = 0
        for _ in range(count):
            if opponent.field.monster_zone:
                # 浼樺厛鐮村潖鏀诲嚮鍔涙渶楂樼殑
                idx = max(range(len(opponent.field.monster_zone)), 
                         key=lambda i: opponent.field.monster_zone[i].atk)
                m = opponent.field.monster_zone.pop(idx)
                opponent.graveyard.append(m)
                gs.log(f"銆恵card.name}銆戠牬鍧忎簡銆恵m.name}銆戯紒")
                destroyed += 1
        return destroyed > 0
    return effect

def buff_effect(atk: int, defense: int = 0):
    def effect(gs, player, target, card):
        if target is not None and target < len(player.field.monster_zone):
            m = player.field.monster_zone[target]
            m.atk += atk
            m.defense += defense
            gs.log(f"銆恵card.name}銆戙€恵m.name}銆戞敾+{atk} 瀹?{defense}")
            return True
        return False
    return effect

def search_effect(card_name_keyword: str):
    def effect(gs, player, target, card):
        for c in player.deck:
            if card_name_keyword in c.name:
                player.deck.remove(c)
                player.hand.append(c)
                gs.log(f"銆恵card.name}銆戝皢銆恵c.name}銆戝姞鍏ユ墜鐗岋紒")
                return True
        gs.log(f"銆恵card.name}銆戞绱㈠け璐ワ紝鍗＄粍娌℃湁绗﹀悎鏉′欢鐨勫崱")
        return False
    return effect

def special_summon_from_deck(level_limit: int = 4):
    def effect(gs, player, target, card):
        candidates = [c for c in player.deck if c.card_type == CardType.MONSTER 
                      and c.level <= level_limit and not c.is_extra_deck]
        if candidates:
            c = random.choice(candidates)
            player.deck.remove(c)
            if player.field.can_summon_monster():
                player.field.monster_zone.append(c)
                gs.log(f"銆恵card.name}銆戠壒娈婂彫鍞ゃ€恵c.name}銆戯紒")
                return True
            else:
                player.graveyard.append(c)
                gs.log(f"銆恵card.name}銆戠壒娈婂彫鍞ゅけ璐ワ紝鎬吔鍖哄凡婊?)
                return False
        return False
    return effect

def destroy_spell_trap_effect(count: int = 1):
    def effect(gs, player, target, card):
        opponent = gs.get_opponent(player)
        destroyed = 0
        for _ in range(count):
            if opponent.field.spell_trap_zone:
                idx = 0
                st = opponent.field.spell_trap_zone.pop(idx)
                opponent.graveyard.append(st["card"])
                gs.log(f"銆恵card.name}銆戠牬鍧忎簡瀵规墜鐨勩€恵st['card'].name}銆戯紒")
                destroyed += 1
        return destroyed > 0
    return effect

def negate_attack_effect():
    def effect(gs, player, target, card):
        gs.pending_attack = None
        gs.log(f"銆恵card.name}銆戞敾鍑绘棤鏁堝寲锛?)
        return True
    return effect

def half_damage_effect():
    def effect(gs, player, target, card):
        gs.damage_multiplier = 0.5
        gs.log(f"銆恵card.name}銆戞湰鍥炲悎鍙楀埌鐨勪激瀹冲噺鍗婏紒")
        return True
    return effect

# ==================== 涓诲崱缁勬€吔锛?0寮狅級 ====================
def create_main_monsters():
    cards = []
    # 閫氬父鎬吔锛?0寮狅級
    normals = [
        (1, "闈掔溂鐧介緳", 8, 3000, 2500, Attribute.LIGHT, "浠ラ珮鏀诲嚮鍔涜憲绉扮殑浼犺涔嬮緳"),
        (2, "榛戦瓟瀵?, 7, 2500, 2100, Attribute.DARK, "榄旀硶浣夸腑鐨勯瓟娉曚娇"),
        (3, "鐪熺孩鐪奸粦榫?, 7, 2400, 2000, Attribute.DARK, "鎷ユ湁鐪熺孩涔嬬溂鐨勯粦榫?),
        (4, "璇呭拻涔嬮緳", 5, 2000, 1500, Attribute.DARK, "琚瘏鍜掔殑閭緳"),
        (5, "鏆楅粦楠戝＋鐩栦簹", 7, 2300, 2100, Attribute.WIND, "楠戠潃鐤鹃涔嬮┈鐨勯獞澹?),
        (6, "绮剧伒鍓戝＋", 4, 1400, 1200, Attribute.EARTH, "绮鹃€氬墤鏈殑绮剧伒"),
        (7, "鑽掗噹涔嬬嫾", 3, 1200, 800, Attribute.EARTH, "鑽掗噹涓殑瀛ょ嫾"),
        (8, "娴锋槦灏忓瓙", 2, 600, 700, Attribute.WATER, "娴疯竟鐨勫彲鐖辩敓鐗?),
        (9, "鐏劙骞界伒", 3, 1000, 800, Attribute.FIRE, "鐕冪儳鐨勭伒榄?),
        (10, "宀╃煶宸ㄥ叺", 3, 1300, 1400, Attribute.EARTH, "瀹堟姢灞卞渤鐨勫法浜?),
    ]
    for m in normals:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=MonsterType.NORMAL))

    # 鏁堟灉鎬吔锛?0寮狅級
    effects = [
        (11, "鏆楅亾鍖栧笀褰煎緱", 3, 600, 1500, Attribute.DARK, "缈昏浆锛氭娊1寮犲崱", draw_effect(1), MonsterType.EFFECT),
        (12, "鍦ｇ簿鐏?, 3, 800, 2000, Attribute.LIGHT, "缈昏浆锛氭仮澶?000LP", heal_effect(1000), MonsterType.EFFECT),
        (13, "榄斿鎴樺＋鐮村潖鑰?, 4, 1600, 1000, Attribute.DARK, "鍙敜鎴愬姛鏃讹細鐮村潖1寮犻瓟闄?, destroy_spell_trap_effect(1), MonsterType.EFFECT),
        (14, "娣锋矊鎴樺＋", 8, 3000, 2500, Attribute.EARTH, "鍙敜鎴愬姛鏃讹細鐮村潖瀵规墜1鍙€吔", destroy_monster_effect(1), MonsterType.EFFECT),
        (15, "鐢靛瓙榫?, 5, 2100, 1600, Attribute.LIGHT, "瀵规墜鍦轰笂鏈夋€吔鏃跺彲鐩存帴鏀诲嚮", damage_effect(0), MonsterType.EFFECT),
        (16, "妫夎姳绯?, 3, 300, 500, Attribute.LIGHT, "閲屼晶琛ㄧず鏃朵笉浼氳鎴樻枟鐮村潖", None, MonsterType.EFFECT),
        (17, "鍓婇瓊姝荤伒", 3, 200, 200, Attribute.DARK, "鐩存帴鏀诲嚮鎴愬姛鏃跺鎵嬮殢鏈轰涪1鎵嬬墝", None, MonsterType.EFFECT),
        (18, "绁炲湥榄旀湳甯?, 1, 300, 400, Attribute.LIGHT, "缈昏浆锛氫粠澧撳湴鍥炴敹1寮犻瓟娉曞崱", draw_effect(1), MonsterType.EFFECT),
        (19, "寮傛鍏冩垬澹?, 4, 1200, 1000, Attribute.EARTH, "鎴樻枟鐮村潖瀵规墜鎬吔鏃堕櫎澶栭偅鍙€吔", None, MonsterType.EFFECT),
        (20, "绾界壒", 4, 1900, 400, Attribute.DARK, "鍙敜鎴愬姛鏃讹細瀵规墜鍙楀埌500浼ゅ", damage_effect(500), MonsterType.EFFECT),
        (21, "娴佹皳浣ｅ叺閮ㄩ槦", 4, 1000, 1000, Attribute.EARTH, "瑙ｆ斁姝ゅ崱锛氱牬鍧忓鎵?鍙€吔", destroy_monster_effect(1), MonsterType.EFFECT),
        (22, "鍝ュ竷鏋楃獊鍑婚儴闃?, 4, 2300, 0, Attribute.EARTH, "鏀诲嚮琛ㄧず鏃舵敾鍑诲姏涓婂崌", buff_effect(300), MonsterType.EFFECT),
        (23, "杩呮嵎榧紶", 2, 1000, 100, Attribute.EARTH, "琚垬鏂楃牬鍧忔椂锛氭仮澶?000LP", heal_effect(1000), MonsterType.EFFECT),
        (24, "鏆椾箣鍋囬潰", 2, 900, 400, Attribute.DARK, "缈昏浆锛氫粠澧撳湴鐩栨斁1寮犻櫡闃?, None, MonsterType.EFFECT),
        (25, "鍏変箣鍋囬潰", 2, 1000, 1000, Attribute.LIGHT, "缈昏浆锛氫粠澧撳湴鐩栨斁1寮犻瓟娉?, None, MonsterType.EFFECT),
        (26, "涓夌溂鎬?, 3, 450, 600, Attribute.DARK, "浠庡崱缁勫姞鍏?鍙?500鏀讳互涓嬬殑鎬吔鍒版墜鐗?, search_effect(""), MonsterType.EFFECT),
        (27, "榛戞．鏋楀コ宸?, 4, 1100, 1200, Attribute.DARK, "浠庡崱缁勫姞鍏?鍙?500瀹堜互涓嬬殑鎬吔鍒版墜鐗?, search_effect(""), MonsterType.EFFECT),
        (28, "鏉€鎵嬬暘鑼?, 4, 1400, 1100, Attribute.DARK, "琚牬鍧忔椂锛氫粠鍗＄粍鐗规畩鍙敜1鍙殫灞炴€ф€吔", special_summon_from_deck(4), MonsterType.EFFECT),
        (29, "娣辨笂鏆楁潃鑰?, 4, 1200, 1000, Attribute.DARK, "浠庡鍦伴櫎澶栵細鐮村潖瀵规墜1鍙€吔", destroy_monster_effect(1), MonsterType.EFFECT),
        (30, "鍗＄墖闃插崼澹?, 3, 0, 2000, Attribute.EARTH, "鍙敜鎴愬姛鏃讹細鍗＄粍鏈€涓婃柟3寮犲崱閫佸叆澧撳湴", draw_effect(0), MonsterType.EFFECT),
    ]
    for m in effects:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=m[8], effect=m[7]))

    # 璋冩暣鎬吔锛?0寮狅級- 鐢ㄤ簬鍚岃皟鍙敜
    tuners = [
        (31, "搴熷搧鍚岃皟澹?, 3, 900, 600, Attribute.EARTH, "璋冩暣锛氬彫鍞ゆ垚鍔熸椂鐗规畩鍙敜1鍙?鏄熶互涓嬫€吔", special_summon_from_deck(2), True),
        (32, "閫熸敾鍚岃皟澹?, 5, 700, 1400, Attribute.WIND, "璋冩暣锛氬彲灏?鍙€吔浣滀负绁搧浠庢墜鐗岀壒娈婂彫鍞ゆ鍗?, None, True),
        (33, "鏁堟灉閬挋鑰?, 1, 0, 0, Attribute.LIGHT, "璋冩暣锛氳В鏀炬鍗★紝鏃犳晥瀵规墜1鍙€吔鏁堟灉", None, True),
        (34, "骞诲吔鏈虹寧鎴峰骇", 2, 600, 1000, Attribute.WIND, "璋冩暣锛氭鍗′綔涓哄悓璋冪礌鏉愭椂锛屼粠鍗＄粍鐗规畩鍙敜1鍙够鍏芥満", special_summon_from_deck(3), True),
        (35, "鍍靛案甯﹁弻鑰?, 2, 400, 200, Attribute.DARK, "璋冩暣锛?鍥炲悎1娆★紝灏嗗崱缁勬渶涓婃柟鍗￠€佸叆澧撳湴锛屾鍗′粠澧撳湴鐗规畩鍙敜", None, True),
        (36, "鍠锋皵鍚岃皟澹?, 1, 500, 0, Attribute.FIRE, "璋冩暣锛氭鍗′綔涓哄悓璋冪礌鏉愰€佸鏃舵娊1寮犲崱", draw_effect(1), True),
        (37, "鐏版祦涓?, 3, 0, 1800, Attribute.FIRE, "璋冩暣锛氬鎵嬪彂鍔ㄦ晥鏋滄椂锛屼涪寮冩鍗′娇鍏舵棤鏁?, None, True),
        (38, "骞介鍏?, 3, 0, 1800, Attribute.FIRE, "璋冩暣锛氬満涓婂崱鏁堟灉鍙戝姩鏃讹紝涓㈠純姝ゅ崱鐮村潖閭ｅ紶鍗?, destroy_spell_trap_effect(1), True),
        (39, "閾舵渤榄斿甯?, 4, 0, 1800, Attribute.LIGHT, "璋冩暣锛氬瑷€1涓崱鍚嶏紝浠庡崱缁勫姞鍏ユ墜鐗?, search_effect("閾舵渤"), True),
        (40, "鍏遍福铏?, 3, 800, 700, Attribute.EARTH, "璋冩暣锛氫綔涓哄悓璋冪礌鏉愭椂锛屼粠鍗＄粍鍔犲叆1鍙皟鏁村埌鎵嬬墝", search_effect("璋冩暣"), True),
    ]
    for m in tuners:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=MonsterType.TUNER, is_tuner=True, effect=m[7]))
    return cards

# ==================== 榄旀硶鍗★紙25寮狅級 ====================
def create_spells():
    cards = []
    spells = [
        # 閫氬父榄旀硶
        (51, "姝昏€呰嫃鐢?, "閫氬父锛氫互鑷繁鎴栧鎵嬪鍦?鍙€吔涓哄璞″彂鍔紝閭ｅ彧鎬吔鍦ㄨ嚜宸卞満涓婄壒娈婂彫鍞?, None, SpellType.NORMAL),
        (52, "寮烘涔嬪６", "閫氬父锛氳嚜宸变粠鍗＄粍鎶?寮?, draw_effect(2), SpellType.NORMAL),
        (53, "澶ч鏆?, "閫氬父锛氬満涓婃墍鏈夐瓟娉暵烽櫡闃卞崱鐮村潖", destroy_spell_trap_effect(5), SpellType.NORMAL),
        (54, "榛戞礊", "閫氬父锛氬満涓婃墍鏈夋€吔鐮村潖", destroy_monster_effect(5), SpellType.NORMAL),
        (55, "闆峰嚮", "閫氬父锛氬鎵嬪満涓?鍙€吔鐮村潖", destroy_monster_effect(1), SpellType.NORMAL),
        (56, "缇芥瘺鎵?, "閫氬父锛氬鎵嬪満涓婃墍鏈夐瓟娉暵烽櫡闃卞崱鐮村潖", destroy_spell_trap_effect(5), SpellType.NORMAL),
        (57, "澶╀娇鐨勬柦鑸?, "閫氬父锛氭娊3寮犲崱锛岀劧鍚庝涪寮?寮犳墜鐗?, draw_effect(3), SpellType.NORMAL),
        (58, "榄備箣瑙ｆ斁", "閫氬父锛氬弻鏂瑰鍦扮殑鍗″悎璁℃渶澶?寮犱粠娓告垙涓櫎澶?, None, SpellType.NORMAL),
        (59, "铻嶅悎", "閫氬父锛氫粠鎵嬬墝路鍦轰笂灏嗚瀺鍚堢礌鏉愭€吔閫佸幓澧撳湴锛岃瀺鍚堝彫鍞?鍙瀺鍚堟€吔", None, SpellType.NORMAL),
        (60, "铻嶅悎鍥炴敹", "閫氬父锛氫粠澧撳湴鍥炴敹1寮犮€岃瀺鍚堛€嶅拰1鍙瀺鍚堢礌鏉愭€吔鍔犲叆鎵嬬墝", draw_effect(2), SpellType.NORMAL),
        (61, "姝昏€呰浆鐢?, "閫氬父锛氫涪寮?寮犳墜鐗岋紝浠ヨ嚜宸卞鍦?鍙€吔涓哄璞″姞鍏ユ墜鐗?, search_effect(""), SpellType.NORMAL),
        (62, "鎶典环璐墿", "閫氬父锛氫涪寮?鍙?鏄熸€吔锛屾娊2寮犲崱", draw_effect(2), SpellType.NORMAL),
        # 閫熸敾榄旀硶
        (63, "鏃嬮", "閫熸敾锛氬満涓?寮犻瓟娉暵烽櫡闃卞崱鐮村潖", destroy_spell_trap_effect(1), SpellType.QUICK),
        (64, "鏁屼汉鎿嶇旱鍣?, "閫熸敾锛氬彉鏇村鎵?鍙€吔琛ㄧず褰㈠紡鎴栨帶鍒舵潈", None, SpellType.QUICK),
        (65, "绂佸繉鐨勫湥鏋?, "閫熸敾锛氬満涓?鍙€吔鏀诲嚮鍔涗笅闄?00锛屼笉鍙楀叾浠栭瓟娉暵烽櫡闃辨晥鏋滃奖鍝?, buff_effect(-800), SpellType.QUICK),
        (66, "鏈堜箣涔?, "閫熸敾锛氬満涓?鍙€吔鍙樻垚閲屼晶瀹堝琛ㄧず", None, SpellType.QUICK),
        (67, "绐佽繘", "閫熸敾锛氬満涓?鍙€吔鏀诲嚮鍔涗笂鍗?00", buff_effect(700), SpellType.QUICK),
        (68, "鏁屼汉鎺у埗鍣?, "閫熸敾锛氬鎵?鍙€吔杩欏洖鍚堜笉鑳芥敾鍑?, None, SpellType.QUICK),
        # 瑁呭榄旀硶
        (69, "鍥㈢粨涔嬪姏", "瑁呭锛氳澶囨€吔鏀诲嚮鍔涗笂鍗囪嚜宸卞満涓婅〃渚ц〃绀烘€吔鏁伴噺脳800", buff_effect(800), SpellType.EQUIP),
        (70, "榄斿甯堜箣鍔?, "瑁呭锛氳澶囨€吔鏀诲嚮鍔浡峰畧澶囧姏涓婂崌鍦轰笂榄旈櫡鏁伴噺脳500", buff_effect(500, 500), SpellType.EQUIP),
        (71, "闂數涔嬪墤", "瑁呭锛氳澶囨€吔鏀诲嚮鍔涗笂鍗?00锛屽畧澶囧姏涓嬮檷400", buff_effect(800, -400), SpellType.EQUIP),
        # 姘哥画榄旀硶
        (72, "姘哥画榄旀硶A", "姘哥画锛氳嚜宸卞満涓婃€吔鏀诲嚮鍔涗笂鍗?00", buff_effect(300), SpellType.CONTINUOUS),
        (73, "姘哥画榄旀硶B", "姘哥画锛氭瘡娆¤嚜宸卞彫鍞ゆ€吔鎶?寮犲崱", draw_effect(1), SpellType.CONTINUOUS),
        # 鍦哄湴榄旀硶
        (74, "姝昏€呬箣璋?, "鍦哄湴锛氬弻鏂瑰鍦扮殑鎬吔涓嶄細琚晥鏋滈櫎澶?, None, SpellType.FIELD),
        (75, "鎽╁ぉ妤?, "鍦哄湴锛氳嚜宸辨垬澹棌鎬吔鏀诲嚮鏀诲嚮鍔涙洿楂樼殑鎬吔鏃讹紝鏀诲嚮鍔涗笂鍗?000", buff_effect(1000), SpellType.FIELD),
        (76, "鏆?, "鍦哄湴锛氬満涓婃殫灞炴€ф€吔鏀诲嚮鍔涗笂鍗?00", buff_effect(500), SpellType.FIELD),
        (77, "鍏変箣缁撶晫", "鍦哄湴锛氬満涓婂厜灞炴€ф€吔鏀诲嚮鍔涗笂鍗?00锛屽畧澶囧姏涓嬮檷400", buff_effect(500, -400), SpellType.FIELD),
    ]
    for s in spells:
        cards.append(Card(id=s[0], name=s[1], card_type=CardType.SPELL, description=s[2],
                         spell_type=s[4], effect=s[3]))
    return cards

# ==================== 闄烽槺鍗★紙20寮狅級 ====================
def create_traps():
    cards = []
    traps = [
        # 閫氬父闄烽槺
        (81, "绁炲湥闃叉姢缃?鍙嶅皠闀滃姏-", "閫氬父锛氬鎵嬫€吔鏀诲嚮瀹ｈ█鏃讹紝鐮村潖瀵规墜鎵€鏈夋敾鍑昏〃绀烘€吔", destroy_monster_effect(5), TrapType.NORMAL),
        (82, "榄旀硶绛?, "閫氬父锛氬鎵嬫€吔鏀诲嚮瀹ｈ█鏃讹紝缁欏鎵嬮€犳垚閭ｅ彧鎬吔鏀诲嚮鍔涙暟鍊肩殑浼ゅ", damage_effect(1000), TrapType.NORMAL),
        (83, "钀界┐", "閫氬父锛氬鎵嬪彫鍞ぢ峰弽杞彫鍞ぢ风壒娈婂彫鍞ゆ€吔鎴愬姛鏃讹紝鏀诲嚮鍔?000浠ヤ笂鎬吔鐮村潖", destroy_monster_effect(1), TrapType.NORMAL),
        (84, "婵€娴佽懍", "閫氬父锛氭€吔鍙敜路鍙嶈浆鍙敜路鐗规畩鍙敜鏃讹紝鍦轰笂鎵€鏈夋€吔鐮村潖", destroy_monster_effect(5), TrapType.NORMAL),
        (85, "娆″厓骞介棴", "閫氬父锛氬鎵嬫€吔鏀诲嚮瀹ｈ█鏃讹紝閭ｅ彧鎬吔浠庢父鎴忎腑闄ゅ", destroy_monster_effect(1), TrapType.NORMAL),
        (86, "鐮村潖杞?, "閫氬父锛氬満涓?鍙€吔鐮村潖锛屽弻鏂瑰彈鍒伴偅鍙€吔鏀诲嚮鍔涙暟鍊肩殑浼ゅ", damage_effect(1000), TrapType.NORMAL),
        (87, "涓囪兘鍦伴浄", "閫氬父锛氬鎵嬫€吔鏀诲嚮瀹ｈ█鏃讹紝鐮村潖鏀诲嚮鍔涙渶楂樼殑鏀诲嚮鎬吔", destroy_monster_effect(1), TrapType.NORMAL),
        (88, "浜氱┖闂寸墿璐ㄤ紶閫佽缃?, "閫氬父锛氳嚜宸卞満涓?鍙€吔闄ゅ锛岀粨鏉熼樁娈垫椂鍥炲埌鍦轰笂", None, TrapType.NORMAL),
        (89, "浣姩浣滄垬", "閫氬父锛氬鎵嬫€吔鐩存帴鏀诲嚮鏃讹紝閭ｆ鎴樻枟浼ゅ鍙樹负0", half_damage_effect(), TrapType.NORMAL),
        (90, "鐩楀鑰?, "閫氬父锛氬鎵嬪鍦?寮犻瓟娉曞崱鍙戝姩锛岄偅寮犲崱鏁堟灉閫傜敤鍚庝粠娓告垙涓櫎澶?, draw_effect(1), TrapType.NORMAL),
        # 姘哥画闄烽槺
        (91, "鎶€鑳芥娊鍙?, "姘哥画锛氬満涓婃墍鏈夎〃渚ц〃绀烘€吔鏁堟灉鏃犳晥鍖?, None, TrapType.CONTINUOUS),
        (92, "鐜嬪鐨勯€氬憡", "姘哥画锛氬満涓婃墍鏈夐櫡闃卞崱鏁堟灉鏃犳晥鍖?, None, TrapType.CONTINUOUS),
        (93, "鐜嬪鐨勫脊鍘?, "姘哥画锛氭€吔鐗规畩鍙敜鏃讹紝鏀粯800LP浣垮叾鏃犳晥骞剁牬鍧?, destroy_monster_effect(1), TrapType.CONTINUOUS),
        (94, "鍙敜闄愬埗鍣?, "姘哥画锛氬弻鏂?鍥炲悎鍙兘鍙敜路鐗规畩鍙敜鍚堣1娆?, None, TrapType.CONTINUOUS),
        (95, "榄斾箣鍗＄粍鐮村潖鐥呮瘨", "姘哥画锛氳В鏀?鍙殫灞炴€ф敾鍑诲姏1500浠ヤ笅鐨勬€吔锛岀‘璁ゅ鎵嬫墜鐗屄峰崱缁勭牬鍧忔敾鍑诲姏1500浠ヤ笂鐨勬€吔", destroy_monster_effect(3), TrapType.CONTINUOUS),
        # 鍙嶅嚮闄烽槺
        (96, "绁炰箣瀹ｅ憡", "鍙嶅嚮锛氭€吔鍙敜路榄旀硶路闄烽槺鍙戝姩鏃犳晥骞剁牬鍧忥紝鏀粯涓€鍗奓P", destroy_monster_effect(1), TrapType.COUNTER),
        (97, "绁炰箣璀﹀憡", "鍙嶅嚮锛氭€吔鍙敜路鐗规畩鍙敜路榄旀硶路闄烽槺鍙戝姩鏃犳晥骞剁牬鍧忥紝鏀粯2000LP", destroy_monster_effect(1), TrapType.COUNTER),
        (98, "鐩楄醇鐨勪竷閬撳叿", "鍙嶅嚮锛氶櫡闃卞崱鍙戝姩鏃犳晥骞剁牬鍧忥紝鏀粯1000LP", destroy_spell_trap_effect(1), TrapType.COUNTER),
        (99, "鏀诲嚮鏃犲姏鍖?, "鍙嶅嚮锛氭€吔鏀诲嚮鏃犳晥锛岀粨鏉熸垬鏂楅樁娈?, negate_attack_effect(), TrapType.COUNTER),
        (100, "榄旀硶骞叉壈闃?, "鍙嶅嚮锛氶瓟娉曞崱鍙戝姩鏃犳晥骞剁牬鍧忥紝涓㈠純1寮犳墜鐗?, destroy_spell_trap_effect(1), TrapType.COUNTER),
    ]
    for t in traps:
        cards.append(Card(id=t[0], name=t[1], card_type=CardType.TRAP, description=t[2],
                         trap_type=t[4], effect=t[3]))
    return cards

# ==================== 棰濆鍗＄粍鎬吔锛?0寮狅級 ====================
def create_extra_deck():
    cards = []

    # 铻嶅悎鎬吔锛?5寮狅級
    fusions = [
        (101, "闈掔溂绌舵瀬榫?, 12, 4500, 3800, Attribute.LIGHT, "铻嶅悎锛氶潚鐪肩櫧榫櫭?", "闈掔溂鐧介緳+闈掔溂鐧介緳+闈掔溂鐧介緳", MonsterType.FUSION),
        (102, "榛戦瓟瀵奸獞澹?, 9, 2500, 2100, Attribute.DARK, "铻嶅悎锛氶粦榄斿+鎴樺＋鏃忔€吔", "榛戦瓟瀵?鎴樺＋鏃?, MonsterType.FUSION),
        (103, "榫欓獞澹洊浜?, 7, 2600, 2100, Attribute.WIND, "铻嶅悎锛氭殫榛戦獞澹洊浜?璇呭拻涔嬮緳", "鏆楅粦楠戝＋鐩栦簹+璇呭拻涔嬮緳", MonsterType.FUSION),
        (104, "鍙屽ご闆烽緳", 8, 2800, 2100, Attribute.LIGHT, "铻嶅悎锛氶浄榫櫭?", "闆烽緳+闆烽緳", MonsterType.FUSION),
        (105, "鍗冨勾榫?, 7, 2400, 2000, Attribute.WIND, "铻嶅悎锛氭椂闂撮瓟鏈笀+瀹濊礉榫?, "鏃堕棿榄旀湳甯?瀹濊礉榫?, MonsterType.FUSION),
        (106, "娣锋矊鎴樺＋", 8, 3000, 2500, Attribute.EARTH, "铻嶅悎锛氭殫榛戦獞澹洊浜?璇呭拻涔嬮緳", "鏆楅粦楠戝＋鐩栦簹+璇呭拻涔嬮緳", MonsterType.FUSION),
        (107, "姝讳骸鎭堕瓟榫?, 6, 2000, 1200, Attribute.DARK, "铻嶅悎锛氭伓榄斿彫鍞?灏忛緳", "鎭堕瓟鍙敜+灏忛緳", MonsterType.FUSION),
        (108, "娴佹槦榛戦緳", 8, 3500, 2000, Attribute.DARK, "铻嶅悎锛氱湡绾㈢溂榛戦緳+娴佹槦涔嬮緳", "鐪熺孩鐪奸粦榫?娴佹槦涔嬮緳", MonsterType.FUSION),
        (109, "鐢靛瓙缁堢粨榫?, 10, 4000, 2800, Attribute.LIGHT, "铻嶅悎锛氱數瀛愰緳脳3", "鐢靛瓙榫?鐢靛瓙榫?鐢靛瓙榫?, MonsterType.FUSION),
        (110, "浜斿笣榫?, 12, 5000, 5000, Attribute.DARK, "铻嶅悎锛氶緳鏃忔€吔脳5", "榫欐棌+榫欐棌+榫欐棌+榫欐棌+榫欐棌", MonsterType.FUSION),
        (111, "宓屽悎瑕佸榫?, 8, 0, 0, Attribute.DARK, "铻嶅悎锛氱數瀛愰緳+鏈烘鏃忔€吔", "鐢靛瓙榫?鏈烘鏃?, MonsterType.FUSION),
        (112, "铏瑰厜鏂板畤渚?, 10, 4500, 3000, Attribute.LIGHT, "铻嶅悎锛氬厓绱犺嫳闆勬柊瀹囦緺+浠绘剰鑻遍泟", "鏂板畤渚?鑻遍泟", MonsterType.FUSION),
        (113, "瀹濈煶楠戝＋路鐝嶇彔", 4, 2600, 1900, Attribute.EARTH, "铻嶅悎锛氬疂鐭抽獞澹€吔脳2", "瀹濈煶楠戝＋+瀹濈煶楠戝＋", MonsterType.FUSION),
        (114, "鏃х鍔尐", 4, 2500, 1200, Attribute.EARTH, "铻嶅悎锛氬悓璋冩€吔+瓒呴噺鎬吔", "鍚岃皟+瓒呴噺", MonsterType.FUSION),
        (115, "褰变緷路绫冲痉鎷変粈", 5, 2200, 800, Attribute.DARK, "铻嶅悎锛氬奖渚濇€吔+鏆楀睘鎬ф€吔", "褰变緷+鏆楀睘鎬?, MonsterType.FUSION),
    ]
    for m in fusions:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=m[8], materials=m[7]))

    # 鍚岃皟鎬吔锛?5寮狅級
    synchros = [
        (121, "搴熷搧鎴樺＋", 5, 2300, 1300, Attribute.DARK, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (122, "鏄熷皹榫?, 8, 2500, 2000, Attribute.WIND, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (123, "绾㈣幉榄旈緳", 8, 3000, 2000, Attribute.DARK, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (124, "榛戣敺钖囬緳", 7, 2400, 1800, Attribute.FIRE, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (125, "鍙や唬濡栫簿榫?, 7, 2100, 3000, Attribute.LIGHT, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (126, "鍔ㄥ姏宸ュ叿榫?, 7, 2300, 2500, Attribute.EARTH, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (127, "姘礌鎴樺＋", 7, 2800, 1800, Attribute.FIRE, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (128, "鍠烽湠铏?, 6, 2400, 1200, Attribute.WIND, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (129, "鍐扮粨鐣屼箣榫欏厜鏋緳", 6, 2300, 1400, Attribute.WATER, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (130, "姝ｄ箟鐩熷啗鐏句骸铏?, 5, 2200, 1200, Attribute.DARK, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (131, "姝﹀櫒娲?, 4, 1800, 800, Attribute.EARTH, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (132, "绉戞妧灞炶秴鍥句功棣嗗憳", 5, 2400, 1800, Attribute.DARK, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙互涓?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (133, "鏂圭▼寮忓悓璋冨＋", 2, 900, 300, Attribute.LIGHT, "鍚岃皟锛氳皟鏁?璋冩暣浠ュ鐨勬€吔1鍙?, "璋冩暣+闈炶皟鏁?, MonsterType.SYNCHRO),
        (134, "娴佸ぉ绫绘槦榫?, 12, 4000, 4000, Attribute.LIGHT, "鍚岃皟锛氳皟鏁?鍙?璋冩暣浠ュ鐨勬€吔1鍙?, "璋冩暣2+闈炶皟鏁?, MonsterType.SYNCHRO),
        (135, "瀹囧畽鑰€鍙橀緳", 12, 4000, 4000, Attribute.WIND, "鍚岃皟锛氳皟鏁?鍙?璋冩暣浠ュ鐨勬€吔1鍙?, "璋冩暣2+闈炶皟鏁?, MonsterType.SYNCHRO),
    ]
    for m in synchros:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=m[8], materials=m[7]))

    # 瓒呴噺鎬吔锛?0寮狅級
    xyzs = [
        (141, "No.39 甯屾湜鐨囬湇鏅?, 4, 2500, 2000, Attribute.LIGHT, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (142, "No.34 鐢电畻鏈哄吔澶瓧鑺?, 3, 0, 2900, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "3鏄熋?", MonsterType.XYZ),
        (143, "No.17 娴锋伓榫?, 3, 2000, 0, Attribute.WATER, "瓒呴噺锛?鏄熸€吔脳2", "3鏄熋?", MonsterType.XYZ),
        (144, "No.50 榛戠帀绫冲彿", 4, 2100, 1500, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (145, "鐔斿博璋烽攣閾鹃緳", 4, 2500, 1200, Attribute.FIRE, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (146, "鍙戞潯鏈洪浄鍙戞潯闆?, 4, 2500, 1500, Attribute.WIND, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (147, "鑻辫豹鍐犲啗鏂挗鍓戠帇", 4, 2500, 1600, Attribute.EARTH, "瓒呴噺锛?鏄熸垬澹棌鎬吔脳2", "4鏄熸垬澹?", MonsterType.XYZ),
        (148, "濮嬬瀹堟姢鑰呮彁鎷夋柉", 5, 2600, 1700, Attribute.LIGHT, "瓒呴噺锛?鏄熸€吔脳2", "5鏄熋?", MonsterType.XYZ),
        (149, "鐏北鎭愰緳", 5, 2500, 1800, Attribute.FIRE, "瓒呴噺锛?鏄熸€吔脳2", "5鏄熋?", MonsterType.XYZ),
        (150, "No.61 鐏北鎭愰緳", 5, 2500, 1800, Attribute.FIRE, "瓒呴噺锛?鏄熸€吔脳2", "5鏄熋?", MonsterType.XYZ),
        (151, "鏄熷湥娆х背浼芥槦浜?, 4, 2400, 1900, Attribute.LIGHT, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (152, "榄斿涔﹀＋宸寸壒灏?, 2, 1000, 1000, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "2鏄熋?", MonsterType.XYZ),
        (153, "楝艰鏃犲ご楠戝＋", 1, 1000, 1000, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "1鏄熋?", MonsterType.XYZ),
        (154, "鍔辫緣澹叆榄旇潎鐜?, 4, 1900, 300, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (155, "楦熼摮澹崱鏂嘲灏?, 4, 2000, 1500, Attribute.WIND, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (156, "娣辨笂鐨勬綔浼忚€?, 4, 1700, 1400, Attribute.WATER, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (157, "闂厜No.39 甯屾湜鐨囬湇鏅风數鍏夌殗", 5, 2500, 2000, Attribute.LIGHT, "瓒呴噺锛?鏄熸€吔脳3", "5鏄熋?", MonsterType.XYZ),
        (158, "No.101 瀵傞潤鑽ｈ獕鏂硅垷楠戝＋", 4, 2100, 1000, Attribute.WATER, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (159, "鏆楀彌閫嗚秴閲忛緳", 4, 2500, 2000, Attribute.DARK, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
        (160, "甯屾湜鐨囬湇鏅锋簮鏈?, 4, 3000, 2500, Attribute.LIGHT, "瓒呴噺锛?鏄熸€吔脳2", "4鏄熋?", MonsterType.XYZ),
    ]
    for m in xyzs:
        cards.append(Card(id=m[0], name=m[1], card_type=CardType.MONSTER, description=m[6],
                         level=0, rank=m[2], atk=m[3], defense=m[4], attribute=m[5],
                         monster_type=m[8], materials=m[7]))
    return cards

# ==================== 鏁版嵁搴撶鐞?====================
ALL_CARDS: List[Card] = []
EXTRA_CARDS: List[Card] = []

def init_database():
    global ALL_CARDS, EXTRA_CARDS
    if not ALL_CARDS:
        main = create_main_monsters() + create_spells() + create_traps()
        extra = create_extra_deck()
        ALL_CARDS = main + extra
        EXTRA_CARDS = extra
    return ALL_CARDS

def get_all_cards() -> List[Card]:
    init_database()
    return [c.copy() for c in ALL_CARDS]

def get_main_deck_cards() -> List[Card]:
    init_database()
    return [c.copy() for c in ALL_CARDS if not c.is_extra_deck]

def get_extra_deck_cards() -> List[Card]:
    init_database()
    return [c.copy() for c in EXTRA_CARDS]

def get_card_by_id(cid: int) -> Optional[Card]:
    init_database()
    for c in ALL_CARDS:
        if c.id == cid:
            return c.copy()
    return None

def add_custom_card(card: Card):
    """鍚庢湡娣诲姞鏂板崱鎺ュ彛"""
    ALL_CARDS.append(card)
    if card.is_extra_deck:
        EXTRA_CARDS.append(card)
