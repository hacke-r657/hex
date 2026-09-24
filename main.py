from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import math
import random
from pathlib import Path

# HEX Survival - expanded prototype
random.seed(7)
app = Ursina()
window.title = 'HEX - Survival'
window.borderless = False
window.fps_counter.enabled = True
window.exit_button.visible = False
window.color = color.rgb(22, 30, 42)

SAVE_PATH = Path('save_data.json')
WORLD_SEED = 7
inventory = {'wood': 0, 'stone': 0, 'food': 2, 'crystal': 0, 'water': 1, 'arrows': 0}
stats = {'health': 100, 'hunger': 100, 'thirst': 100, 'stamina': 100, 'temperature': 70}
resources, enemies, animals, structures, rain_drops = [], [], [], [], []
selected_slot = 0
selected_tool = 'hands'
paused = False
night_vision = False
weather = 'clear'
weather_timer = 30
save_timer = 0
world_clock = 8.0


def clamp(value, low, high):
    return max(low, min(high, value))


def load_game():
    if not SAVE_PATH.exists():
        return [0, 2, -5]
    try:
        data = json.loads(SAVE_PATH.read_text(encoding='utf-8'))
        inventory.update(data.get('inventory', {}))
        stats.update(data.get('stats', {}))
        return data.get('player_position', [0, 2, -5])
    except (OSError, ValueError, TypeError):
        return [0, 2, -5]


def save_game():
    try:
        SAVE_PATH.write_text(json.dumps({
            'inventory': inventory,
            'stats': stats,
            'player_position': list(player.position),
        }, indent=2), encoding='utf-8')
    except OSError:
        pass


# Atmosphere
Sky()
scene.fog_density = 0.012
scene.fog_start, scene.fog_end = 20, 115
scene.fog_color = color.rgb(120, 160, 190)
ambient = AmbientLight(color=color.rgba(140, 145, 165, 0.55))
sun = DirectionalLight(color=color.rgb(255, 235, 200), shadows=True)
sun.look_at(Vec3(1, -1, -1))

# World
Entity(model='plane', scale=(180, 1, 180), texture='grass', texture_scale=(60, 60), color=color.rgb(130, 160, 110), collider='box')
Entity(model='plane', y=-.08, scale=(200, 1, 200), color=color.rgb(45, 55, 42))
water = Entity(model='cube', position=(24, -.08, 18), scale=(20, .12, 14), color=color.rgba(40, 145, 210, 190), collider='box')


def tree(x, z, size=1):
    Entity(model='cube', position=(x, 1.25 * size, z), scale=(.42 * size, 2.5 * size, .42 * size), color=color.rgb(97, 62, 34), collider='box')
    Entity(model='sphere', position=(x, 2.75 * size, z), scale=1.8 * size, color=color.rgb(38, 105, 52))
    Entity(model='sphere', position=(x + .65 * size, 2.55 * size, z), scale=1.2 * size, color=color.rgb(55, 130, 63))


def rock(x, z, size=1):
    Entity(model='sphere', position=(x, .35 * size, z), scale=(1.1 * size, .7 * size, .9 * size), rotation=(0, random.randrange(360), 0), color=color.rgb(105, 110, 120), collider='box')


def resource(kind, x, z, tint):
    item = Entity(model='cube', position=(x, .5, z), scale=(.65, .65, .65), color=tint, collider='box')
    item.kind = kind
    resources.append(item)
    return item


def crystal(x, z):
    return resource('crystal', x, z, random.choice([color.azure, color.violet, color.cyan, color.magenta]))


def enemy(x, z):
    mob = Entity(model='cube', position=(x, .8, z), scale=(.9, 1.6, .9), color=color.rgb(170, 60, 60), collider='box')
    mob.health, mob.speed, mob.wander = 50, random.uniform(1.4, 2.3), 0
    enemies.append(mob)


def animal(x, z):
    deer = Entity(model='cube', position=(x, .65, z), scale=(1.3, 1.0, .65), color=color.rgb(150, 105, 70), collider='box')
    deer.health, deer.wander = 25, 0
    animals.append(deer)


def build_piece(position, kind='wall', rotation=0):
    if kind == 'floor':
        piece = Entity(model='cube', position=position, scale=(2.5, .15, 2.5), color=color.rgb(115, 90, 65), collider='box')
    elif kind == 'campfire':
        piece = Entity(model='sphere', position=(position[0], .5, position[2]), scale=1.0, color=color.orange)
    else:
        piece = Entity(model='cube', position=(position[0], 1.2, position[2]), scale=(2.5, 2.4, .15), rotation_y=rotation, color=color.rgb(100, 86, 70), collider='box')
    piece.kind = kind
    structures.append(piece)


for _ in range(75):
    x, z = random.uniform(-60, 60), random.uniform(-60, 60)
    if abs(x) > 10 or abs(z) > 10:
        tree(x, z, random.uniform(.8, 1.6))
for _ in range(90):
    x, z = random.uniform(-65, 65), random.uniform(-65, 65)
    if abs(x) > 8 or abs(z) > 8:
        rock(x, z, random.uniform(.7, 1.5))
for _ in range(25):
    crystal(random.uniform(-50, 50), random.uniform(-50, 50))
for i in range(18):
    angle = math.radians(i * 20)
    r = random.uniform(8, 17)
    x, z = math.cos(angle) * r, math.sin(angle) * r
    resource('wood', x, z, color.rgb(110, 80, 40))
    resource('stone', x + 1.8, z + 1, color.rgb(120, 120, 130))
for _ in range(7):
    enemy(random.uniform(-45, 45), random.uniform(-45, 45))
for _ in range(8):
    animal(random.uniform(-40, 40), random.uniform(-40, 40))

# Player
player = FirstPersonController()
player.position = tuple(load_game())
player.speed, player.gravity, player.jump_height = 5, .7, 1.6
player.cursor.color = color.rgb(110, 220, 255)
player.is_sprinting, player.is_crouching, player.head_bob = False, False, 0

# UI
Entity(parent=camera.ui, model='quad', color=color.rgba(10, 15, 25, 190), scale=(.35, .11), position=(-.76, .43))
Text(parent=camera.ui, text='⬡  HEX', position=(-.86, .435), scale=1.55, color=color.rgb(220, 245, 255))
Text(parent=camera.ui, text='SURVIVAL', position=(-.69, .395), scale=.52, color=color.rgb(130, 210, 235))
status_text = Text(parent=camera.ui, position=(-.92, .22), scale=.78)
stats_text = Text(parent=camera.ui, position=(.98, .43), origin=(1, 0), scale=.72, color=color.azure)
hint_text = Text(parent=camera.ui, position=(0, -.40), origin=(0, 0), scale=.9, color=color.yellow)
message_text = Text(parent=camera.ui, position=(0, .30), origin=(0, 0), scale=1.1, color=color.white)
pause_text = Text(parent=camera.ui, text='PAUSED\n\nESC: resume    F5: save', origin=(0, 0), scale=1.5, enabled=False)

# Weather particles
for _ in range(90):
    drop = Entity(parent=scene, model='cube', scale=(.015, .35, .015), color=color.rgba(130, 190, 255, 130), enabled=False)
    rain_drops.append(drop)


def nearest(items):
    if not items:
        return None, 999
    item = min(items, key=lambda obj: distance(player.position, obj.position))
    return item, distance(player.position, item.position)


def hud():
    hotbar = ['wood', 'stone', 'food', 'crystal', 'water', 'arrows']
    status_text.text = '  '.join(f'[{i + 1}] {name.upper()}: {inventory[name]}' for i, name in enumerate(hotbar))
    stats_text.text = f"HP {int(stats['health'])}\nFOOD {int(stats['hunger'])}\nWATER {int(stats['thirst'])}\nSTAM {int(stats['stamina'])}\nTEMP {int(stats['temperature'])}\nTOOL {selected_tool.upper()}"
    item, dist = nearest(resources)
    mob, mob_dist = nearest(enemies)
    if item and dist < 2.7:
        hint_text.text = f'E: collect {item.kind.upper()}'
    elif mob and mob_dist < 2.8:
        hint_text.text = 'Q: attack   F: shoot arrow'
    else:
        hint_text.text = 'C craft food   B build wall   G build floor   T torch/night vision'


def flash(text):
    message_text.text = text
    invoke(setattr, message_text, 'text', '', delay=2)


def collect():
    item, dist = nearest(resources)
    if item and dist < 2.7:
        inventory[item.kind] = inventory.get(item.kind, 0) + 1
        resources.remove(item)
        destroy(item)
        flash(f'+1 {item.kind}')
        save_game()


def attack(damage=20):
    mob, dist = nearest(enemies + animals)
    if mob and dist < 2.8:
        mob.health -= damage
        mob.color = color.white
        invoke(setattr, mob, 'color', color.rgb(170, 60, 60) if mob in enemies else color.rgb(150, 105, 70), delay=.12)
        if mob.health <= 0:
            if mob in enemies:
                enemies.remove(mob)
            else:
                animals.remove(mob)
            destroy(mob)
            inventory['food'] += 1
            flash('+1 food')


def craft():
    if inventory['wood'] >= 3 and inventory['stone'] >= 2:
        inventory['wood'] -= 3
        inventory['stone'] -= 2
        inventory['food'] += 1
        flash('Crafted food ration')
    elif inventory['wood'] >= 2 and inventory['crystal'] >= 1:
        inventory['wood'] -= 2
        inventory['crystal'] -= 1
        inventory['arrows'] += 5
        flash('Crafted 5 arrows')
    else:
        flash('Need 3 wood + 2 stone, or 2 wood + 1 crystal')


def build(kind):
    cost = {'wall': (2, 1), 'floor': (3, 0), 'campfire': (2, 1)}[kind]
    if inventory['wood'] < cost[0] or inventory['stone'] < cost[1]:
        flash('Not enough materials')
        return
    inventory['wood'] -= cost[0]
    inventory['stone'] -= cost[1]
    forward = camera.forward
    p = player.position + Vec3(forward.x * 3, 0, forward.z * 3)
    build_piece(p, kind, player.rotation_y)
    flash(f'Built {kind}')
    save_game()


def eat():
    if inventory['food']:
        inventory['food'] -= 1
        stats['health'] = clamp(stats['health'] + 18, 0, 100)
        stats['hunger'] = clamp(stats['hunger'] + 25, 0, 100)
        flash('Ate food')
    else:
        flash('No food')


def toggle_weather():
    global weather
    weather = 'rain' if weather == 'clear' else 'clear'
    for drop in rain_drops:
        drop.enabled = weather == 'rain'
    flash('Rain started' if weather == 'rain' else 'Rain stopped')


def input(key):
    global selected_slot, selected_tool, paused, night_vision
    if key == 'escape':
        paused = not paused
        pause_text.enabled = paused
        mouse.locked = not paused
    if paused and key not in ('escape', 'f5'):
        return
    if key in ('1', '2', '3', '4', '5', '6'):
        selected_slot = int(key) - 1
        selected_tool = ['wood', 'stone', 'food', 'crystal', 'water', 'arrows'][selected_slot]
    elif key == 'e': collect()
    elif key == 'q': attack()
    elif key == 'f' and inventory['arrows'] > 0:
        inventory['arrows'] -= 1
        attack(35)
    elif key == 'c': craft()
    elif key == 'h': eat()
    elif key == 'b': build('wall')
    elif key == 'g': build('floor')
    elif key == 'n': build('campfire')
    elif key == 'r': toggle_weather()
    elif key == 't':
        night_vision = not night_vision
        flash('Night vision on' if night_vision else 'Night vision off')
    elif key == 'f5': save_game(); flash('Game saved')


def movement():
    moving = any(held_keys[k] for k in ('w', 'a', 's', 'd'))
    sprint = held_keys['shift'] and moving and stats['stamina'] > 0 and not player.is_crouching
    player.speed = 8.5 if sprint else 5
    player.is_sprinting = sprint
    stats['stamina'] += (-22 if sprint else 14) * time.dt
    player.is_crouching = bool(held_keys['control'])
    player.height = lerp(player.height, 1.2 if player.is_crouching else 2, 8 * time.dt)
    if moving and player.grounded:
        player.head_bob += time.dt * (14 if sprint else 9)
        camera.y = 1.65 + math.sin(player.head_bob) * (.045 if sprint else .025)
    else:
        camera.y = lerp(camera.y, 1.65, 6 * time.dt)
    stats['stamina'] = clamp(stats['stamina'], 0, 100)


def survival():
    stats['hunger'] -= .55 * time.dt
    stats['thirst'] -= .8 * time.dt
    cold = player.y < 2 or world_clock < 5 or world_clock > 20
    stats['temperature'] += (-2 if cold else .5) * time.dt
    if distance(player.position, water.position) < 12 and player.y < 3:
        stats['thirst'] = clamp(stats['thirst'] + 4 * time.dt, 0, 100)
    if stats['hunger'] < 15 or stats['thirst'] < 15 or stats['temperature'] < 15:
        stats['health'] -= 2.5 * time.dt
    stats['health'] = clamp(stats['health'], 0, 100)
    stats['hunger'] = clamp(stats['hunger'], 0, 100)
    stats['thirst'] = clamp(stats['thirst'], 0, 100)
    stats['temperature'] = clamp(stats['temperature'], 0, 100)


def ai():
    for mob in enemies:
        d = distance(player.position, mob.position)
        if d < 12:
            mob.position += (player.position - mob.position).normalized() * mob.speed * time.dt
            if d < 1.7:
                stats['health'] -= 7 * time.dt
        else:
            mob.wander -= time.dt
            if mob.wander <= 0:
                mob.rotation_y = random.randrange(360)
                mob.wander = random.uniform(2, 5)
            direction = Vec3(math.sin(math.radians(mob.rotation_y)), 0, math.cos(math.radians(mob.rotation_y)))
            mob.position += direction * mob.speed * .25 * time.dt
    for deer in animals:
        deer.wander -= time.dt
        if deer.wander <= 0:
            deer.rotation_y = random.randrange(360)
            deer.wander = random.uniform(2, 5)
        direction = Vec3(math.sin(math.radians(deer.rotation_y)), 0, math.cos(math.radians(deer.rotation_y)))
        deer.position += direction * .45 * time.dt


def update_weather():
    global weather_timer, weather
    weather_timer -= time.dt
    if weather_timer <= 0:
        weather_timer = random.uniform(25, 50)
        if random.random() < .35:
            toggle_weather()
    if weather == 'rain':
        for drop in rain_drops:
            drop.position = player.position + Vec3(random.uniform(-25, 25), random.uniform(7, 16), random.uniform(-25, 25))
            drop.y -= time.dt * 18
            if drop.y < player.y:
                drop.y = player.y + 14


def update():
    global world_clock, save_timer
    if paused:
        return
    movement()
    survival()
    ai()
    update_weather()
    world_clock = (world_clock + time.dt * .12) % 24
    sun.rotation_y = world_clock * 15
    sun.rotation_x = 25 + math.sin(world_clock / 24 * math.tau) * 35
    night_vision_color = color.rgb(80, 220, 120) if night_vision else color.rgb(120, 160, 190)
    scene.fog_color = night_vision_color
    save_timer += time.dt
    if save_timer > 15:
        save_timer = 0
        save_game()
    if stats['health'] <= 0:
        hint_text.text = 'YOU DIED - press R to respawn'
    hud()


update_hud = hud
hud()
app.run()
