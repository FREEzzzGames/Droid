from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.animation import Animation
import random, math

try:
    from plyer import tts, accelerometer
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


class MiniDroid(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = 0.0
        self.battery = 100.0
        self.oil = 100.0
        self.score = 0
        self.mode = "normal"
        self.jump_offset = 0
        self.blink_state = 1
        self.last_accel = (0, 0, 0)
        self.pos_x = 200
        self.pos_y = 300
        self.dirt_spots = []
        self.items = []
        self.game_timer = 0.0
        self.spawn_timer = 0.0
        if HAS_TTS:
            try:
                accelerometer.enable()
            except Exception:
                pass
        Clock.schedule_interval(self.update, 1 / 60)
        Clock.schedule_interval(self.tick, 1.0)
        Clock.schedule_interval(self.add_dirt, 4.0)

    def tick(self, dt):
        if self.mode == "charging":
            self.battery = min(100.0, self.battery + 5)
            if self.battery >= 100:
                self.mode = "normal"
                self.set_status("Батарея заряжена на 100%!")
        elif self.mode != "sleeping":
            self.battery = max(0.0, self.battery - 0.5)
            self.oil = max(0.0, self.oil - 0.3)
            if self.battery <= 0:
                self.mode = "sleeping"
                self.say("Энергия на нуле. Выключение.")
            elif self.oil <= 0 and random.random() < 0.1:
                self.say("Хочу маслица!")
        app = App.get_running_app()
        if app:
            app.update_ui()

    def add_dirt(self, dt):
        if self.mode in ("normal", "sleeping") and len(self.dirt_spots) < 8:
            max_x = max(50, int(self.width - 50))
            max_y = max(150, int(self.height - 50))
            self.dirt_spots.append([random.randint(50, max_x),
                                    random.randint(80, max_y),
                                    random.randint(20, 40)])

    def update(self, dt):
        if self.mode != "sleeping":
            self.time += min(dt, 0.05)
            self.check_shake()
        self.update_game(min(dt, 0.05))
        self.draw_droid()

    def update_game(self, dt):
        if self.mode != "playing":
            return
        self.game_timer -= dt
        if self.game_timer <= 0:
            self.end_game()
            return
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.items.append({"x": random.randint(50, max(50, int(self.width - 50))),
                               "y": self.height,
                               "type": "battery" if random.random() < 0.7 else "trash",
                               "speed": random.uniform(250, 400)})
            self.spawn_timer = max(0.25, 0.7 - (20 - self.game_timer) * 0.02)
        for item in self.items[:]:
            item["y"] -= item["speed"] * dt
            if item["y"] < 0:
                self.items.remove(item)
            elif math.hypot(item["x"] - self.pos_x, item["y"] - self.pos_y) < 60:
                if item["type"] == "battery":
                    self.score += 10
                    self.battery = min(100, self.battery + 2)
                    self.oil = min(100, self.oil + 1)
                else:
                    self.battery = max(0, self.battery - 10)
                    self.score = max(0, self.score - 5)
                self.items.remove(item)
                self.blink()

    def draw_droid(self):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return
        self.pos_x = max(60, min(max(60, self.width - 60), self.pos_x))
        target_y = self.height / 2 if self.mode != "sleeping" else min(100, self.height / 2)
        self.pos_y += (target_y - self.pos_y) * 0.05
        hover = math.sin(self.time * 3) * 10 if self.mode != "sleeping" else 0
        cx, cy = self.pos_x, self.pos_y + hover - self.jump_offset
        look_x = math.cos(self.time * 10) * 10 if self.mode == "dizzy" else 0
        look_y = math.sin(self.time * 10) * 10 if self.mode == "dizzy" else 0
        body = (0.8, 0.6, 0.1) if self.score >= 300 else ((0.5, 0.2, 0.6) if self.score >= 100 else (0.3, 0.3, 0.35))
        with self.canvas:
            Color(0.2, 0.2, 0.2, 0.5)
            Ellipse(pos=(cx - 40, 90), size=(80, 20))
            Color(0.7, 0.7, 0.8)
            Line(points=[cx, cy + 50, cx, cy + 80], width=3)
            Color(*( (1, 0, 0.5) if self.mode != "sleeping" else (0.3, 0.3, 0.3) ))
            Ellipse(pos=(cx - 6, cy + 76), size=(12, 12))
            Color(*body)
            RoundedRectangle(pos=(cx - 50, cy - 50), size=(100, 100), radius=[30])
            Color(0.1, 0.1, 0.15)
            RoundedRectangle(pos=(cx - 40, cy - 30), size=(80, 60), radius=[15])
            eye = (0, 1, 0) if self.mode == "charging" else ((1, 0, 0) if self.battery < 20 else ((0.2, 0.2, 0.2) if self.mode == "sleeping" else (0, 1, 1)))
            Color(*eye)
            eye_h = max(1, 20 * self.blink_state)
            if self.mode == "sleeping":
                Line(points=[cx - 25, cy - 10, cx - 10, cy - 10], width=3)
                Line(points=[cx + 10, cy - 10, cx + 25, cy - 10], width=3)
            else:
                Ellipse(pos=(cx - 25 + look_x, cy - 10 - eye_h/2 + look_y), size=(15, eye_h))
                Ellipse(pos=(cx + 10 + look_x, cy - 10 - eye_h/2 + look_y), size=(15, eye_h))
                Line(points=[cx - 15, cy - 20, cx, cy - 15, cx + 15, cy - 20], width=2)
            Color(0.5, 0.5, 0.6)
            RoundedRectangle(pos=(cx - 60, cy - 15), size=(10, 30), radius=[5])
            RoundedRectangle(pos=(cx + 50, cy - 15), size=(10, 30), radius=[5])
            for d in self.dirt_spots:
                Color(0.6, 0.6, 0.6, 0.6)
                Ellipse(pos=(d[0]-d[2], d[1]-d[2]), size=(d[2]*2, d[2]*2))
            for item in self.items:
                if item["type"] == "battery":
                    Color(0.2, 1, 0.2)
                    RoundedRectangle(pos=(item["x"]-10, item["y"]-15), size=(20, 30), radius=[5])
                else:
                    Color(1, 0.2, 0.2)
                    Ellipse(pos=(item["x"]-12, item["y"]-12), size=(24, 24))

    def on_touch_down(self, touch):
        if self.mode == "playing":
            return False
        for d in self.dirt_spots[:]:
            if math.hypot(touch.x-d[0], touch.y-d[1]) < d[2]+30:
                self.dirt_spots.remove(d)
                self.blink()
                return True
        if self.collide_point(*touch.pos) and self.mode != "sleeping" and math.hypot(touch.x-self.pos_x, touch.y-self.pos_y) < 100:
            if self.mode == "charging":
                self.set_status("Не мешай заряжаться!")
            else:
                self.react()
            return True
        return super().on_touch_down(touch)

    def react(self):
        self.say(random.choice(["Бип-буп!", "Мне щекотно!", "Ещё разок!", "Осторожнее!", "Я в порядке!"]))
        self.jump_offset = 0
        (Animation(jump_offset=60, duration=0.15) + Animation(jump_offset=0, duration=0.3, transition="bounce")).start(self)
        self.blink()

    def blink(self):
        self.blink_state = 0
        Clock.schedule_once(lambda dt: setattr(self, "blink_state", 1), 0.1)

    def say(self, message):
        self.set_status(message)
        if HAS_TTS:
            try:
                tts.speak(message)
            except Exception:
                pass

    def set_status(self, message):
        app = App.get_running_app()
        if app:
            app.status_label.text = message

    def check_shake(self):
        if not HAS_TTS:
            return
        try:
            acc = accelerometer.acceleration
            if acc and acc != (0, 0, 0):
                if (abs(acc[0]-self.last_accel[0]) > 15 or abs(acc[1]-self.last_accel[1]) > 15) and self.mode == "normal":
                    self.mode = "dizzy"
                    self.say("Хватит трясти меня!")
                    Clock.schedule_once(lambda dt: setattr(self, "mode", "normal") if self.mode == "dizzy" else None, 4)
                self.last_accel = acc
        except Exception:
            pass

    def start_game(self):
        if self.mode in ("sleeping", "charging"):
            self.set_status("Сначала приведи меня в норму!")
            return
        self.mode, self.game_timer, self.spawn_timer, self.items = "playing", 20.0, 0.0, []
        self.say("Игра началась! Лови батарейки и избегай мусора.")

    def end_game(self):
        self.mode = "normal"
        self.items = []
        self.say(f"Игра окончена! Опыт: {self.score}")


class DroidApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        top = BoxLayout(size_hint_y=0.12, spacing=5)
        self.lbl_bat = Label(text="BAT: 100%", font_size=16, color=(0,1,0,1))
        self.lbl_oil = Label(text="OIL: 100%", font_size=16, color=(1,0.8,0,1))
        self.lbl_score = Label(text="XP: 0", font_size=16, color=(0,1,1,1))
        for widget in (self.lbl_bat, self.lbl_oil, self.lbl_score):
            top.add_widget(widget)
        root.add_widget(top)
        self.droid = MiniDroid()
        root.add_widget(self.droid)
        panel = BoxLayout(orientation="vertical", size_hint_y=0.28, spacing=5, padding=5)
        self.status_label = Label(text="Привет! Я твой дроид. Сотри с меня пыль!", font_size=15, size_hint_y=0.42)
        panel.add_widget(self.status_label)
        row = BoxLayout(spacing=5)
        for title, callback, color in (
            ("ЗАРЯДКА", self.charge, (0.2,0.6,0.2,1)),
            ("СОН / БОДРСТВОВАНИЕ", self.toggle_sleep, (0.3,0.3,0.6,1)),
            ("МАСЛО", self.feed, (0.6,0.4,0.1,1)),
        ):
            button = Button(text=title, background_color=color, font_size=13)
            button.bind(on_press=callback)
            row.add_widget(button)
        panel.add_widget(row)
        self.btn_play = Button(text="ИГРАТЬ", background_color=(0.8,0.1,0.1,1), font_size=14)
        self.btn_play.bind(on_press=lambda *_: self.droid.start_game())
        panel.add_widget(self.btn_play)
        root.add_widget(panel)
        return root

    def charge(self, *_):
        if self.droid.mode == "sleeping":
            self.droid.set_status("Сначала разбуди меня.")
        else:
            self.droid.mode = "charging"
            self.droid.say("Подключаюсь к зарядке.")

    def toggle_sleep(self, *_):
        self.droid.mode = "normal" if self.droid.mode == "sleeping" else "sleeping"
        self.droid.say("Проснулся! Доброе утро." if self.droid.mode == "normal" else "Ухожу в спящий режим...")

    def feed(self, *_):
        if self.droid.mode == "sleeping":
            return
        if self.droid.oil >= 100:
            self.droid.say("Я не голоден!")
        else:
            self.droid.oil = min(100, self.droid.oil + 30)
            self.droid.say("Ммм, вкусное масло!")

    def update_ui(self):
        d = self.droid
        self.lbl_bat.text = f"BAT: {int(d.battery)}%"
        self.lbl_bat.color = (1,0,0,1) if d.battery < 20 else (0,1,0,1)
        self.lbl_oil.text = f"OIL: {int(d.oil)}%"
        self.lbl_oil.color = (1,0,0,1) if d.oil < 20 else (1,0.8,0,1)
        self.lbl_score.text = f"XP: {int(d.score)}"
        self.btn_play.disabled = d.mode == "playing"
        if d.mode == "playing":
            self.status_label.text = f"Игра! Время: {int(d.game_timer)} сек"

    def on_touch_move(self, touch):
        d = self.droid
        if d.mode == "playing":
            d.pos_x = max(60, min(max(60, d.width-60), touch.x))
        elif touch.y > d.height and d.mode not in ("sleeping", "charging"):
            d.pos_x = max(60, min(max(60, d.width-60), touch.x))
            d.pos_y = max(100, min(max(100, d.height-100), touch.y))
        return super().on_touch_move(touch)


if __name__ == "__main__":
    DroidApp().run()
