# -*- coding: utf-8 -*-
"""
娓告垙鐜嬪ぇ甯堝喅鏂?- 鏍稿績瑙勫垯寮曟搸
"""
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import random
from cards import (Card, CardType, MonsterType, SpellType, TrapType, Position,
                   Attribute, init_database, get_card_by_id, get_all_cards)

class Phase(Enum):
    DRAW = "鎶藉崱闃舵"
    STANDBY = "鍑嗗闃舵"
    MAIN1 = "涓昏闃舵1"
    BATTLE = "鎴樻枟闃舵"
    MAIN2 = "涓昏闃舵2"
    END = "缁撴潫闃舵"

class GameResult(Enum):
    ONGOING = "杩涜涓?
    PLAYER1_WIN = "鐜╁1鑳滃埄"
    PLAYER2_WIN = "鐜╁2鑳滃埄"
    DRAW = "骞冲眬"

@dataclass
class Field:
    """鍦哄湴 - 娓告垙鐜嬪ぇ甯堣鍒?020鍦哄湴"""
    monster_zone: List[Dict[str, Any]] = field(default_factory=list)      # 涓绘€吔鍖?5鏍硷紝dict鍚玞ard鍜宲osition
    spell_trap_zone: List[Dict[str, Any]] = field(default_factory=list)   # 榄旈櫡鍖?5鏍?    field_zone: Optional[Dict[str, Any]] = None                           # 鍦哄湴榄旀硶鍖?    extra_monster_zone: List[Dict[str, Any]] = field(default_factory=list) # 棰濆鎬吔鍖?2鏍硷紙鍏辩敤锛?
    def get_monster_count(self) -> int:
        return len(self.monster_zone)

    def get_st_count(self) -> int:
        return len(self.spell_trap_zone)

    def can_summon_monster(self) -> bool:
        return len(self.monster_zone) < 5

    def can_place_st(self) -> bool:
        return len(self.spell_trap_zone) < 5

    def can_use_emz(self) -> bool:
        return len(self.extra_monster_zone) < 2

    def get_monster_at(self, idx: int) -> Optional[Dict[str, Any]]:
        if 0 <= idx < len(self.monster_zone):
            return self.monster_zone[idx]
        return None

    def remove_monster(self, idx: int) -> Optional[Card]:
        if 0 <= idx < len(self.monster_zone):
            return self.monster_zone.pop(idx)["card"]
        return None

@dataclass
class Player:
    """鐜╁"""
    name: str
    lp: int = 8000
    deck: List[Card] = field(default_factory=list)
    extra_deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    graveyard: List[Card] = field(default_factory=list)
    banished: List[Card] = field(default_factory=list)
    field: Field = field(default_factory=Field)
    has_normal_summoned: bool = False
    has_normal_set: bool = False
    can_still_summon: bool = True  # 閫氬彫鏉冿紙閫氬父鍙敜鎴栫洊鏀惧悎璁?娆★級

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def draw(self) -> Optional[Card]:
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None

    def draw_initial(self, count: int = 5):
        for _ in range(count):
            self.draw()

    def can_normal_summon(self, card: Card) -> Tuple[bool, str]:
        if card.card_type != CardType.MONSTER:
            return False, "涓嶆槸鎬吔鍗?
        if card.is_extra_deck:
            return False, "棰濆鍗＄粍鎬吔涓嶈兘閫氬父鍙敜"
        if not self.field.can_summon_monster():
            return False, "涓绘€吔鍖哄凡婊?
        if not self.can_still_summon:
            return False, "鏈洖鍚堝凡閫氬父鍙敜/鐩栨斁"
        # 绁搧璁＄畻
        required = 0
        if card.level >= 5 and card.level <= 6:
            required = 1
        elif card.level >= 7:
            required = 2
        available = len(self.field.monster_zone)
        if available < required:
            return False, f"闇€瑕?{required} 鍙€吔浣滀负绁搧"
        return True, "鍙互鍙敜"

    def normal_summon(self, card: Card, hand_index: int, position: Position = Position.ATTACK) -> bool:
        can, msg = self.can_normal_summon(card)
        if not can:
            return False

        self.hand.pop(hand_index)

        # 澶勭悊绁搧
        required = 0
        if card.level >= 5 and card.level <= 6:
            required = 1
        elif card.level >= 7:
            required = 2

        for _ in range(required):
            if self.field.monster_zone:
                tribute = self.field.monster_zone.pop(0)
                self.graveyard.append(tribute["card"])

        self.field.monster_zone.append({"card": card, "position": position, "can_attack": False if position != Position.ATTACK else True})
        self.can_still_summon = False
        return True

    def normal_set(self, card: Card, hand_index: int) -> bool:
        if card.card_type != CardType.MONSTER or card.is_extra_deck:
            return False
        if not self.field.can_summon_monster() or not self.can_still_summon:
            return False
        self.hand.pop(hand_index)
        self.field.monster_zone.append({"card": card, "position": Position.FACE_DOWN_DEFENSE, "can_attack": False})
        self.can_still_summon = False
        return True

    def special_summon(self, card: Card, from_extra: bool = False, use_emz: bool = False) -> bool:
        """鐗规畩鍙敜锛堣瀺鍚?鍚岃皟/瓒呴噺绛夛級"""
        if from_extra and card.is_extra_deck:
            # 浼樺厛鏀句富鎬吔鍖猴紝婊′簡鏀鹃澶栨€吔鍖?            if self.field.can_summon_monster() and not use_emz:
                self.field.monster_zone.append({"card": card, "position": Position.ATTACK, "can_attack": True})
                return True
            elif self.field.can_use_emz():
                self.field.extra_monster_zone.append({"card": card, "position": Position.ATTACK, "can_attack": True})
                return True
            return False
        else:
            if self.field.can_summon_monster():
                self.field.monster_zone.append({"card": card, "position": Position.ATTACK, "can_attack": True})
                return True
            return False

    def set_spell_trap(self, card: Card, hand_index: int) -> bool:
        if card.card_type not in (CardType.SPELL, CardType.TRAP):
            return False

        # 鍦哄湴榄旀硶鏀惧埌鍦哄湴榄旀硶鍖?        if card.card_type == CardType.SPELL and card.spell_type == SpellType.FIELD:
            self.hand.pop(hand_index)
            if self.field.field_zone:
                old = self.field.field_zone["card"]
                self.graveyard.append(old)
            self.field.field_zone = {"card": card, "is_set": False}
            return True

        if not self.field.can_place_st():
            return False
        self.hand.pop(hand_index)
        is_set = True
        can_activate = False  # 鐩栨斁褰撳洖鍚堜笉鑳藉彂鍔紙閫熸敾榄旀硶闄ゅ锛?        if card.card_type == CardType.SPELL and card.spell_type == SpellType.QUICK:
            can_activate = True
        self.field.spell_trap_zone.append({"card": card, "is_set": is_set, "can_activate": can_activate})
        return True

    def activate_spell_from_hand(self, card: Card, hand_index: int, gs, target=None) -> bool:
        if card.card_type != CardType.SPELL:
            return False

        # 鍦哄湴榄旀硶鐩存帴鍙戝姩鍒板満鍦板尯
        if card.spell_type == SpellType.FIELD:
            self.hand.pop(hand_index)
            if self.field.field_zone:
                old = self.field.field_zone["card"]
                self.graveyard.append(old)
            self.field.field_zone = {"card": card, "is_set": False}
            if card.effect:
                card.effect(gs, self, target, card)
            return True

        # 鍏朵粬榄旀硶闇€瑕侀瓟闄峰尯
        if not self.field.can_place_st():
            return False
        self.hand.pop(hand_index)
        self.graveyard.append(card)
        if card.effect:
            return card.effect(gs, self, target, card)
        return True

    def activate_trap(self, zone_index: int, gs, target=None) -> bool:
        if zone_index >= len(self.field.spell_trap_zone):
            return False
        st = self.field.spell_trap_zone[zone_index]
        if st["card"].card_type != CardType.TRAP:
            return False
        if st["is_set"] and not st["can_activate"]:
            return False
        card = st["card"]
        self.field.spell_trap_zone.pop(zone_index)
        self.graveyard.append(card)
        if card.effect:
            return card.effect(gs, self, target, card)
        return True

    def activate_set_spell(self, zone_index: int, gs, target=None) -> bool:
        """鍙戝姩鐩栨斁鐨勯€熸敾榄旀硶"""
        if zone_index >= len(self.field.spell_trap_zone):
            return False
        st = self.field.spell_trap_zone[zone_index]
        if st["card"].card_type != CardType.SPELL or st["card"].spell_type != SpellType.QUICK:
            return False
        if not st["can_activate"]:
            return False
        card = st["card"]
        self.field.spell_trap_zone.pop(zone_index)
        self.graveyard.append(card)
        if card.effect:
            return card.effect(gs, self, target, card)
        return True

class GameState:
    def __init__(self, p1_name: str = "鐜╁1", p2_name: str = "鐜╁2"):
        init_database()
        self.player1 = Player(p1_name)
        self.player2 = Player(p2_name)
        self.turn_player_idx = 0
        self.phase = Phase.DRAW
        self.turn_count = 1
        self.logs: List[str] = []
        self.result = GameResult.ONGOING
        self.players = [self.player1, self.player2]
        self.first_turn = True
        self.pending_attack: Optional[Tuple[Player, int, Optional[int]]] = None
        self.damage_multiplier = 1.0
        self.chain_links = []  # 绠€鍖栬繛閿?
    def log(self, msg: str):
        self.logs.append(msg)
        if len(self.logs) > 200:
            self.logs.pop(0)

    def get_current_player(self) -> Player:
        return self.players[self.turn_player_idx]

    def get_opponent(self, player: Player) -> Player:
        return self.player2 if player == self.player1 else self.player1

    def get_opponent_player(self) -> Player:
        return self.players[1 - self.turn_player_idx]

    def start_game(self, deck1: List[Card], extra1: List[Card], deck2: List[Card], extra2: List[Card]):
        self.player1.deck = [c.copy() for c in deck1]
        self.player1.extra_deck = [c.copy() for c in extra1]
        self.player2.deck = [c.copy() for c in deck2]
        self.player2.extra_deck = [c.copy() for c in extra2]

        for p in self.players:
            p.shuffle_deck()
            p.draw_initial(5)

        self.log("鍐虫枟寮€濮嬶紒鍙屾柟LP 8000锛屾娊鍙栧垵濮嬫墜鐗?寮犮€?)
        self.phase = Phase.DRAW
        self.start_turn()

    def start_turn(self):
        player = self.get_current_player()
        self.log(f"=== {player.name} 鐨勭 {self.turn_count} 鍥炲悎 [{self.phase.value}] ===")

        # 閲嶇疆鐘舵€?        player.can_still_summon = True
        player.has_normal_summoned = False
        player.has_normal_set = False
        self.damage_multiplier = 1.0

        # 鎶藉崱闃舵
        self.phase = Phase.DRAW
        if not self.first_turn:
            drawn = player.draw()
            if drawn:
                self.log(f"{player.name} 鎶藉埌浜嗐€恵drawn.name}銆?)
            else:
                self.log(f"{player.name} 鍗＄粍鎶界┖锛?)
                self.end_game(self.get_opponent_player())
                return
        else:
            self.first_turn = False
            self.log("鍏堟敾涓嶆娊鍗?)

        self.phase = Phase.STANDBY
        self.log("鍑嗗闃舵")
        self.phase = Phase.MAIN1
        self.log("杩涘叆涓昏闃舵1")

    def next_phase(self):
        if self.phase == Phase.MAIN1:
            self.phase = Phase.BATTLE
            self.log("杩涘叆鎴樻枟闃舵锛?)
        elif self.phase == Phase.BATTLE:
            self.phase = Phase.MAIN2
            self.log("杩涘叆涓昏闃舵2")
        elif self.phase == Phase.MAIN2:
            self.phase = Phase.END
            self.log("缁撴潫闃舵")
            self.end_turn()
        elif self.phase == Phase.MAIN1 and not self.get_current_player().field.monster_zone:
            # 娌℃湁鎬吔鍙互鐩存帴缁撴潫
            self.phase = Phase.END
            self.log("缁撴潫闃舵")
            self.end_turn()

    def end_turn(self):
        self.turn_player_idx = 1 - self.turn_player_idx
        self.turn_count += 1
        self.start_turn()

    def check_win(self) -> GameResult:
        p1, p2 = self.player1, self.player2
        if p1.lp <= 0 and p2.lp <= 0:
            self.result = GameResult.DRAW
        elif p1.lp <= 0:
            self.result = GameResult.PLAYER2_WIN
        elif p2.lp <= 0:
            self.result = GameResult.PLAYER1_WIN
        return self.result

    def end_game(self, winner: Optional[Player] = None):
        if winner == self.player1:
            self.result = GameResult.PLAYER1_WIN
        elif winner == self.player2:
            self.result = GameResult.PLAYER2_WIN
        else:
            self.result = GameResult.DRAW
        self.log(f"鍐虫枟缁撴潫锛亄self.result.value}")

    # ==================== 鎴樻枟绯荤粺 ====================
    def declare_attack(self, attacker_idx: int, target_idx: Optional[int] = None) -> bool:
        """鏀诲嚮瀹ｈ█"""
        attacker_p = self.get_current_player()
        defender_p = self.get_opponent_player()

        if attacker_idx >= len(attacker_p.field.monster_zone):
            return False

        atk_data = attacker_p.field.monster_zone[attacker_idx]
        atk_monster = atk_data["card"]

        if atk_data["position"] != Position.ATTACK:
            self.log("鏀诲嚮琛ㄧず鐨勬€吔鎵嶈兘鏀诲嚮锛?)
            return False

        if not atk_data.get("can_attack", True):
            self.log("杩欏彧鎬吔杩欏洖鍚堜笉鑳芥敾鍑伙紒")
            return False

        self.pending_attack = (attacker_p, attacker_idx, target_idx)

        if target_idx is None:
            # 鐩存帴鏀诲嚮
            damage = atk_monster.atk
            defender_p.lp -= int(damage * self.damage_multiplier)
            self.log(f"銆恵atk_monster.name}銆戠洿鎺ユ敾鍑伙紒缁欎簣 {damage} 鎴樻枟浼ゅ锛?)
        else:
            if target_idx >= len(defender_p.field.monster_zone):
                return False
            def_data = defender_p.field.monster_zone[target_idx]
            def_monster = def_data["card"]

            # 澶勭悊閲屼晶瀹堝琛ㄧず琚敾鍑?            if def_data["position"] == Position.FACE_DOWN_DEFENSE:
                def_data["position"] = Position.DEFENSE  # 缈诲紑
                self.log(f"銆恵def_monster.name}銆戣鏀诲嚮缈诲紑锛?)
                # 缈昏浆鏁堟灉锛堢畝鍖栵細鐩存帴澶勭悊锛?                if def_monster.effect:
                    def_monster.effect(self, defender_p, None, def_monster)

            if def_data["position"] == Position.ATTACK:
                # 鏀诲鏀?                if atk_monster.atk > def_monster.atk:
                    diff = atk_monster.atk - def_monster.atk
                    defender_p.lp -= int(diff * self.damage_multiplier)
                    defender_p.field.monster_zone.pop(target_idx)
                    defender_p.graveyard.append(def_monster)
                    self.log(f"銆恵atk_monster.name}銆?{atk_monster.atk}) 鍑荤牬 銆恵def_monster.name}銆?{def_monster.atk})锛佺粰浜?{diff} 浼ゅ锛?)
                elif atk_monster.atk == def_monster.atk:
                    attacker_p.field.monster_zone.pop(attacker_idx)
                    attacker_p.graveyard.append(atk_monster)
                    defender_p.field.monster_zone.pop(target_idx)
                    defender_p.graveyard.append(def_monster)
                    self.log(f"鍚屽綊浜庡敖锛併€恵atk_monster.name}銆戜笌銆恵def_monster.name}銆戜簰鐩哥牬鍧忥紒")
                    return True
                else:
                    diff = def_monster.atk - atk_monster.atk
                    attacker_p.lp -= int(diff * self.damage_multiplier)
                    attacker_p.field.monster_zone.pop(attacker_idx)
                    attacker_p.graveyard.append(atk_monster)
                    self.log(f"銆恵atk_monster.name}銆戞敾鍑诲け璐ワ紒鍙楀埌 {diff} 鍙嶅脊浼ゅ锛?)
            else:
                # 鏀诲瀹?                if atk_monster.atk > def_monster.defense:
                    defender_p.field.monster_zone.pop(target_idx)
                    defender_p.graveyard.append(def_monster)
                    self.log(f"銆恵atk_monster.name}銆戠牬鍧忓畧澶囪〃绀虹殑銆恵def_monster.name}銆戯紒")
                elif atk_monster.atk == def_monster.defense:
                    self.log(f"銆恵atk_monster.name}銆戜笌銆恵def_monster.name}銆戝娍鍧囧姏鏁岋紒")
                else:
                    diff = def_monster.defense - atk_monster.atk
                    attacker_p.lp -= int(diff * self.damage_multiplier)
                    self.log(f"銆恵atk_monster.name}銆戞敾鍑诲畧澶囨€吔澶辫触锛佸彈鍒?{diff} 璐┛浼ゅ锛?)

        self.pending_attack = None
        self.check_win()
        return True

    # ==================== 鐗规畩鍙敜绯荤粺 ====================
    def fusion_summon(self, fusion_card: Card, material_indices: List[int], from_hand: List[int]) -> bool:
        """铻嶅悎鍙敜"""
        player = self.get_current_player()
        if fusion_card.monster_type != MonsterType.FUSION:
            return False

        # 鏀堕泦绱犳潗
        materials = []
        # 浠庡満涓?        field_mats = sorted(material_indices, reverse=True)
        for idx in field_mats:
            if idx < len(player.field.monster_zone):
                m = player.field.monster_zone.pop(idx)
                materials.append(m["card"])
                player.graveyard.append(m["card"])
        # 浠庢墜鐗?        hand_mats = sorted(from_hand, reverse=True)
        for idx in hand_mats:
            if idx < len(player.hand):
                m = player.hand.pop(idx)
                materials.append(m)
                player.graveyard.append(m)

        success = player.special_summon(fusion_card.copy(), from_extra=True)
        if success:
            self.log(f"铻嶅悎鍙敜锛併€恵fusion_card.name}銆戯紒")
            # 浠庨澶栧崱缁勭Щ闄?            for i, c in enumerate(player.extra_deck):
                if c.id == fusion_card.id:
                    player.extra_deck.pop(i)
                    break
        else:
            self.log("铻嶅悎鍙敜澶辫触锛?)
        return success

    def synchro_summon(self, synchro_card: Card, tuner_idx: int, non_tuner_indices: List[int]) -> bool:
        """鍚岃皟鍙敜锛氳皟鏁?鍙?+ 闈炶皟鏁?鍙互涓婏紝绛夌骇鍚堣=鍚岃皟鎬吔绛夌骇"""
        player = self.get_current_player()
        if synchro_card.monster_type != MonsterType.SYNCHRO:
            return False

        if tuner_idx >= len(player.field.monster_zone):
            return False

        tuner_data = player.field.monster_zone[tuner_idx]
        tuner = tuner_data["card"]
        if not tuner.is_tuner and tuner.monster_type != MonsterType.TUNER:
            self.log("鍚岃皟鍙敜闇€瑕佽皟鏁存€吔锛?)
            return False

        total_level = tuner.level
        materials = [tuner]

        # 绉婚櫎璋冩暣
        player.field.monster_zone.pop(tuner_idx)
        player.graveyard.append(tuner)

        # 绉婚櫎闈炶皟鏁?        sorted_indices = sorted(non_tuner_indices, reverse=True)
        for idx in sorted_indices:
            if idx >= len(player.field.monster_zone):
                continue
            m_data = player.field.monster_zone[idx]
            m = m_data["card"]
            if m.is_tuner or m.monster_type == MonsterType.TUNER:
                self.log("鍚岃皟绱犳潗涓嶈兘鍖呭惈璋冩暣鎬吔锛堥櫎璋冩暣鏈韩澶栵級锛?)
                return False
            total_level += m.level
            materials.append(m)
            player.field.monster_zone.pop(idx)
            player.graveyard.append(m)

        if total_level != synchro_card.level:
            self.log(f"鏄熺骇鍚堣涓簕total_level}锛岄渶瑕亄synchro_card.level}鏄燂紒")
            return False

        success = player.special_summon(synchro_card.copy(), from_extra=True)
        if success:
            self.log(f"鍚岃皟鍙敜锛併€恵synchro_card.name}銆戯紒")
            for i, c in enumerate(player.extra_deck):
                if c.id == synchro_card.id:
                    player.extra_deck.pop(i)
                    break
        return success

    def xyz_summon(self, xyz_card: Card, material_indices: List[int]) -> bool:
        """瓒呴噺鍙敜锛?鍙互涓婂悓绛夌骇鎬吔鍙犳斁"""
        player = self.get_current_player()
        if xyz_card.monster_type != MonsterType.XYZ:
            return False

        if len(material_indices) < 2:
            self.log("瓒呴噺鍙敜闇€瑕?鍙互涓婃€吔锛?)
            return False

        first_level = None
        materials = []
        sorted_indices = sorted(material_indices, reverse=True)

        for idx in sorted_indices:
            if idx >= len(player.field.monster_zone):
                continue
            m_data = player.field.monster_zone[idx]
            m = m_data["card"]
            if first_level is None:
                first_level = m.level
            elif m.level != first_level:
                self.log("瓒呴噺绱犳潗蹇呴』鏄悓绛夌骇鎬吔锛?)
                return False
            materials.append(m)
            player.field.monster_zone.pop(idx)

        if len(materials) < 2:
            return False

        xyz_copy = xyz_card.copy()
        xyz_copy.xyz_materials = materials
        success = player.special_summon(xyz_copy, from_extra=True)
        if success:
            self.log(f"瓒呴噺鍙敜锛併€恵xyz_card.name}銆戯紒浣跨敤{len(materials)}涓猉YZ绱犳潗锛?)
            for i, c in enumerate(player.extra_deck):
                if c.id == xyz_card.id:
                    player.extra_deck.pop(i)
                    break
        return success

    def xyz_detach(self, xyz_idx: int, gs, target=None) -> bool:
        """鍘婚櫎瓒呴噺绱犳潗鍙戝姩鏁堟灉"""
        player = self.get_current_player()
        if xyz_idx >= len(player.field.monster_zone):
            return False
        m_data = player.field.monster_zone[xyz_idx]
        m = m_data["card"]
        if m.monster_type != MonsterType.XYZ or not m.xyz_materials:
            return False
        detached = m.xyz_materials.pop(0)
        player.graveyard.append(detached)
        self.log(f"銆恵m.name}銆戝幓闄?涓猉YZ绱犳潗銆恵detached.name}銆戯紒")
        if m.effect:
            return m.effect(gs, player, target, m)
        return True

    def flip_summon(self, idx: int) -> bool:
        """缈昏浆鍙敜"""
        player = self.get_current_player()
        if idx >= len(player.field.monster_zone):
            return False
        m_data = player.field.monster_zone[idx]
        if m_data["position"] != Position.FACE_DOWN_DEFENSE:
            return False
        m_data["position"] = Position.ATTACK
        self.log(f"銆恵m_data['card'].name}銆戠炕杞彫鍞わ紒")
        if m_data["card"].effect:
            m_data["card"].effect(self, player, None, m_data["card"])
        return True

# ==================== 鍗＄粍鏋勫缓鍣?====================
class DeckBuilder:
    def __init__(self):
        init_database()
        self.all_cards = get_all_cards()

    def validate_main_deck(self, deck: List[Card]) -> Tuple[bool, str]:
        if len(deck) < 40 or len(deck) > 60:
            return False, f"涓诲崱缁勫繀椤讳负40-60寮狅紙褰撳墠{len(deck)}寮狅級"
        name_counts = {}
        for c in deck:
            if c.is_extra_deck:
                return False, f"銆恵c.name}銆戞槸棰濆鍗＄粍鎬吔锛屼笉鑳芥斁鍏ヤ富鍗＄粍"
            name_counts[c.name] = name_counts.get(c.name, 0) + 1
        for name, count in name_counts.items():
            if count > 3:
                return False, f"銆恵name}銆戣秴杩囬檺鍒讹紙鏈€澶?寮狅級"
        return True, "鍗＄粍鍚堟硶"

    def validate_extra_deck(self, deck: List[Card]) -> Tuple[bool, str]:
        if len(deck) > 15:
            return False, f"棰濆鍗＄粍鏈€澶?5寮狅紙褰撳墠{len(deck)}寮狅級"
        name_counts = {}
        for c in deck:
            if not c.is_extra_deck:
                return False, f"銆恵c.name}銆戜笉鏄澶栧崱缁勬€吔"
            name_counts[c.name] = name_counts.get(c.name, 0) + 1
        for name, count in name_counts.items():
            if count > 3:
                return False, f"銆恵name}銆戣秴杩囬檺鍒讹紙鏈€澶?寮狅級"
        return True, "棰濆鍗＄粍鍚堟硶"

    def create_default_main(self) -> List[Card]:
        """鍒涘缓榛樿涓诲崱缁勶紙40寮狅級"""
        deck = []
        ids = [1,1,2,2,3,3,4,5,6,6,7,7,8,9,10,
               11,12,13,14,15,16,17,18,19,20,
               21,22,23,24,25,26,27,28,29,30,
               31,32,33,34,35]  # 鎬吔
        ids += [51,52,53,59,59,60,63,64,69,70,74,76]  # 榄旀硶
        ids += [81,82,83,91,96,99]  # 闄烽槺
        for cid in ids:
            c = get_card_by_id(cid)
            if c: deck.append(c)
        random.shuffle(deck)
        return deck

    def create_default_extra(self) -> List[Card]:
        """鍒涘缓榛樿棰濆鍗＄粍锛?5寮狅級"""
        deck = []
        ids = [101,102,103,104,105,121,122,123,124,125,141,142,143,144,145]
        for cid in ids:
            c = get_card_by_id(cid)
            if c: deck.append(c)
        return deck
