# -*- coding: utf-8 -*-
"""
娓告垙鐜婣I - 鍩轰簬瑙勫垯鐨凙I瀵规墜
"""
from typing import Optional, Tuple, List
import random
from cards import Card, CardType, MonsterType, SpellType, TrapType, Position
from engine import GameState, Phase, Player, MonsterType

class YGOAI:
    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty

    def think(self, gs: GameState) -> Optional[Tuple[str, dict]]:
        player = gs.get_current_player()
        opponent = gs.get_opponent_player()

        if gs.phase == Phase.MAIN1 or gs.phase == Phase.MAIN2:
            # 1. 浼樺厛鐗规畩鍙敜锛堣瀺鍚?鍚岃皟/瓒呴噺锛?            action = self._think_extra_summon(gs, player)
            if action: return action

            # 2. 鍙戝姩榄旀硶鍗?            action = self._think_spell(gs, player)
            if action: return action

            # 3. 閫氬父鍙敜
            action = self._think_normal_summon(gs, player)
            if action: return action

            # 4. 鐩栨斁鎬吔鎴栭瓟闄?            action = self._think_set(gs, player)
            if action: return action

            # 5. 缈昏浆鍙敜
            action = self._think_flip(gs, player)
            if action: return action

            # 杩涘叆鎴樻枟闃舵鎴栫粨鏉?            if gs.phase == Phase.MAIN1 and player.field.monster_zone:
                return ("next_phase", {})
            else:
                return ("next_phase", {})

        elif gs.phase == Phase.BATTLE:
            action = self._think_battle(gs, player, opponent)
            if action: return action
            return ("next_phase", {})

        return ("next_phase", {})

    def _think_normal_summon(self, gs, player: Player) -> Optional[Tuple[str, dict]]:
        if not player.can_still_summon:
            return None
        candidates = []
        for i, c in enumerate(player.hand):
            if c.card_type == CardType.MONSTER and not c.is_extra_deck:
                can, _ = player.can_normal_summon(c)
                if can:
                    candidates.append((i, c))
        if not candidates:
            return None

        if self.difficulty == "easy":
            idx, card = random.choice(candidates)
        else:
            # 浼樺厛鍙敜楂樻敾鎬?            candidates.sort(key=lambda x: x[1].atk, reverse=True)
            idx, card = candidates[0]

        # 4鏄熶互涓婁紭鍏堟敾鍑昏〃绀猴紝鏈夐槻寰″姏鐨勮€冭檻瀹堝
        pos = Position.ATTACK
        if card.defense > card.atk * 1.5 and self.difficulty != "easy":
            pos = Position.DEFENSE
        return ("normal_summon", {"hand_index": idx, "position": pos})

    def _think_extra_summon(self, gs, player: Player) -> Optional[Tuple[str, dict]]:
        """鎬濊€冭瀺鍚?鍚岃皟/瓒呴噺鍙敜"""
        if self.difficulty == "easy":
            return None  # 绠€鍗旳I涓嶇敤棰濆

        # 瓒呴噺鍙敜锛堟渶绠€鍗曞垽鏂級
        xyz_candidates = []
        for ex in player.extra_deck:
            if ex.monster_type == MonsterType.XYZ:
                # 鎵惧満涓婂悓绛夌骇鎬吔
                levels = {}
                for i, m in enumerate(player.field.monster_zone):
                    lv = m["card"].level
                    if lv > 0:
                        if lv not in levels:
                            levels[lv] = []
                        levels[lv].append(i)
                for lv, indices in levels.items():
                    if len(indices) >= 2:
                        xyz_candidates.append((ex, indices[:2]))

        if xyz_candidates:
            xyz, mats = random.choice(xyz_candidates)
            return ("xyz_summon", {"xyz_card_id": xyz.id, "material_indices": mats})

        # 鍚岃皟鍙敜
        synchro_candidates = []
        for ex in player.extra_deck:
            if ex.monster_type == MonsterType.SYNCHRO:
                for ti, t_data in enumerate(player.field.monster_zone):
                    tuner = t_data["card"]
                    if tuner.is_tuner or tuner.monster_type == MonsterType.TUNER:
                        needed = ex.level - tuner.level
                        if needed <= 0:
                            continue
                        # 鎵鹃潪璋冩暣鍚堣=needed
                        non_tuners = []
                        for ni, n_data in enumerate(player.field.monster_zone):
                            if ni == ti:
                                continue
                            nc = n_data["card"]
                            if not nc.is_tuner and nc.monster_type != MonsterType.TUNER:
                                non_tuners.append((ni, nc.level))
                        # 绠€鍗曪細鎵句竴鍙瓑绾ф濂?needed鐨?                        for ni, nlv in non_tuners:
                            if nlv == needed:
                                synchro_candidates.append((ex, ti, [ni]))
                                break

        if synchro_candidates:
            sc, ti, nis = random.choice(synchro_candidates)
            return ("synchro_summon", {"synchro_card_id": sc.id, "tuner_idx": ti, "non_tuner_indices": nis})

        # 铻嶅悎鍙敜锛堢畝鍖栵細鎵嬬墝+鍦轰笂绱犳潗锛?        fusion_candidates = []
        for ex in player.extra_deck:
            if ex.monster_type == MonsterType.FUSION:
                # 绠€鍖栧垽鏂細鍙鍦轰笂鏈夋€?鎵嬬墝鏈夋€氨灏濊瘯
                if player.field.monster_zone and any(c.card_type == CardType.MONSTER for c in player.hand):
                    fusion_candidates.append(ex)
        if fusion_candidates and random.random() < 0.3:
            fc = random.choice(fusion_candidates)
            field_idx = [0] if player.field.monster_zone else []
            hand_idx = [i for i, c in enumerate(player.hand) if c.card_type == CardType.MONSTER][:1]
            return ("fusion_summon", {"fusion_card_id": fc.id, "field_indices": field_idx, "hand_indices": hand_idx})

        return None

    def _think_spell(self, gs, player: Player) -> Optional[Tuple[str, dict]]:
        for i, c in enumerate(player.hand):
            if c.card_type == CardType.SPELL:
                if "鎶? in c.description:
                    return ("activate_spell", {"hand_index": i, "target": None})
                elif "鐮村潖" in c.description and ("鎬吔" in c.description or "榄旈櫡" in c.description):
                    return ("activate_spell", {"hand_index": i, "target": None})
                elif "浼ゅ" in c.description:
                    return ("activate_spell", {"hand_index": i, "target": None})
                elif "鎭㈠" in c.description and player.lp < 4000:
                    return ("activate_spell", {"hand_index": i, "target": None})
                elif "鍦哄湴" in c.description or c.spell_type and c.spell_type.value == "鍦哄湴":
                    return ("activate_spell", {"hand_index": i, "target": None})
        return None

    def _think_set(self, gs, player: Player) -> Optional[Tuple[str, dict]]:
        # 鐩栨斁闄烽槺鎴栭€熸敾榄旀硶
        for i, c in enumerate(player.hand):
            if c.card_type == CardType.TRAP:
                return ("set_st", {"hand_index": i})
            elif c.card_type == CardType.SPELL and c.spell_type and c.spell_type.value == "閫熸敾":
                return ("set_st", {"hand_index": i})
        # 鐩栨斁浣庣骇鎬吔
        if player.can_still_summon:
            for i, c in enumerate(player.hand):
                if c.card_type == CardType.MONSTER and c.level <= 4 and not c.is_extra_deck:
                    if self.difficulty != "easy" or random.random() < 0.3:
                        return ("set_monster", {"hand_index": i})
        return None

    def _think_flip(self, gs, player: Player) -> Optional[Tuple[str, dict]]:
        for i, m in enumerate(player.field.monster_zone):
            if m["position"].value == "閲屼晶瀹堝琛ㄧず":
                if self.difficulty != "easy":
                    return ("flip_summon", {"idx": i})
        return None

    def _think_battle(self, gs, player: Player, opponent: Player) -> Optional[Tuple[str, dict]]:
        for i, m in enumerate(player.field.monster_zone):
            if m["position"] != Position.ATTACK or not m.get("can_attack", True):
                continue

            if opponent.field.monster_zone:
                # 鎵捐兘鍑荤牬鐨勭洰鏍?                best_target = None
                best_val = -9999
                for j, om in enumerate(opponent.field.monster_zone):
                    if m["card"].atk > om["card"].defense:
                        val = om["card"].atk + (m["card"].atk - om["card"].defense)
                        if val > best_val:
                            best_val = val
                            best_target = j
                if best_target is not None:
                    return ("attack", {"attacker_idx": i, "target_idx": best_target})

                # 鎵炬敾鍑诲姏鏈€浣庣殑鎹?                weakest = min(range(len(opponent.field.monster_zone)), 
                             key=lambda j: opponent.field.monster_zone[j]["card"].atk)
                if m["card"].atk >= opponent.field.monster_zone[weakest]["card"].atk:
                    return ("attack", {"attacker_idx": i, "target_idx": weakest})
            else:
                return ("attack", {"attacker_idx": i, "target_idx": None})
        return None

    def respond(self, gs: GameState) -> Optional[Tuple[str, dict]]:
        """鍝嶅簲瀵规墜琛屽姩锛堝彂鍔ㄩ櫡闃辩瓑锛?""
        player = gs.get_opponent_player()
        for i, st in enumerate(player.field.spell_trap_zone):
            if st["card"].card_type == CardType.TRAP and st.get("can_activate", False):
                if self.difficulty == "easy":
                    if random.random() < 0.4:
                        return ("activate_trap", {"zone_index": i})
                else:
                    if player.lp < 3000 or "绁炲湥" in st["card"].name or "鏀诲嚮" in st["card"].name:
                        return ("activate_trap", {"zone_index": i})
        return None
