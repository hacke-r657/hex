from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math
import json
from pathlib import Path

# ------------------------------------------------------------
# HEX Survival Prototype
# ------------------------------------------------------------

random.seed(7)

app = Ursina()
window.title = 'HEX'
window.borderless = False
window.fps_counter.enabled = True
window.exit_button.visible = False
window.fullscreen = False
window.color = color.rgba(20, 25, 30, 255)

# -------------------------
# Save / Load
# -------------------------
SAVE_PATH = Path('save_data.json')

inventory = {'wood': 0, 'stone': 0, 'food': 0, 'crystal': 0}
stats = {'health': 100, 'hunger': 100, 'thirst': 100, 'stamina': 100}
resources = []
enemies = []
structures = []


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def save_game():
    data = {
        'inventory': inventory,
        'stats': stats,
        'player_position': list(player.position),
    }
    SAVE_PATH.write_text(json.dumps(data), encoding='utf-8')


def load_game():
    if SAVE_PATH.exists():
        try:
            data = json.loads(SAVE_PATH.read_text(encoding='utf-8'))
            for key, value in data.get('inventory', {}).items():
                inventory[key] = value
            for key, value in data.get('stats', {}).items():
                stats[key] = value
            return data.get('player_position', [0, 2, -5])
        except Exception:
            pass
    return [0, 2, -5]


# -------------------------
# Lighting and atmosphere
# -------------------------
Sky(color=color.rgb(110, 150, 200))
scene.fog_density = 0.015
scene.fog_color = color.rgb(120, 160, 190)
scene.fog_start = 18
scene.fog_end = 100

AmbientLight(color=color.rgba(160, 170, 190, 0.6))
sun = DirectionalLight(color=color.rgb(255, 230, 200), shadows=True)
sun.rotation = (30, -20, 0)

# -------------------------
# Player
# -------------------------
player = FirstPersonController()
player.speed = 5
player.gravity = 0.7
player.jump_height = 1.6
player.cursor.color = color.rgb(110, 220, 255)
player.max_stamina = 100
player.stamina = 100
player.is_sprinting = False
player.is_crouching = False
player.head_bob = 0
player.position = tuple(load_game())

# -------------------------
# Ground and terrain
# -------------------------
Entity(
    model='plane',
    shader='lit_with_shadows_shader',
    scale=(180, 1, 180),
    texture='grass',
    texture_scale=(60, 60),
    collider='box',
    color=color.rgb(130, 160, 110)
)

Entity(
    model='plane',
    shader='lit_with_shadows_shader',
    position=(0, -0.08, 0),
    scale=(200, 1, 200),
    color=color.rgb(45, 55, 42)
)

# -------------------------
# Helper functions
# -------------------------
def create_tree(x, z, scale=1):
    trunk = Entity(
        model='cube',
        shader='lit_with_shadows_shader',
        position=(x, 1.3 * scale, z),
        scale=(0.45 * scale, 2.6 * scale, 0.45 * scale),
        color=color.rgb(97, 62, 34),
        collider='box'
    )
    Entity(
        model='sphere',
        shader='lit_with_shadows_shader',
        position=(x, 2.8 * scale, z),
        scale=(1.8 * scale, 1.5 * scale, 1.8 * scale),
        color=color.rgb(40, 110, 55)
    )
    Entity(
        model='sphere',
        shader='lit_with_shadows_shader',
        position=(x + 0.8 * scale, 2.6 * scale, z + 0.2 * scale),
        scale=(1.3 * scale, 1.1 * scale, 1.3 * scale),
        color=color.rgb(52, 130, 62)
    )
    Entity(
        model='sphere',
        shader='lit_with_shadows_shader',
        position=(x - 0.6 * scale, 2.5 * scale, z - 0.3 * scale),
        scale=(1.2 * scale, 1.2 * scale, 1.2 * scale),
        color=color.rgb(32, 95, 50)
    )
    return trunk


def create_rock(x, z, scale=1):
    rock = Entity(
        model='sphere',
        shader='lit_with_shadows_shader',
        position=(x, 0.45 * scale, z),
        scale=(random.uniform(0.5, 1.2) * scale, random.uniform(0.4, 1.0) * scale, random.uniform(0.5, 1.1) * scale),
        rotation=(random.randint(0, 180), random.randint(0, 180), random.randint(0, 180)),
        color=color.rgb(110, 110, 120),
        collider='box',
    )
    return rock


def create_crystal(x, z, scale=1):
    crystal = Entity(
        model='cube',
        shader='lit_with_shadows_shader',
        position=(x, 0.9 * scale, z),
        scale=(0.4 * scale, random.uniform(1.2, 2.4) * scale, 0.4 * scale),
        color=random.choice([
            color.rgb(90, 210, 255),
            color.rgb(160, 90, 255),
            color.rgb(90, 255, 210),
            color.rgb(255, 120, 200),
        ]),
        collider='box',
    )
    crystal.kind = 'crystal'
    crystal.shimmer = random.random() * 10
    return crystal


def create_resource(kind, x, z, color_value):
    res = Entity(
        model='cube',
        shader='lit_with_shadows_shader',
        position=(x, 0.5, z),
        scale=(0.7, 0.7, 0.7),
        color=color_value,
        collider='box',
    )
    res.kind = kind
    resources.append(res)
    return res


def create_enemy(x, z):
    enemy = Entity(
        model='cube',
        shader='lit_with_shadows_shader',
        position=(x, 0.8, z),
        scale=(0.9, 1.6, 0.9),
        color=color.rgb(170, 60, 60),
        collider='box',
    )
    enemy.kind = 'enemy'
    enemy.health = 40
    enemy.speed = random.uniform(1.5, 2.5)
    enemy.wander_timer = 0
    enemies.append(enemy)
    return enemy


def create_structure(x, z, kind='wall'):
    piece = Entity(
        model='cube',
        shader='lit_with_shadows_shader',
        position=(x, 1.2, z),
        scale=(1.5, 2.4, 1.5),
        color=color.rgb(90, 100, 115),
        collider='box',
    )
    piece.kind = kind
    structures.append(piece)
    return piece


def nearest_resource():
    best = None
    best_distance = 999
    for item in resources:
        d = distance(player.position, item.position)
        if d < best_distance:
            best = item
            best_distance = d
    return best, best_distance


def nearest_enemy():
    best = None
    best_distance = 999
    for enemy in enemies:
        d = distance(player.position, enemy.position)
        if d < best_distance:
            best = enemy
            best_distance = d
    return best, best_distance


def update_hud():
    inv_text.text = (
        f"WOOD: {inventory['wood']}   "
        f"STONE: {inventory['stone']}   "
        f"FOOD: {inventory['food']}   "
        f"CRYSTAL: {inventory['crystal']}"
    )

    stat_text.text = (
        f"HEALTH: {int(stats['health'])}%   "
        f"HUNGER: {int(stats['hunger'])}%   "
        f"THIRST: {int(stats['thirst'])}%   "
        f"STAMINA: {int(stats['stamina'])}%"
    )

    nearest, dist = nearest_resource()
    if nearest and dist < 2.6:
        prompt.text = f"Press E to collect {nearest.kind.upper()}"
    else:
        nearest_enemy_obj, enemy_dist = nearest_enemy()
        if nearest_enemy_obj and enemy_dist < 2.5:
            prompt.text = 'Press Q to attack nearby enemy'
        else:
            prompt.text = 'Explore the world'

# -------------------------
# World generation
# -------------------------
for _ in range(80):
    x = random.uniform(-60, 60)
    z = random.uniform(-60, 60)
    if abs(x) < 12 and abs(z) < 12:
        continue
    create_tree(x, z, random.uniform(0.8, 1.6))

for _ in range(90):
    x = random.uniform(-65, 65)
    z = random.uniform(-65, 65)
    if abs(x) < 10 and abs(z) < 10:
        continue
    create_rock(x, z, random.uniform(0.8, 1.6))

for _ in range(28):
    x = random.uniform(-50, 50)
    z = random.uniform(-50, 50)
    if abs(x) < 8 and abs(z) < 8:
        continue
    create_crystal(x, z, random.uniform(0.8, 1.5))

# Add initial resources around player
for i in range(12):
    angle = i * (360 / 12)
    r = random.uniform(8, 16)
    x = math.cos(math.radians(angle)) * r
    z = math.sin(math.radians(angle)) * r
    create_resource('wood', x, z, color.rgb(110, 80, 40))
    create_resource('stone', x + 2, z + 1, color.rgb(120, 120, 130))
    create_resource('crystal', x - 2, z + 2, color.rgb(90, 200, 255))

# Spawn enemies
for _ in range(6):
    x = random.uniform(-45, 45)
    z = random.uniform(-45, 45)
    if abs(x) < 12 and abs(z) < 12:
        continue
    create_enemy(x, z)

# Camp and fire
camp = Entity(model='cube', shader='lit_with_shadows_shader', position=(0, 1.5, 12), scale=(4, 3, 4), color=color.rgb(60, 70, 80), collider='box')
fire = Entity(model='sphere', shader='lit_with_shadows_shader', position=(0, 2.1, 12), scale=(1.3, 1.3, 1.3), color=color.rgb(255, 120, 50))

# -------------------------
# HUD and logo
# -------------------------
logo_panel = Entity(parent=camera.ui, model='quad', color=color.rgba(10, 15, 25, 180), scale=(0.35, 0.11, 1), position=(-0.76, 0.43))
Text(parent=camera.ui, text='⬡', position=(-0.87, 0.44), scale=2.0, color=color.rgb(90, 220, 255))
Text(parent=camera.ui, text='HEX', position=(-0.70, 0.445), scale=1.6, color=color.rgb(230, 240, 255))
Text(parent=camera.ui, text='SURVIVAL', position=(-0.69, 0.398), scale=0.55, color=color.rgba(180, 215, 230, 220))
inv_text = Text(parent=camera.ui, text='', position=(-0.92, 0.20), scale=0.85, color=color.rgb(240, 245, 255))
stat_text = Text(parent=camera.ui, text='', position=(0.55, 0.40), scale=0.75, color=color.rgb(160, 225, 255), origin=(0, 0))
prompt = Text(parent=camera.ui, text='', position=(0, -0.38), scale=1, color=color.rgb(255, 240, 180))

# -------------------------
# Input
# -------------------------
def input(key):
    if key == 'escape':
        application.quit()

    if key == 'e':
        nearest, dist = nearest_resource()
        if nearest and dist < 2.6:
            inventory[nearest.kind] = inventory.get(nearest.kind, 0) + 1
            destroy(nearest)
            resources.remove(nearest)
            update_hud()
            save_game()

    if key == 'c':
        if inventory['wood'] >= 3 and inventory['stone'] >= 2:
            inventory['wood'] -= 3
            inventory['stone'] -= 2
            inventory['food'] += 1
            update_hud()
            save_game()

    if key == 'h':
        if inventory['food'] >= 1:
            inventory['food'] -= 1
            stats['health'] = clamp(stats['health'] + 25, 0, 100)
            stats['hunger'] = clamp(stats['hunger'] + 10, 0, 100)
            stats['thirst'] = clamp(stats['thirst'] + 10, 0, 100)
            update_hud()
            save_game()

    if key == 'b':
        if inventory['wood'] >= 2 and inventory['stone'] >= 1:
            inventory['wood'] -= 2
            inventory['stone'] -= 1
            pos = player.position + Vec3(2, 0, 0)
            create_structure(pos.x, pos.z, 'wall')
            update_hud()
            save_game()

    if key == 'q':
        enemy, dist = nearest_enemy()
        if enemy and dist < 2.2:
            enemy.health -= 20
            if enemy.health <= 0:
                destroy(enemy)
                enemies.remove(enemy)
                inventory['food'] += 1
            update_hud()
            save_game()

    if key == 'r':
        if stats['health'] <= 0:
            stats['health'] = 100
            stats['hunger'] = 100
            stats['thirst'] = 100
            stats['stamina'] = 100
            player.position = (0, 2, -5)
            save_game()

# -------------------------
# Survival, movement, enemy AI
# -------------------------
def handle_movement():
    moving = held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']
    sprinting = held_keys['shift'] and moving and stats['stamina'] > 0 and not player.is_crouching

    if sprinting:
        player.speed = 9
        player.is_sprinting = True
        stats['stamina'] -= 20 * time.dt
    else:
        player.speed = 5
        player.is_sprinting = False
        stats['stamina'] += 14 * time.dt

    if held_keys['control']:
        player.is_crouching = True
        player.height = lerp(player.height, 1.2, 8 * time.dt)
    else:
        player.is_crouching = False
        player.height = lerp(player.height, 2.0, 8 * time.dt)

    stats['stamina'] = clamp(stats['stamina'], 0, 100)

    if moving and player.grounded:
        player.head_bob += time.dt * 12
        camera.y = 1.65 + math.sin(player.head_bob) * 0.04
    else:
        camera.y = lerp(camera.y, 1.65, 5 * time.dt)


def handle_survival():
    stats['hunger'] -= 0.7 * time.dt
    stats['thirst'] -= 1.1 * time.dt

    if stats['hunger'] < 20 or stats['thirst'] < 20:
        stats['health'] -= 3.5 * time.dt

    if stats['hunger'] > 60 and stats['thirst'] > 60 and stats['health'] < 100:
        stats['health'] += 0.8 * time.dt

    stats['health'] = clamp(stats['health'], 0, 100)
    stats['hunger'] = clamp(stats['hunger'], 0, 100)
    stats['thirst'] = clamp(stats['thirst'], 0, 100)


def update_enemies():
    for enemy in enemies:
        enemy.wander_timer -= time.dt
        if enemy.wander_timer <= 0:
            enemy.rotation_y = random.uniform(0, 360)
            enemy.wander_timer = random.uniform(1.5, 4.0)

        if distance(player.position, enemy.position) < 10:
            direction = (player.position - enemy.position).normalized()
            enemy.position += direction * enemy.speed * time.dt
            enemy.look_at(player.position, 'forward')
        else:
            forward = Vec3(math.sin(math.radians(enemy.rotation_y)), 0, math.cos(math.radians(enemy.rotation_y)))
            enemy.position += forward * enemy.speed * time.dt * 0.4

        if distance(player.position, enemy.position) < 1.8:
            stats['health'] -= 8 * time.dt


def update_day_cycle():
    sun.rotation_y += time.dt * 12
    sun.rotation_x = 30 + math.sin(time.time() * 0.4) * 25


def update():
    handle_movement()
    handle_survival()
    update_enemies()
    update_day_cycle()
    update_hud()

    if stats['health'] <= 0:
        prompt.text = 'You died. Press R to respawn'

    save_game()

# -------------------------
# Run
# -------------------------
update_hud()
app.run()
