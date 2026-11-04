
# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3
# import hashlib
import os
import json

from werkzeug.security import generate_password_hash, check_password_hash

from database.database import (
    connect_db,
    create_database,
    create_sheet_tables,
    add_excel_sheet_fields,
    view_player_page as db_view_player_page,
    remove_player as db_remove_player
    # get_user_characters as db_get_user_characters
)

app = Flask(__name__)

# temp session verification
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# temp stuff for character sheet
create_database()
create_sheet_tables()
add_excel_sheet_fields()

# Add password storage to existing databases
with connect_db() as conn:
    columns = [
        row[1]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    ]

    if "password_hash" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN password_hash TEXT"
        )


# Character abilities
ABILITIES = (
    'strength',
    'dexterity',
    'constitution',
    'intelligence',
    'wisdom',
    'charisma'
)

SKILLS = {
    'Acrobatics': 'dexterity',
    'Animal Handling': 'wisdom',
    'Arcana': 'intelligence',
    'Athletics': 'strength',
    'Deception': 'charisma',
    'History': 'intelligence',
    'Insight': 'wisdom',
    'Intimidation': 'charisma',
    'Investigation': 'intelligence',
    'Medicine': 'wisdom',
    'Nature': 'intelligence',
    'Perception': 'wisdom',
    'Performance': 'charisma',
    'Persuasion': 'charisma',
    'Religion': 'intelligence',
    'Sleight of Hand': 'dexterity',
    'Stealth': 'dexterity',
    'Survival': 'wisdom'
}


# Character sheet references
SHEET_SECTIONS = {
    'Identity & Appearance': [
        ('gender', 'Gender'),
        ('deity', 'Deity'),
        ('background', 'Background'),
        ('size', 'Size'),
        ('age', 'Age'),
        ('height', 'Height'),
        ('weight', 'Weight'),
        ('hair', 'Hair'),
        ('eyes', 'Eyes'),
        ('portrait_url', 'Portrait URL / reference')
    ],

    'Classes & Advancement': [
        ('experience_points', 'Experience Points'),
        ('class_levels', 'Additional classes / levels'),
        ('hit_dice', 'Hit Dice (e.g. 3d12)'),
        ('proficiency_override', 'Proficiency Bonus Override (optional)')
    ],

    'Combat & Movement': [
        ('initiative_bonus', 'Initiative Bonus'),
        ('speed', 'Walking Speed'),
        ('other_movement', 'Other Movement Modes'),
        ('temp_hp', 'Temporary HP'),
        ('death_successes', 'Death Save Successes (0-3)'),
        ('death_failures', 'Death Save Failures (0-3)'),
        ('armor_worn', 'Armor Worn'),
        ('shield', 'Shield'),
        ('armor_notes', 'Armor / AC Breakdown'),
        ('ammunition', 'Ammunition'),
        ('weapons_spells', 'Weapons & Spells / Attack Details'),
        ('special_attacks', 'Special Attacks'),
        ('special_defenses', 'Special Defenses')
    ],

    'Features & Spellcasting': [
        ('racial_background_features', 'Race / Background / Feats'),
        ('class_features', 'Class Features'),
        ('additional_class_info', 'Additional Class Information'),
        ('spellcasting_ability', 'Spellcasting Ability'),
        ('spell_save_dc', 'Spell Save DC'),
        ('spell_attack_bonus', 'Spell Attack Bonus'),
        ('known_spells', 'Known / Prepared Spells'),
        ('magic_items', 'Magic Items')
    ],

    'Equipment & Wealth': [
        ('copper', 'Copper Pieces (CP)'),
        ('silver', 'Silver Pieces (SP)'),
        ('electrum', 'Electrum Pieces (EP)'),
        ('platinum', 'Platinum Pieces (PP)'),
        ('gems', 'Gems'),
        ('valuables', 'Jewelry / Valuables'),
        ('consumables', 'Consumables'),
        ('equipment_locations', 'Equipment Locations / Containers'),
        ('equipment_weight', 'Equipment Weight Notes'),
        ('encumbrance', 'Encumbrance / Carrying Capacity'),
        ('misc_possessions', 'Miscellaneous Possessions')
    ],

    'Biography & Relationships': [
        ('character_bio', 'Character Biography'),
        ('allies_organizations', 'Allies & Organizations'),
        ('storytelling', 'Storytelling / Background Notes'),
        ('misc_info', 'Miscellaneous Information')
    ]
}


# Character sheet keys
SHEET_KEYS = [
    'gender',
    'deity',
    'background',
    'size',
    'age',
    'height',
    'weight',
    'hair',
    'eyes',
    'portrait_url',
    'experience_points',
    'class_levels',
    'hit_dice',
    'proficiency_override',
    'initiative_bonus',
    'speed',
    'other_movement',
    'temp_hp',
    'death_successes',
    'death_failures',
    'armor_worn',
    'shield',
    'armor_notes',
    'ammunition',
    'weapons_spells',
    'special_attacks',
    'special_defenses',
    'racial_background_features',
    'class_features',
    'additional_class_info',
    'spellcasting_ability',
    'spell_save_dc',
    'spell_attack_bonus',
    'known_spells',
    'magic_items',
    'copper',
    'silver',
    'electrum',
    'platinum',
    'gems',
    'valuables',
    'consumables',
    'equipment_locations',
    'equipment_weight',
    'encumbrance',
    'misc_possessions',
    'character_bio',
    'allies_organizations',
    'storytelling',
    'misc_info'
]


# Numerical values of character sheet stuff
SHEET_NUMERIC = {
    'experience_points',
    'death_successes',
    'death_failures',
    'copper',
    'silver',
    'electrum',
    'platinum',
    'temp_hp',
    'age',
    'speed',
    'initiative_bonus',
    'spell_save_dc',
    'spell_attack_bonus'
}


# Checks number inputs
def integer_field(form, key, minimum, maximum, default=None):
    raw = form.get(key, '')

    if raw == '' and default is not None:
        return default

    try:
        number = int(raw)
    except (ValueError, TypeError):
        abort(400, description='Invalid input: ' + key)

    if not minimum <= number <= maximum:
        abort(400, description='Invalid input: ' + key)

    return number


# Checks text inputs
def text_field(form, key, limit=2000, required=False):
    value = form.get(key, '').strip()

    if len(value) > limit or (required and not value):
        abort(400, description='Invalid input: ' + key)

    return value


# Gets the logged-in user's ID
def current_user_id():
    username = session.get('username')

    if not username:
        abort(401, description='Please log in first.')

    with connect_db() as conn:
        row = conn.execute(
            'SELECT user_id FROM users WHERE username=?',
            (username,)
        ).fetchone()

    if row is None:
        abort(401, description='User not found.')

    return row[0]


# Checks that a character belongs to the logged-in user
def owned_character(conn, character_id, user_id):
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        'SELECT * FROM characters WHERE character_id=? AND user_id=?',
        (character_id, user_id)
    ).fetchone()

    if row is None:
        abort(404, description='Character not found.')

    return row


# Creates or finds the user's personal party
def personal_party_id(conn, user_id):
    row = conn.execute(
        'SELECT party_id FROM parties WHERE dm_user_id=? AND party_name=?',
        (user_id, 'Personal Characters')
    ).fetchone()

    if row:
        return row[0]

    cursor = conn.execute(
        'INSERT INTO parties (party_name, dm_user_id) VALUES (?, ?)',
        ('Personal Characters', user_id)
    )

    party_id = cursor.lastrowid

    conn.execute(
        'INSERT INTO party_members (party_id, user_id) VALUES (?, ?)',
        (party_id, user_id)
    )

    return party_id


# LOGIN
@app.route('/')
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def index():

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template(
                'login.html',
                error='Please enter your username and password.'
            )

        with connect_db() as conn:
            user = conn.execute(
                'SELECT username, password_hash FROM users WHERE username=?',
                (username,)
            ).fetchone()

        if user and user[1] and check_password_hash(user[1], password):
            session.clear()
            session['username'] = user[0]
            return redirect(url_for('main_menu'))

        return render_template(
            'login.html',
            error='Invalid username or password.'
        )

    return render_template('login.html')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(username) < 3 or len(username) > 40:
            return render_template(
                'register.html',
                error='Username must be between 3 and 40 characters.'
            )

        if len(password) < 8:
            return render_template(
                'register.html',
                error='Password must be at least 8 characters.'
            )

        if password != confirm_password:
            return render_template(
                'register.html',
                error='Passwords do not match.'
            )

        password_hash = generate_password_hash(password)

        try:
            with connect_db() as conn:
                conn.execute(
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (username, password_hash)
                )

        except sqlite3.IntegrityError:
            return render_template(
                'register.html',
                error='That username is already taken.'
            )

        session.clear()
        session['username'] = username

        return redirect(url_for('main_menu'))

    return render_template('register.html')


# LOGOUT
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# MAIN MENU
@app.route('/main', methods=['GET'])
def main_menu():

    user_id = current_user_id()

    with connect_db() as conn:
        characters = conn.execute(
            '''SELECT character_id, character_name,
                      character_class, character_level
               FROM characters
               WHERE user_id=?
               ORDER BY character_id DESC''',
            (user_id,)
        ).fetchall()

    return render_template(
        'main.html',
        characters=characters
    )


# CHARACTER CREATOR PAGE
@app.route('/character-creator', methods=['GET'])
def character_creator():
    current_user_id()
    return render_template('character-creator.html')


# VIEW A PLAYER IN A PARTY
@app.route('/party/<int:party_id>/player/<int:player_id>', methods=['GET'])
def dm_view_player(party_id, player_id):

    dm_user_id = current_user_id()

    try:
        result = db_view_player_page(
            dm_user_id,
            party_id,
            player_id
        )

        player = result["player"]
        characters = result["characters"]

        return jsonify({
            "player": {
                "user_id": player[0],
                "username": player[1]
            },
            "characters": [
                {
                    "character_id": character[0],
                    "character_name": character[1],
                    "character_class": character[2],
                    "level": character[3]
                }
                for character in characters
            ],
            "response_seconds": result["response_seconds"]
        })

    except PermissionError as error:
        return jsonify({"error": str(error)}), 403

    except ValueError as error:
        return jsonify({"error": str(error)}), 404


# CREATE PARTY
@app.route('/parties/create', methods=['POST'])
def create_party():

    user_id = current_user_id()

    party_name = text_field(
        request.form,
        'party_name',
        100,
        True
    )

    with connect_db() as conn:
        cursor = conn.execute(
            '''INSERT INTO parties (party_name, dm_user_id)
               VALUES (?, ?)''',
            (party_name, user_id)
        )

        party_id = cursor.lastrowid

        # Add the DM to the party
        conn.execute(
            '''INSERT INTO party_members (party_id, user_id)
               VALUES (?, ?)''',
            (party_id, user_id)
        )

    return jsonify({
        "success": True,
        "party_id": party_id,
        "party_name": party_name
    }), 201


# REMOVE PLAYER FROM PARTY
@app.route('/party/<int:party_id>/remove/<int:player_id>', methods=['POST'])
def dm_remove_player(party_id, player_id):

    dm_user_id = current_user_id()

    try:
        result = db_remove_player(
            dm_user_id,
            party_id,
            player_id
        )

        return jsonify({
            "success": True,
            "message": "Player successfully removed.",
            "response_seconds": result["response_seconds"]
        })

    except PermissionError as error:
        return jsonify({"error": str(error)}), 403

    except ValueError as error:
        return jsonify({"error": str(error)}), 404


# JOIN PARTY
@app.route('/party/<int:party_id>/join', methods=['POST'])
def join_party(party_id):

    user_id = current_user_id()

    with connect_db() as conn:
        party = conn.execute(
            '''SELECT party_id
               FROM parties
               WHERE party_id = ?''',
            (party_id,)
        ).fetchone()

        if party is None:
            return jsonify({"error": "Party not found."}), 404

        try:
            conn.execute(
                '''INSERT INTO party_members (party_id, user_id)
                   VALUES (?, ?)''',
                (party_id, user_id)
            )

        except sqlite3.IntegrityError:
            return jsonify({
                "error": "Already a member."
            }), 409

    return jsonify({"success": True}), 201


# CREATE CHARACTER
@app.route('/characters/create', methods=['POST'])
def create_character():

    user_id = current_user_id()

    name = text_field(request.form, 'nameField', 100, True)
    player = text_field(request.form, 'pNameField', 100, True)
    character_class = text_field(request.form, 'classField', 100, True)
    level = integer_field(request.form, 'lvlField', 1, 20)
    alignment = text_field(request.form, 'alignField', 100, True)
    race = text_field(request.form, 'raceField', 100, True)

    # Player name remains a creator field
    with connect_db() as conn:
        party_id = personal_party_id(conn, user_id)

        cursor = conn.execute(
            '''INSERT INTO characters
               (user_id, party_id, character_name,
                character_class, character_level)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, party_id, name, character_class, level)
        )

        character_id = cursor.lastrowid

        conn.execute(
            '''INSERT INTO character_details
               (character_id, alignment, race)
               VALUES (?, ?, ?)''',
            (character_id, alignment, race)
        )

    return redirect(
        url_for('character_sheet', character_id=character_id)
    )


# VIEW CHARACTER SHEET
@app.route('/characters/<int:character_id>', methods=['GET'])
def character_sheet(character_id):

    user_id = current_user_id()

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        character = owned_character(conn, character_id, user_id)

        details = conn.execute(
            'SELECT * FROM character_details WHERE character_id=?',
            (character_id,)
        ).fetchone()

        items = conn.execute(
            '''SELECT * FROM character_items
               WHERE character_id=? ORDER BY item_id''',
            (character_id,)
        ).fetchall()

        resources = conn.execute(
            '''SELECT * FROM character_resources
               WHERE character_id=? ORDER BY resource_id''',
            (character_id,)
        ).fetchall()

    details = dict(details) if details else {}

    try:
        excel_values = json.loads(details.get('excel_fields', '{}'))

        if not isinstance(excel_values, dict):
            excel_values = {}

    except (ValueError, TypeError):
        excel_values = {}

    prof_skills = json.loads(
        details.get('skill_proficiencies', '[]') or '[]'
    )

    prof_saves = json.loads(
        details.get('saving_throw_proficiencies', '[]') or '[]'
    )

    proficiency_bonus = 2 + (character['character_level'] - 1) // 4

    modifiers = {
        a: (character[a] - 10) // 2
        for a in ABILITIES
    }

    return render_template(
        'character-sheet.html',
        character=character,
        details=details,
        items=items,
        resources=resources,
        abilities=ABILITIES,
        skills=SKILLS,
        prof_skills=prof_skills,
        prof_saves=prof_saves,
        modifiers=modifiers,
        proficiency_bonus=proficiency_bonus,
        sheet_sections=SHEET_SECTIONS,
        excel_values=excel_values,
        excel_numeric=SHEET_NUMERIC,
        passive_skills={
            name: 10 + modifiers[SKILLS[name]] +
            (proficiency_bonus if name in prof_skills else 0)
            for name in ("Insight", "Investigation", "Perception")
        }
    )


# SAVE CHARACTER SHEET
@app.route('/characters/<int:character_id>/save', methods=['POST'])
def save_character(character_id):

    user_id = current_user_id()
    form = request.form

    scores = {
        a: integer_field(form, a, 1, 30)
        for a in ABILITIES
    }

    hp = integer_field(form, 'hit_points', 0, 9999)
    max_hp = integer_field(form, 'max_hit_points', 1, 9999)
    ac = integer_field(form, 'armor_class', 0, 100)
    gold = integer_field(form, 'gold', 0, 1000000000)

    skill_profs = form.getlist('skill_proficiencies')
    save_profs = form.getlist('saving_throw_proficiencies')

    if (
        any(skill not in SKILLS for skill in skill_profs)
        or any(a not in ABILITIES for a in save_profs)
    ):
        abort(400, description='Invalid proficiency selection')

    fields = (
        'alignment',
        'race',
        'languages',
        'ideals',
        'bonds',
        'flaws',
        'personality',
        'other_notes',
        'other_proficiencies'
    )

    text_values = {
        key: text_field(form, key)
        for key in fields
    }

    item_names = form.getlist('item_name')
    item_quantities = form.getlist('item_quantity')
    item_notes = form.getlist('item_notes')

    resource_names = form.getlist('resource_name')
    resource_current = form.getlist('resource_current')
    resource_max = form.getlist('resource_max')

    if (
        len(item_names) != len(item_quantities)
        or len(item_names) != len(item_notes)
    ):
        abort(400, description='Invalid inventory rows')

    if (
        len(resource_names) != len(resource_current)
        or len(resource_names) != len(resource_max)
    ):
        abort(400, description='Invalid resource rows')

    if len(item_names) > 100 or len(resource_names) > 100:
        abort(400, description='Too many rows')

    items = []

    for name, quantity, note in zip(
        item_names, item_quantities, item_notes
    ):
        name, note = name.strip(), note.strip()

        if len(name) > 100 or len(note) > 500:
            abort(400, description='Invalid inventory text')

        if name:
            items.append((
                name,
                integer_field({'q': quantity}, 'q', 0, 99999),
                note
            ))

    resources = []

    for name, current, maximum in zip(
        resource_names,
        resource_current,
        resource_max
    ):
        name = name.strip()

        if len(name) > 100:
            abort(400, description='Invalid resource name')

        if name:
            cur = integer_field({'v': current}, 'v', 0, 99999)
            mx = integer_field({'v': maximum}, 'v', 0, 99999)

            if cur > mx:
                abort(
                    400,
                    description='Resource current value exceeds maximum'
                )

            resources.append((name, cur, mx))

    # Validate additional character sheet fields
    excel_values = {}

    for key in SHEET_KEYS:
        value = text_field(form, 'excel_' + key, 4000)

        if key in SHEET_NUMERIC and value:
            try:
                number = int(value)
            except ValueError:
                abort(400, description='Invalid input: ' + key)

            if number < 0 and key not in (
                'initiative_bonus',
                'spell_attack_bonus'
            ):
                abort(400, description='Invalid input: ' + key)

            if key in (
                'death_successes',
                'death_failures'
            ) and number > 3:
                abort(400, description='Invalid death save count')

            if number > 1000000000:
                abort(400, description='Invalid input: ' + key)

        excel_values[key] = value

    with connect_db() as conn:
        owned_character(conn, character_id, user_id)

        conn.execute(
            '''UPDATE characters
               SET strength=?, dexterity=?, constitution=?,
                   intelligence=?, wisdom=?, charisma=?,
                   hit_points=?, armor_class=?, inventory=?
               WHERE character_id=?''',
            (
                *scores.values(),
                hp,
                ac,
                '\n'.join(
                    f'{q}x {n}' for n, q, _ in items
                ),
                character_id
            )
        )

        conn.execute(
            '''INSERT OR IGNORE INTO character_details
               (character_id) VALUES (?)''',
            (character_id,)
        )

        conn.execute(
            '''UPDATE character_details
               SET alignment=?, race=?, languages=?, ideals=?,
                   bonds=?, flaws=?, personality=?,
                   other_notes=?, other_proficiencies=?,
                   max_hit_points=?, gold=?,
                   skill_proficiencies=?,
                   saving_throw_proficiencies=?
               WHERE character_id=?''',
            (
                *(text_values[k] for k in fields),
                max_hp,
                gold,
                json.dumps(skill_profs),
                json.dumps(save_profs),
                character_id
            )
        )

        # Store additional fields
        conn.execute(
            '''UPDATE character_details
               SET excel_fields=?
               WHERE character_id=?''',
            (json.dumps(excel_values), character_id)
        )

        # Replace inventory rows
        conn.execute(
            'DELETE FROM character_items WHERE character_id=?',
            (character_id,)
        )

        conn.executemany(
            '''INSERT INTO character_items
               (character_id, item_name, quantity, notes)
               VALUES (?, ?, ?, ?)''',
            [
                (character_id, *item)
                for item in items
            ]
        )

        # Replace resource rows
        conn.execute(
            'DELETE FROM character_resources WHERE character_id=?',
            (character_id,)
        )

        conn.executemany(
            '''INSERT INTO character_resources
               (character_id, resource_name, current_value, max_value)
               VALUES (?, ?, ?, ?)''',
            [
                (character_id, *resource)
                for resource in resources
            ]
        )

    return redirect(
        url_for('character_sheet', character_id=character_id)
    )


# STATUS CHECK
@app.route('/status', methods=['GET'])
def home():
    return jsonify({
        "service": "DND Stat Holder",
        "status": "running"
    })


# LEGACY CHARACTER ENDPOINT
@app.route('/character', methods=['GET'])
def character():

    name = request.args.get('nameField', '').strip()
    level = request.args.get('lvlField', '')
    player = request.args.get('pNameField', '')
    character_class = request.args.get('classField', '')
    alignment = request.args.get('alignField', '')
    race = request.args.get('raceField', '')

    if (
        not name
        or not level
        or not level.isdigit()
        or not 1 <= int(level) <= 20
    ):
        abort(400, description='Invalid input')

    data = {
        'name': name,
        'player': player,
        'class': character_class,
        'level': int(level),
        'alignment': alignment,
        'race': race
    }

    if request.args.get('sheetCheck'):
        return jsonify(data), 200

    return render_template(
        'legacy-character.html',
        data=data
    ), 200


# DOCUMENTATION
@app.route('/docs', methods=['GET'])
def docs():

    return jsonify({
        'service': 'DND Stat Holder',
        'routes': [
            '/login',
            '/register',
            '/logout',
            '/main',
            '/character-creator',
            '/character',
            '/characters/create',
            '/characters/<id>',
            '/characters/<id>/save',
            '/parties/create',
            '/party/<id>/join',
            '/party/<id>/remove/<player_id>',
            '/party/<id>/player/<player_id>',
            '/status'
        ]
    })

# DICE ROLLER
@app.route('/dice-roller', methods=['GET', 'POST'])
def dice_roller():

    current_user_id()

    result = None

    if request.method == 'POST':
        dice_type = request.form.get('dice_type', request.form.get('dice', 'd20')).lower()
        roll_type = request.form.get('roll_type', 'normal').lower()

        try:
            number = int(request.form.get('number', 1))
            modifier = int(request.form.get('modifier', 0))
        except (ValueError, TypeError):
            abort(400, description='Please enter valid numbers.')

        if number < 1 or number > 100:
            abort(400, description='Number of dice must be between 1 and 100.')

        dice_options = {
            'd4': 4,
            'd6': 6,
            'd8': 8,
            'd10': 10,
            'd12': 12,
            'd20': 20,
            'd100': 100
        }

        if dice_type not in dice_options:
            abort(400, description='Invalid dice selection.')

        if roll_type not in ('normal', 'advantage', 'disadvantage'):
            abort(400, description='Invalid roll type.')

        import random

        sides = dice_options[dice_type]

        if roll_type == 'normal':
            rolls = [
                random.randint(1, sides)
                for i in range(number)
            ]

            total = sum(rolls) + modifier

        else:
            if dice_type != 'd20' or number != 1:
                abort(400, description='Advantage and disadvantage require one D20.')

            first_roll = random.randint(1, 20)
            second_roll = random.randint(1, 20)

            if roll_type == 'advantage':
                chosen_roll = max(first_roll, second_roll)
            else:
                chosen_roll = min(first_roll, second_roll)

            rolls = [first_roll, second_roll]
            total = chosen_roll + modifier

        result = {
            'dice_type': dice_type.upper(),
            'rolls': rolls,
            'modifier': modifier,
            'total': total
        }

    return render_template('dice_roller.html', result=result)


# START FLASK
if __name__ == '__main__':
    app.run(debug=True)
