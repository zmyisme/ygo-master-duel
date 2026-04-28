# -*- coding: utf-8 -*-
"""
娓告垙鐜嬪ぇ甯堝喅鏂?- Kivy涓荤▼搴?"""
import os
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_WINDOW'] = 'sdl2'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from cards import (Card, CardType, MonsterType, SpellType, TrapType, Position,
                   get_all_cards, get_card_by_id, get_main_deck_cards, get_extra_deck_cards)
from engine import GameState, Phase, GameResult, Player, DeckBuilder
from ai import YGOAI

# ==================== 鏍峰紡甯搁噺 ====================
CW = dp(65)   # 鍗＄墝瀹藉害
CH = dp(95)   # 鍗＄墝楂樺害
MC = (0.15, 0.35, 0.75, 1)   # 鎬吔鍗¤摑
SC = (0.2, 0.7, 0.4, 1)      # 榄旀硶鍗＄豢
TC = (0.75, 0.15, 0.55, 1)   # 闄烽槺鍗＄传
FC = (0.6, 0.3, 0.1, 1)      # 鍦哄湴鍗℃
EC = (0.5, 0.2, 0.7, 1)      # 棰濆绱?BG = (0.1, 0.1, 0.14, 1)     # 鑳屾櫙

# ==================== 鍗＄墝缁勪欢 ====================
class CardBtn(Button):
    def __init__(self, card: Card, **kwargs):
        self.card_obj = card
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (CW, CH)
        self.font_size = dp(9)
        self.halign = 'center'
        self.valign = 'middle'
        self.update_display()

    def update_display(self, face_down: bool = False):
        c = self.card_obj
        if face_down:
            self.text = "???"
            self.background_color = (0.25, 0.25, 0.3, 1)
            return
        if c.card_type == CardType.MONSTER:
            if c.monster_type == MonsterType.FUSION:
                self.background_color = (0.6, 0.3, 0.7, 1)
            elif c.monster_type == MonsterType.SYNCHRO:
                self.background_color = (0.9, 0.9, 0.9, 1)
            elif c.monster_type == MonsterType.XYZ:
                self.background_color = (0.15, 0.15, 0.15, 1)
                self.color = (1, 1, 1, 1)
            elif c.is_tuner:
                self.background_color = (0.9, 0.8, 0.5, 1)
            else:
                self.background_color = MC
            star = f"鈽厈c.level}" if c.level > 0 else f"鈽唟c.rank}"
            self.text = f"{c.name}\n{star}\n{c.atk}/{c.defense}"
        elif c.card_type == CardType.SPELL:
            self.background_color = FC if c.spell_type and c.spell_type.value == "鍦哄湴" else SC
            self.text = f"銆愰瓟銆憑c.name}"
        else:
            self.background_color = TC
            self.text = f"銆愰櫡銆憑c.name}"

# ==================== 鍦哄湴鏍煎瓙 ====================
class Zone(BoxLayout):
    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (CW + dp(8), CH + dp(18))
        with self.canvas.before:
            Color(0.2, 0.2, 0.25, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.bind(pos=self._upd, size=self._upd)
        self.lbl = Label(text=label, size_hint=(1, None), height=dp(14), font_size=dp(8))
        self.add_widget(self.lbl)
        self.card_btn = None

    def _upd(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_card(self, card=None, face_down=False, label=""):
        if self.card_btn:
            self.remove_widget(self.card_btn)
            self.card_btn = None
        if card:
            self.card_btn = CardBtn(card)
            self.card_btn.update_display(face_down)
            self.add_widget(self.card_btn)
            self.lbl.text = label
        else:
            self.lbl.text = label

# ==================== 鐜╁淇℃伅 ====================
class InfoBar(BoxLayout):
    def __init__(self, player: Player, is_top=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(36)
        self.padding = dp(4)
        self.spacing = dp(8)
        self.lp_lbl = Label(text=f"LP:{player.lp}", font_size=dp(13), bold=True,
                           color=(1, 0.3, 0.3, 1) if is_top else (0.3, 1, 0.3, 1))
        self.name_lbl = Label(text=player.name, font_size=dp(13), bold=True)
        self.detail_lbl = Label(text="", font_size=dp(10))
        if is_top:
            self.add_widget(self.detail_lbl); self.add_widget(self.name_lbl); self.add_widget(self.lp_lbl)
        else:
            self.add_widget(self.lp_lbl); self.add_widget(self.name_lbl); self.add_widget(self.detail_lbl)

    def update(self, p: Player, is_turn=False):
        self.lp_lbl.text = f"LP:{p.lp}"
        self.name_lbl.text = p.name + (" [鍥炲悎]" if is_turn else "")
        self.detail_lbl.text = f"鎵?{len(p.hand)} 澧?{len(p.graveyard)} 闄?{len(p.banished)} 棰?{len(p.extra_deck)}"

# ==================== 鎵嬬墝鍖?====================
class HandZone(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='horizontal', size_hint=(None, 1), spacing=dp(4), padding=dp(4))
        self.layout.bind(minimum_width=self.layout.setter('width'))
        self.add_widget(self.layout)
        self.selected = None
        self.btns = []

    def set_hand(self, hand, selectable=True):
        self.layout.clear_widgets()
        self.btns = []
        self.selected = None
        for i, c in enumerate(hand):
            b = CardBtn(c)
            if selectable:
                b.bind(on_press=lambda inst, idx=i: self._sel(idx))
            self.layout.add_widget(b)
            self.btns.append(b)
        self.layout.width = len(hand) * (CW + dp(4)) + dp(8)

    def _sel(self, idx):
        self.selected = idx
        for i, b in enumerate(self.btns):
            b.background_color = [min(1, x + 0.25) for x in b.background_color[:3]] + [1] if i == idx else b.background_color

# ==================== 鏃ュ織 ====================
class LogView(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lbl = Label(text="", size_hint=(1, None), font_size=dp(10),
                        halign='left', valign='top', text_size=(None, None), color=(0.9, 0.9, 0.9, 1))
        self.lbl.bind(texture_size=self.lbl.setter('size'))
        self.add_widget(self.lbl)

    def add(self, txt):
        cur = self.lbl.text
        self.lbl.text = (cur + "\n" + txt) if cur else txt
        self.scroll_to(self.lbl)
    def clear(self):
        self.lbl.text = ""

# ==================== 娓告垙涓诲睆 ====================
class DuelScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gs = None
        self.ai = None
        self.mode = "pvp"
        self.ai_scheduled = False
        self.build_ui()
        Clock.schedule_interval(self.loop, 1/30)

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(3), spacing=dp(2))

        # 瀵规墜淇℃伅
        self.top_info = InfoBar(Player("瀵规墜"), is_top=True)
        root.add_widget(self.top_info)

        # 瀵规墜鍦哄湴
        opp = BoxLayout(orientation='vertical', size_hint=(1, None), height=CH*2+dp(40))
        opp_st = GridLayout(cols=5, spacing=dp(4), size_hint=(1, None), height=CH+dp(20))
        self.opp_fz = Zone("鍦哄湴")
        self.opp_emz = [Zone("EX1"), Zone("EX2")]
        self.opp_stz = [Zone(f"S{i+1}") for i in range(5)]
        for z in [self.opp_fz] + self.opp_emz + self.opp_stz:
            opp_st.add_widget(z)
        opp.add_widget(opp_st)

        opp_mz = GridLayout(cols=5, spacing=dp(4), size_hint=(1, None), height=CH+dp(20))
        self.opp_mz = [Zone(f"M{i+1}") for i in range(5)]
        for z in self.opp_mz:
            opp_mz.add_widget(z)
        opp.add_widget(opp_mz)
        root.add_widget(opp)

        # 涓棿锛氭棩蹇?鎸夐挳
        mid = BoxLayout(orientation='horizontal', size_hint=(1, 1))
        self.logv = LogView()
        mid.add_widget(self.logv)

        btns = BoxLayout(orientation='vertical', size_hint=(None, 1), width=dp(110), spacing=dp(3))
        self.b_summon = Button(text="鍙敜", on_press=self.do_summon, font_size=dp(11))
        self.b_set_m = Button(text="鐩栨斁鎬吔", on_press=self.do_set_monster, font_size=dp(11))
        self.b_spell = Button(text="鍙戝姩榄旀硶", on_press=self.do_spell, font_size=dp(11))
        self.b_set_st = Button(text="鐩栨斁榄旈櫡", on_press=self.do_set_st, font_size=dp(11))
        self.b_fusion = Button(text="铻嶅悎鍙敜", on_press=self.do_fusion, font_size=dp(11))
        self.b_synchro = Button(text="鍚岃皟鍙敜", on_press=self.do_synchro, font_size=dp(11))
        self.b_xyz = Button(text="瓒呴噺鍙敜", on_press=self.do_xyz, font_size=dp(11))
        self.b_flip = Button(text="缈昏浆鍙敜", on_press=self.do_flip, font_size=dp(11))
        self.b_attack = Button(text="鏀诲嚮", on_press=self.do_attack, font_size=dp(11))
        self.b_next = Button(text="缁撴潫闃舵", on_press=self.do_next, font_size=dp(11))
        self.b_back = Button(text="杩斿洖", on_press=lambda x: setattr(self.manager, 'current', 'menu'), font_size=dp(11))
        for b in [self.b_summon, self.b_set_m, self.b_spell, self.b_set_st, self.b_fusion,
                  self.b_synchro, self.b_xyz, self.b_flip, self.b_attack, self.b_next, self.b_back]:
            btns.add_widget(b)
        mid.add_widget(btns)
        root.add_widget(mid)

        # 鎴戞柟鍦哄湴
        my = BoxLayout(orientation='vertical', size_hint=(1, None), height=CH*2+dp(40))
        my_mz = GridLayout(cols=5, spacing=dp(4), size_hint=(1, None), height=CH+dp(20))
        self.my_mz = [Zone(f"M{i+1}") for i in range(5)]
        for z in self.my_mz:
            my_mz.add_widget(z)
        my.add_widget(my_mz)

        my_st = GridLayout(cols=5, spacing=dp(4), size_hint=(1, None), height=CH+dp(20))
        self.my_stz = [Zone(f"S{i+1}") for i in range(5)]
        self.my_emz = [Zone("EX1"), Zone("EX2")]
        self.my_fz = Zone("鍦哄湴")
        for z in self.my_stz + self.my_emz + [self.my_fz]:
            my_st.add_widget(z)
        my.add_widget(my_st)
        root.add_widget(my)

        # 鎴戞柟淇℃伅
        self.bot_info = InfoBar(Player("鎴?), is_top=False)
        root.add_widget(self.bot_info)

        # 鎵嬬墝
        self.handz = HandZone(size_hint=(1, None), height=CH+dp(20))
        root.add_widget(self.handz)

        self.add_widget(root)

    def start_game(self, mode="pvp", diff="normal"):
        self.mode = mode
        builder = DeckBuilder()
        self.gs = GameState("鐜╁", f"AI({diff})" if mode=="ai" else "鐜╁2")
        if mode == "ai":
            self.ai = YGOAI(diff)
        else:
            self.ai = None

        m1 = builder.create_default_main()
        e1 = builder.create_default_extra()
        m2 = builder.create_default_main()
        e2 = builder.create_default_extra()
        self.gs.start_game(m1, e1, m2, e2)
        self.logv.clear()
        self.update_ui()

    def update_ui(self):
        if not self.gs: return
        p1, p2 = self.gs.player1, self.gs.player2
        cur = self.gs.get_current_player()
        bottom, top = p1, p2

        self.top_info.update(top, cur==top)
        self.bot_info.update(bottom, cur==bottom)

        # 鏇存柊瀵规墜鍦哄湴
        self.opp_fz.set_card(top.field.field_zone["card"] if top.field.field_zone else None, label="鍦哄湴")
        for i in range(2):
            em = top.field.extra_monster_zone[i] if i < len(top.field.extra_monster_zone) else None
            self.opp_emz[i].set_card(em["card"] if em else None, label=f"EX{i+1}")
        for i in range(5):
            st = top.field.spell_trap_zone[i] if i < len(top.field.spell_trap_zone) else None
            self.opp_stz[i].set_card(st["card"] if st else None, st["is_set"] if st else False, f"S{i+1}")
        for i in range(5):
            m = top.field.monster_zone[i] if i < len(top.field.monster_zone) else None
            fd = m["position"] == Position.FACE_DOWN_DEFENSE if m else False
            self.opp_mz[4-i].set_card(m["card"] if m else None, fd, f"M{i+1}")

        # 鏇存柊鎴戞柟鍦哄湴
        self.my_fz.set_card(bottom.field.field_zone["card"] if bottom.field.field_zone else None, label="鍦哄湴")
        for i in range(2):
            em = bottom.field.extra_monster_zone[i] if i < len(bottom.field.extra_monster_zone) else None
            self.my_emz[i].set_card(em["card"] if em else None, label=f"EX{i+1}")
        for i in range(5):
            st = bottom.field.spell_trap_zone[i] if i < len(bottom.field.spell_trap_zone) else None
            self.my_stz[i].set_card(st["card"] if st else None, st["is_set"] if st else False, f"S{i+1}")
        for i in range(5):
            m = bottom.field.monster_zone[i] if i < len(bottom.field.monster_zone) else None
            fd = m["position"] == Position.FACE_DOWN_DEFENSE if m else False
            lbl = f"M{i+1}" + ("(鏀?" if m and m["position"]==Position.ATTACK else "(瀹?")
            self.my_mz[i].set_card(m["card"] if m else None, fd, lbl)

        # 鎵嬬墝
        is_my = (cur == bottom)
        self.handz.set_hand(cur.hand if is_my else [])

        # 鏃ュ織
        for log in self.gs.logs[-8:]:
            self.logv.add(log)
        self.gs.logs.clear()

        if self.gs.result != GameResult.ONGOING:
            self.show_result()

    def loop(self, dt):
        if not self.gs or self.gs.result != GameResult.ONGOING:
            return True
        cur = self.gs.get_current_player()
        if self.mode == "ai" and cur == self.gs.player2 and not self.ai_scheduled:
            self.ai_scheduled = True
            Clock.schedule_once(self.ai_turn, 1.2)
        return True

    def ai_turn(self, dt):
        if not self.gs or self.gs.result != GameResult.ONGOING:
            self.ai_scheduled = False; return
        action = self.ai.think(self.gs)
        if action:
            self.exec_action(action)
        self.update_ui()
        cur = self.gs.get_current_player()
        if self.mode == "ai" and cur == self.gs.player2 and self.gs.phase != Phase.END:
            Clock.schedule_once(self.ai_turn, 0.8)
        else:
            self.ai_scheduled = False

    def exec_action(self, action):
        act, p = action
        pl = self.gs.get_current_player()
        if act == "normal_summon":
            c = pl.hand[p["hand_index"]]
            pl.normal_summon(c, p["hand_index"], p.get("position", Position.ATTACK))
        elif act == "set_monster":
            c = pl.hand[p["hand_index"]]
            pl.normal_set(c, p["hand_index"])
        elif act == "activate_spell":
            self.gs.get_current_player().activate_spell_from_hand(
                pl.hand[p["hand_index"]], p["hand_index"], self.gs, p.get("target"))
        elif act == "set_st":
            pl.set_spell_trap(pl.hand[p["hand_index"]], p["hand_index"])
        elif act == "attack":
            self.gs.declare_attack(p["attacker_idx"], p.get("target_idx"))
        elif act == "next_phase":
            self.gs.next_phase()
        elif act == "flip_summon":
            self.gs.flip_summon(p["idx"])
        elif act == "fusion_summon":
            fc = get_card_by_id(p["fusion_card_id"])
            if fc: self.gs.fusion_summon(fc, p.get("field_indices", []), p.get("hand_indices", []))
        elif act == "synchro_summon":
            sc = get_card_by_id(p["synchro_card_id"])
            if sc: self.gs.synchro_summon(sc, p["tuner_idx"], p.get("non_tuner_indices", []))
        elif act == "xyz_summon":
            xc = get_card_by_id(p["xyz_card_id"])
            if xc: self.gs.xyz_summon(xc, p["material_indices"])
        elif act == "activate_trap":
            pl.activate_trap(p["zone_index"], self.gs)

    def do_summon(self, inst):
        idx = self.handz.selected
        if idx is None: self.logv.add("璇烽€夋嫨鎵嬬墝"); return
        pl = self.gs.get_current_player()
        c = pl.hand[idx]
        if c.card_type != CardType.MONSTER or c.is_extra_deck:
            self.logv.add("涓嶈兘閫氬父鍙敜姝ゅ崱"); return
        pos = Position.ATTACK
        pl.normal_summon(c, idx, pos)
        self.update_ui()

    def do_set_monster(self, inst):
        idx = self.handz.selected
        if idx is None: self.logv.add("璇烽€夋嫨鎵嬬墝"); return
        pl = self.gs.get_current_player()
        c = pl.hand[idx]
        if c.card_type != CardType.MONSTER or c.is_extra_deck:
            self.logv.add("涓嶈兘鐩栨斁姝ゅ崱"); return
        pl.normal_set(c, idx)
        self.update_ui()

    def do_spell(self, inst):
        idx = self.handz.selected
        if idx is None: self.logv.add("璇烽€夋嫨鎵嬬墝"); return
        pl = self.gs.get_current_player()
        c = pl.hand[idx]
        if c.card_type != CardType.SPELL:
            self.logv.add("涓嶆槸榄旀硶鍗?); return
        target = None
        if "涓婂崌" in c.description and pl.field.monster_zone:
            target = 0
        pl.activate_spell_from_hand(c, idx, self.gs, target)
        self.update_ui()

    def do_set_st(self, inst):
        idx = self.handz.selected
        if idx is None: self.logv.add("璇烽€夋嫨鎵嬬墝"); return
        pl = self.gs.get_current_player()
        c = pl.hand[idx]
        if c.card_type not in (CardType.SPELL, CardType.TRAP):
            self.logv.add("涓嶆槸榄旈櫡鍗?); return
        pl.set_spell_trap(c, idx)
        self.update_ui()

    def do_fusion(self, inst):
        # 绠€鍖栬瀺鍚堬細鑷姩閫夋嫨绱犳潗
        pl = self.gs.get_current_player()
        if not pl.extra_deck:
            self.logv.add("棰濆鍗＄粍涓虹┖"); return
        fc = None
        for c in pl.extra_deck:
            if c.monster_type == MonsterType.FUSION:
                fc = c; break
        if not fc:
            self.logv.add("娌℃湁铻嶅悎鎬吔"); return
        field_idx = [0] if pl.field.monster_zone else []
        hand_idx = [i for i, c in enumerate(pl.hand) if c.card_type == CardType.MONSTER][:1]
        if not field_idx and not hand_idx:
            self.logv.add("娌℃湁铻嶅悎绱犳潗"); return
        self.gs.fusion_summon(fc, field_idx, hand_idx)
        self.update_ui()

    def do_synchro(self, inst):
        pl = self.gs.get_current_player()
        if not pl.extra_deck:
            self.logv.add("棰濆鍗＄粍涓虹┖"); return
        sc = None
        for c in pl.extra_deck:
            if c.monster_type == MonsterType.SYNCHRO:
                sc = c; break
        if not sc:
            self.logv.add("娌℃湁鍚岃皟鎬吔"); return
        # 鎵捐皟鏁?        ti = None
        for i, m in enumerate(pl.field.monster_zone):
            if m["card"].is_tuner or m["card"].monster_type == MonsterType.TUNER:
                ti = i; break
        if ti is None:
            self.logv.add("鍦轰笂娌℃湁璋冩暣鎬吔"); return
        # 鎵鹃潪璋冩暣
        ni = None
        for i, m in enumerate(pl.field.monster_zone):
            if i != ti and not m["card"].is_tuner and m["card"].monster_type != MonsterType.TUNER:
                if m["card"].level == sc.level - pl.field.monster_zone[ti]["card"].level:
                    ni = i; break
        if ni is None:
            self.logv.add("娌℃湁鍚堥€傜殑鍚岃皟绱犳潗"); return
        self.gs.synchro_summon(sc, ti, [ni])
        self.update_ui()

    def do_xyz(self, inst):
        pl = self.gs.get_current_player()
        if not pl.extra_deck:
            self.logv.add("棰濆鍗＄粍涓虹┖"); return
        xc = None
        for c in pl.extra_deck:
            if c.monster_type == MonsterType.XYZ:
                xc = c; break
        if not xc:
            self.logv.add("娌℃湁瓒呴噺鎬吔"); return
        # 鎵惧悓绛夌骇
        levels = {}
        for i, m in enumerate(pl.field.monster_zone):
            lv = m["card"].level
            if lv > 0:
                if lv not in levels: levels[lv] = []
                levels[lv].append(i)
        mats = None
        for lv, idxs in levels.items():
            if len(idxs) >= 2:
                mats = idxs[:2]; break
        if not mats:
            self.logv.add("娌℃湁鍚岀瓑绾ц秴閲忕礌鏉?); return
        self.gs.xyz_summon(xc, mats)
        self.update_ui()

    def do_flip(self, inst):
        pl = self.gs.get_current_player()
        for i, m in enumerate(pl.field.monster_zone):
            if m["position"] == Position.FACE_DOWN_DEFENSE:
                self.gs.flip_summon(i)
                self.update_ui()
                return
        self.logv.add("娌℃湁閲屼晶瀹堝琛ㄧず鐨勬€吔")

    def do_attack(self, inst):
        if self.gs.phase != Phase.BATTLE:
            self.logv.add("涓嶆槸鎴樻枟闃舵"); return
        pl = self.gs.get_current_player()
        opp = self.gs.get_opponent_player()
        if not pl.field.monster_zone:
            self.logv.add("娌℃湁鏀诲嚮鎬吔"); return
        # 绠€鍖栵細绗竴涓敾鍑昏〃绀烘€吔鏀诲嚮绗竴涓洰鏍囨垨鐩存帴鏀诲嚮
        for i, m in enumerate(pl.field.monster_zone):
            if m["position"] == Position.ATTACK and m.get("can_attack", True):
                ti = 0 if opp.field.monster_zone else None
                self.gs.declare_attack(i, ti)
                self.update_ui()
                return
        self.logv.add("娌℃湁鍙互鏀诲嚮鐨勬€吔")

    def do_next(self, inst):
        self.gs.next_phase()
        self.update_ui()

    def show_result(self):
        Popup(title="鍐虫枟缁撴潫", content=Label(text=self.gs.result.value, font_size=dp(18)),
              size_hint=(0.6, 0.3)).open()

# ==================== 鍗＄粍缂栬緫 ====================
class DeckEditScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_deck = []
        self.extra_deck = []
        self.all_main = get_main_deck_cards()
        self.all_extra = get_extra_deck_cards()
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='horizontal')
        # 鍗℃睜
        left = BoxLayout(orientation='vertical')
        left.add_widget(Label(text="涓诲崱缁勫崱姹狅紙鐐瑰嚮娣诲姞锛?, size_hint=(1, None), height=dp(24)))
        sc1 = ScrollView()
        g1 = GridLayout(cols=3, spacing=dp(4), size_hint=(1, None))
        g1.bind(minimum_height=g1.setter('height'))
        for c in self.all_main:
            b = CardBtn(c)
            b.bind(on_press=lambda inst, c=c: self.add_main(c))
            g1.add_widget(b)
        sc1.add_widget(g1)
        left.add_widget(sc1)

        left.add_widget(Label(text="棰濆鍗＄粍鍗℃睜", size_hint=(1, None), height=dp(24)))
        sc2 = ScrollView()
        g2 = GridLayout(cols=3, spacing=dp(4), size_hint=(1, None))
        g2.bind(minimum_height=g2.setter('height'))
        for c in self.all_extra:
            b = CardBtn(c)
            b.bind(on_press=lambda inst, c=c: self.add_extra(c))
            g2.add_widget(b)
        sc2.add_widget(g2)
        left.add_widget(sc2)
        root.add_widget(left)

        # 褰撳墠鍗＄粍
        right = BoxLayout(orientation='vertical')
        self.main_lbl = Label(text="涓诲崱缁? 0/60", size_hint=(1, None), height=dp(24))
        self.extra_lbl = Label(text="棰濆鍗＄粍: 0/15", size_hint=(1, None), height=dp(24))
        right.add_widget(self.main_lbl)
        right.add_widget(self.extra_lbl)

        self.deck_sc = ScrollView()
        self.deck_grid = GridLayout(cols=3, spacing=dp(4), size_hint=(1, None))
        self.deck_grid.bind(minimum_height=self.deck_grid.setter('height'))
        self.deck_sc.add_widget(self.deck_grid)
        right.add_widget(self.deck_sc)

        br = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(4))
        br.add_widget(Button(text="娓呯┖", on_press=self.clear))
        br.add_widget(Button(text="榛樿", on_press=self.load_default))
        br.add_widget(Button(text="杩斿洖", on_press=lambda x: setattr(self.manager, 'current', 'menu')))
        right.add_widget(br)
        root.add_widget(right)
        self.add_widget(root)

    def add_main(self, card):
        if len(self.main_deck) >= 60: return
        if sum(1 for c in self.main_deck if c.name == card.name) >= 3: return
        self.main_deck.append(card.copy())
        self.refresh()

    def add_extra(self, card):
        if len(self.extra_deck) >= 15: return
        if sum(1 for c in self.extra_deck if c.name == card.name) >= 3: return
        self.extra_deck.append(card.copy())
        self.refresh()

    def refresh(self):
        self.deck_grid.clear_widgets()
        for c in self.main_deck:
            b = CardBtn(c)
            b.bind(on_press=lambda inst, c=c: self.remove(c, "main"))
            self.deck_grid.add_widget(b)
        for c in self.extra_deck:
            b = CardBtn(c)
            b.background_color = EC
            b.bind(on_press=lambda inst, c=c: self.remove(c, "extra"))
            self.deck_grid.add_widget(b)
        self.deck_grid.height = (len(self.main_deck)+len(self.extra_deck)) * (CH+dp(10))
        self.main_lbl.text = f"涓诲崱缁? {len(self.main_deck)}/60"
        self.extra_lbl.text = f"棰濆鍗＄粍: {len(self.extra_deck)}/15"

    def remove(self, card, deck_type):
        if deck_type == "main":
            for i, c in enumerate(self.main_deck):
                if c.id == card.id:
                    self.main_deck.pop(i); break
        else:
            for i, c in enumerate(self.extra_deck):
                if c.id == card.id:
                    self.extra_deck.pop(i); break
        self.refresh()

    def clear(self, inst):
        self.main_deck.clear(); self.extra_deck.clear(); self.refresh()

    def load_default(self, inst):
        b = DeckBuilder()
        self.main_deck = b.create_default_main()
        self.extra_deck = b.create_default_extra()
        self.refresh()

# ==================== 鑿滃崟 ====================
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        bl = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(16))
        bl.add_widget(Label(text="娓告垙鐜嬪ぇ甯堝喅鏂梊nMaster Duel", font_size=dp(28), bold=True, halign='center'))
        bl.add_widget(Label(text="閫夋嫨妯″紡", font_size=dp(14)))
        for txt, mode, diff in [("AI绠€鍗?, "ai", "easy"), ("AI鏅€?, "ai", "normal"),
                                ("AI鍥伴毦", "ai", "hard"), ("鏈湴鍙屼汉", "pvp", "")]:
            bl.add_widget(Button(text=txt, on_press=lambda x, m=mode, d=diff: self.start(m, d)))
        bl.add_widget(Button(text="鍗＄粍缂栬緫", on_press=lambda x: setattr(self.manager, 'current', 'deck')))
        self.add_widget(bl)

    def start(self, mode, diff):
        self.manager.get_screen("duel").start_game(mode, diff)
        self.manager.current = "duel"

# ==================== App ====================
class YGOApp(App):
    def build(self):
        Window.clearcolor = BG
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(DuelScreen(name="duel"))
        sm.add_widget(DeckEditScreen(name="deck"))
        return sm

if __name__ == '__main__':
    YGOApp().run()
