"""
Space Shooter - Kivy Game
Controls: Touch/Click to move ship, auto-fires bullets
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle, Triangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
import random
import math

# Window size (for desktop testing)
Window.size = (400, 700)


class GameObject:
    """Base class for all game objects"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alive = True

    def get_rect(self):
        return (self.x, self.y, self.width, self.height)

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50)
        self.speed = 300
        self.target_x = x
        self.shoot_cooldown = 0
        self.shoot_interval = 0.25  # seconds between shots
        self.lives = 3
        self.invincible = 0  # invincibility frames after hit

    def move_toward_target(self, dt):
        dx = self.target_x - (self.x + self.width / 2)
        if abs(dx) > 5:
            self.x += math.copysign(min(self.speed * dt, abs(dx)), dx)
        # Clamp to screen
        self.x = max(0, min(Window.width - self.width, self.x))

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def update(self, dt):
        self.move_toward_target(dt)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invincible > 0:
            self.invincible -= dt


class Bullet(GameObject):
    def __init__(self, x, y, speed=500, enemy=False):
        super().__init__(x, y, 6, 18)
        self.speed = speed
        self.enemy = enemy

    def update(self, dt):
        if self.enemy:
            self.y -= self.speed * dt
        else:
            self.y += self.speed * dt
        if self.y > Window.height + 20 or self.y < -20:
            self.alive = False


class Enemy(GameObject):
    def __init__(self, x, y, enemy_type=1):
        size = 40 if enemy_type == 1 else 55
        super().__init__(x, y, size, size)
        self.enemy_type = enemy_type
        self.speed = random.randint(80, 160)
        self.points = enemy_type * 10
        self.health = enemy_type
        self.shoot_timer = random.uniform(1.5, 4.0)
        self.drift = random.choice([-1, 1]) * random.uniform(20, 60)

    def update(self, dt):
        self.y -= self.speed * dt
        self.x += self.drift * dt
        # Bounce off walls
        if self.x < 0 or self.x + self.width > Window.width:
            self.drift *= -1
        if self.y < -self.height:
            self.alive = False
        self.shoot_timer -= dt

    def should_shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(2.0, 5.0)
            return True
        return False


class Star:
    """Background star for parallax scrolling"""
    def __init__(self):
        self.reset()

    def reset(self, top=False):
        self.x = random.uniform(0, Window.width)
        self.y = Window.height + 5 if top else random.uniform(0, Window.height)
        self.speed = random.uniform(50, 200)
        self.size = random.uniform(1, 3)
        self.brightness = random.uniform(0.4, 1.0)

    def update(self, dt):
        self.y -= self.speed * dt
        if self.y < -5:
            self.reset(top=True)


class Explosion:
    """Simple particle explosion effect"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0.4
        self.alive = True

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False


class SpaceShooterGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset_game()
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self.bind(on_touch_down=self.on_touch_down_event)
        self.bind(on_touch_move=self.on_touch_move_event)

    def reset_game(self):
        cx = Window.width / 2 - 25
        self.player = Player(cx, 60)
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.stars = [Star() for _ in range(60)]
        self.explosions = []
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.spawn_interval = 1.8
        self.game_over = False
        self.paused = False
        self.level_up_timer = 0

    def on_touch_down_event(self, widget, touch):
        if self.game_over:
            self.reset_game()
            return
        self.player.target_x = touch.x - self.player.width / 2

    def on_touch_move_event(self, widget, touch):
        self.player.target_x = touch.x - self.player.width / 2

    def spawn_enemy(self):
        x = random.uniform(10, Window.width - 60)
        y = Window.height + 20
        enemy_type = 1 if random.random() > 0.3 else 2
        self.enemies.append(Enemy(x, y, enemy_type))

    def update(self, dt):
        if self.game_over:
            self.draw()
            return

        # Update stars
        for star in self.stars:
            star.update(dt)

        # Update player
        self.player.update(dt)

        # Auto shoot
        if self.player.can_shoot():
            bx = self.player.x + self.player.width / 2 - 3
            by = self.player.y + self.player.height
            self.bullets.append(Bullet(bx, by))
            self.player.shoot_cooldown = self.player.shoot_interval

        # Spawn enemies
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = self.spawn_interval

        # Level up every 200 points
        new_level = self.score // 200 + 1
        if new_level > self.level:
            self.level = new_level
            self.spawn_interval = max(0.6, 1.8 - (self.level - 1) * 0.15)
            self.level_up_timer = 2.0

        if self.level_up_timer > 0:
            self.level_up_timer -= dt

        # Update bullets
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        # Update enemies & enemy shooting
        for e in self.enemies:
            e.update(dt)
            if e.should_shoot() and e.alive:
                bx = e.x + e.width / 2 - 3
                by = e.y
                self.enemy_bullets.append(Bullet(bx, by, speed=250, enemy=True))

        self.enemies = [e for e in self.enemies if e.alive]

        # Update enemy bullets
        for b in self.enemy_bullets:
            b.update(dt)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        # Update explosions
        for ex in self.explosions:
            ex.update(dt)
        self.explosions = [ex for ex in self.explosions if ex.alive]

        # Collision: player bullets vs enemies
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.alive and enemy.alive and bullet.collides_with(enemy):
                    bullet.alive = False
                    enemy.health -= 1
                    if enemy.health <= 0:
                        enemy.alive = False
                        self.score += enemy.points
                        self.explosions.append(Explosion(enemy.x + enemy.width / 2, enemy.y + enemy.height / 2))

        # Collision: enemy bullets vs player
        if self.player.invincible <= 0:
            for bullet in self.enemy_bullets[:]:
                if bullet.alive and bullet.collides_with(self.player):
                    bullet.alive = False
                    self.player.lives -= 1
                    self.player.invincible = 1.5
                    self.explosions.append(Explosion(self.player.x + 25, self.player.y + 25))
                    if self.player.lives <= 0:
                        self.game_over = True

        # Collision: enemies vs player
        if self.player.invincible <= 0:
            for enemy in self.enemies[:]:
                if enemy.alive and enemy.collides_with(self.player):
                    enemy.alive = False
                    self.player.lives -= 1
                    self.player.invincible = 1.5
                    self.explosions.append(Explosion(self.player.x + 25, self.player.y + 25))
                    if self.player.lives <= 0:
                        self.game_over = True

        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.02, 0.02, 0.12, 1)
            Rectangle(pos=(0, 0), size=(Window.width, Window.height))

            # Stars
            for star in self.stars:
                Color(star.brightness, star.brightness, 1, star.brightness)
                Ellipse(pos=(star.x, star.y), size=(star.size, star.size))

            # Player ship (triangle shape)
            if not self.game_over:
                alpha = 0.4 if self.player.invincible > 0 and int(self.player.invincible * 10) % 2 == 0 else 1.0
                px, py = self.player.x, self.player.y
                pw, ph = self.player.width, self.player.height
                # Body
                Color(0.2, 0.6, 1.0, alpha)
                Triangle(points=[
                    px + pw / 2, py + ph,
                    px, py,
                    px + pw, py
                ])
                # Cockpit
                Color(0.6, 0.9, 1.0, alpha)
                Ellipse(pos=(px + pw / 2 - 8, py + ph / 3), size=(16, 20))
                # Engine glow
                Color(1.0, 0.5, 0.1, alpha * 0.8)
                Ellipse(pos=(px + pw / 2 - 6, py - 10), size=(12, 14))

            # Player bullets
            Color(0.4, 1.0, 0.4, 1)
            for b in self.bullets:
                Rectangle(pos=(b.x, b.y), size=(b.width, b.height))

            # Enemy bullets
            Color(1.0, 0.3, 0.3, 1)
            for b in self.enemy_bullets:
                Rectangle(pos=(b.x, b.y), size=(b.width, b.height))

            # Enemies
            for e in self.enemies:
                if e.enemy_type == 1:
                    Color(0.9, 0.2, 0.8, 1)
                    # Body
                    Ellipse(pos=(e.x + 5, e.y + 5), size=(e.width - 10, e.height - 10))
                    Color(1.0, 0.5, 0.9, 1)
                    Ellipse(pos=(e.x + 12, e.y + 12), size=(16, 16))
                else:
                    Color(1.0, 0.4, 0.1, 1)
                    Rectangle(pos=(e.x, e.y), size=(e.width, e.height))
                    Color(1.0, 0.8, 0.2, 1)
                    Ellipse(pos=(e.x + 10, e.y + 10), size=(e.width - 20, e.height - 20))

            # Explosions
            for ex in self.explosions:
                progress = 1 - (ex.timer / 0.4)
                radius = 30 * progress
                Color(1.0, 0.6, 0.1, 1 - progress)
                Ellipse(pos=(ex.x - radius, ex.y - radius), size=(radius * 2, radius * 2))
                Color(1.0, 1.0, 0.3, (1 - progress) * 0.7)
                inner_r = radius * 0.5
                Ellipse(pos=(ex.x - inner_r, ex.y - inner_r), size=(inner_r * 2, inner_r * 2))

            # HUD - Score
            Color(1, 1, 1, 1)

        # Score label
        if not hasattr(self, '_score_label'):
            self._score_label = Label(
                text='', font_size=20, bold=True,
                color=(0.4, 1.0, 0.4, 1),
                pos=(10, Window.height - 35), size=(200, 30)
            )
            self._lives_label = Label(
                text='', font_size=20, bold=True,
                color=(1.0, 0.4, 0.4, 1),
                pos=(Window.width - 130, Window.height - 35), size=(120, 30)
            )
            self._level_label = Label(
                text='', font_size=18,
                color=(0.8, 0.8, 1.0, 1),
                pos=(Window.width / 2 - 60, Window.height - 35), size=(120, 30)
            )
            self._levelup_label = Label(
                text='', font_size=28, bold=True,
                color=(1.0, 1.0, 0.2, 1),
                pos=(Window.width / 2 - 100, Window.height / 2), size=(200, 40)
            )
            self._gameover_label = Label(
                text='', font_size=32, bold=True,
                color=(1.0, 0.2, 0.2, 1),
                pos=(Window.width / 2 - 130, Window.height / 2 + 20), size=(260, 50)
            )
            self._restart_label = Label(
                text='', font_size=18,
                color=(1.0, 1.0, 1.0, 0.8),
                pos=(Window.width / 2 - 130, Window.height / 2 - 30), size=(260, 30)
            )
            self.add_widget(self._score_label)
            self.add_widget(self._lives_label)
            self.add_widget(self._level_label)
            self.add_widget(self._levelup_label)
            self.add_widget(self._gameover_label)
            self.add_widget(self._restart_label)

        self._score_label.text = f'Score: {self.score}'
        self._lives_label.text = '❤ ' * self.player.lives
        self._level_label.text = f'Level {self.level}'

        if self.level_up_timer > 0 and not self.game_over:
            self._levelup_label.text = f'LEVEL {self.level}!'
        else:
            self._levelup_label.text = ''

        if self.game_over:
            self._gameover_label.text = 'GAME OVER'
            self._restart_label.text = f'Score: {self.score} — Tap to restart'
        else:
            self._gameover_label.text = ''
            self._restart_label.text = ''


class SpaceShooterApp(App):
    def build(self):
        self.title = 'Space Shooter'
        game = SpaceShooterGame()
        game.size = Window.size
        return game


if __name__ == '__main__':
    SpaceShooterApp().run()