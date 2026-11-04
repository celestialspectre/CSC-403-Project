
# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask


from flask import *
import sqlite3 #later for database integration (if we go with that instead of csv files)
import hashlib #for hashing the user password
import os
import json
import random
import dice_roll
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import connect_db, create_database, create_sheet_tables, add_excel_sheet_fields

app = Flask(__name__) 

# temp session verification
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# temp stuff for character sheet
create_database()
create_sheet_tables()
add_excel_sheet_fields()


def setup_user_passwords():
    with connect_db() as conn:
        columns = [
            column[1]
            for column in conn.execute('PRAGMA table_info(users)').fetchall()
        ]

        if 'password_hash' not in columns:
            conn.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')


setup_user_passwords()
# format: @app.route('websitename.xxx/[THIS RIGHT HERE]', methods=['GET'])


ABILITIES = ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma')
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

# character sheet references
SHEET_SECTIONS = {
    'Identity & Appearance': [('gender', 'Gender'), 
    ('deity', 'Deity'), ('background', 'Background'), ('size', 'Size'), ('age', 'Age'), ('height', 'Height'), ('weight', 'Weight'), ('hair', 'Hair'), ('eyes', 'Eyes'), ('portrait_url', 'Portrait URL / reference')], 
    'Classes & Advancement': [('experience_points', 'Experience Points'), ('class_levels', 'Additional classes / levels'), ('hit_dice', 'Hit Dice (e.g. 3d12)'), ('proficiency_override', 'Proficiency Bonus Override (optional)')], 
    'Combat & Movement': [('initiative_bonus', 'Initiative Bonus'), ('speed', 'Walking Speed'), ('other_movement', 'Other Movement Modes'), ('temp_hp', 'Temporary HP'), ('death_successes', 'Death Save Successes (0-3)'), ('death_failures', 'Death Save Failures (0-3)'), ('armor_worn', 'Armor Worn'), ('shield', 'Shield'), ('armor_notes', 'Armor / AC Breakdown'), ('ammunition', 'Ammunition'), ('weapons_spells', 'Weapons & Spells / Attack Details'), ('special_attacks', 'Special Attacks'), ('special_defenses', 'Special Defenses')], 
    'Features & Spellcasting': [('racial_background_features', 'Race / Background / Feats'), ('class_features', 'Class Features'), ('additional_class_info', 'Additional Class Information'), ('spellcasting_ability', 'Spellcasting Ability'), ('spell_save_dc', 'Spell Save DC'), ('spell_attack_bonus', 'Spell Attack Bonus'), ('known_spells', 'Known / Prepared Spells'), ('magic_items', 'Magic Items')], 
    'Equipment & Wealth': [('copper', 'Copper Pieces (CP)'), ('silver', 'Silver Pieces (SP)'), ('electrum', 'Electrum Pieces (EP)'), ('platinum', 'Platinum Pieces (PP)'), ('gems', 'Gems'), ('valuables', 'Jewelry / Valuables'), ('consumables', 'Consumables'), ('equipment_locations', 'Equipment Locations / Containers'), ('equipment_weight', 'Equipment Weight Notes'), ('encumbrance', 'Encumbrance / Carrying Capacity'), ('misc_possessions', 'Miscellaneous Possessions')], 
    'Biography & Relationships': [('character_bio', 'Character Biography'), ('allies_organizations', 'Allies & Organizations'), ('storytelling', 'Storytelling / Background Notes'), ('misc_info', 'Miscellaneous Information')]
}

# character sheet keys
SHEET_KEYS = [
    'gender', 'deity', 'background', 'size', 'age', 'height', 'weight',
    'hair', 'eyes', 'portrait_url', 'experience_points', 'class_levels',
    'hit_dice', 'proficiency_override', 'initiative_bonus', 'speed',
    'other_movement', 'temp_hp', 'death_successes', 'death_failures',
    'armor_worn', 'shield', 'armor_notes', 'ammunition', 'weapons_spells',
    'special_attacks', 'special_defenses', 'racial_background_features',
    'class_features', 'additional_class_info', 'spellcasting_ability',
    'spell_save_dc', 'spell_attack_bonus', 'known_spells', 'magic_items',
    'copper', 'silver', 'electrum', 'platinum', 'gems', 'valuables',
    'consumables', 'equipment_locations', 'equipment_weight', 'encumbrance',
    'misc_possessions', 'character_bio', 'allies_organizations',
    'storytelling', 'misc_info'
]

# numerical values of character sheet stuff
SHEET_NUMERIC = {
    'experience_points', 'death_successes', 'death_failures', 'copper',
    'silver', 'electrum', 'platinum', 'temp_hp', 'age', 'speed',
    'initiative_bonus', 'spell_save_dc', 'spell_attack_bonus'
}


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


def text_field(form, key, limit=2000, required=False):
    value = form.get(key, '').strip()
    if len(value) > limit or (required and not value):
        abort(400, description='Invalid input: ' + key)
    return value


# temp user id
def current_user_id():
    username = session.get('username')
    if not username:
        abort(401, description='Please log in first.')
    with connect_db() as conn:
        row = conn.execute('SELECT user_id FROM users WHERE username=?', (username,)).fetchone()
    if row is None:
        abort(401)
    return row[0]


def owned_character(conn, character_id, user_id):
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM characters WHERE character_id=? AND user_id=?',
                       (character_id, user_id)).fetchone()
    if row is None:
        abort(404, description='Character not found.')
    return row


def personal_party_id(conn, user_id):
    # temp party_id functionality
    row = conn.execute('SELECT party_id FROM parties WHERE dm_user_id=? AND party_name=?',
                       (user_id, 'Personal Characters')).fetchone()
    if row:
        return row[0]
    cursor = conn.execute('INSERT INTO parties (party_name, dm_user_id) VALUES (?, ?)',
                          ('Personal Characters', user_id))
    party_id = cursor.lastrowid
    conn.execute('INSERT INTO party_members (party_id, user_id) VALUES (?, ?)',
                 (party_id, user_id))
    return party_id


# endpoint; url will say '/' when index returns
@app.route('/login', methods=['GET'])

## runs when page opens, starts off with the html file placed in
## the templates folder. For now, this will be the login screen
def index():
    return render_template('login.html') # loads the login.html page


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if len(username) < 3 or len(username) > 40:
        return render_template('register.html', error='Username must be between 3 and 40 characters.')

    if len(password) < 8:
        return render_template('register.html', error='Password must be at least 8 characters.')

    if password != confirm_password:
        return render_template('register.html', error='Passwords do not match.')

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT user_id FROM users WHERE username=?',
            (username,)
        )

        if cursor.fetchone():
            return render_template('register.html', error='Username already exists.')

        password_hash = generate_password_hash(password)

        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.rollback()
        return render_template('register.html', error='Username already exists.')

    finally:
        conn.close()

    return redirect(url_for('index'))


@app.route('/main', methods=['GET', 'POST'])
def main_menu():

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        with connect_db() as conn:
            user = conn.execute(
                'SELECT username, password_hash FROM users WHERE username=?',
                (username,)
            ).fetchone()

        if not user or not user[1] or not check_password_hash(user[1], password):
            return render_template('login.html', error='Incorrect username or password.')

        session.clear()
        session['username'] = user[0]

    elif 'username' not in session:
        return redirect(url_for('index'))

    user_id = current_user_id()

    with connect_db() as conn:
        characters = conn.execute(
            '''SELECT character_id, character_name, character_class, character_level
               FROM characters
               WHERE user_id=?
               ORDER BY character_id DESC''',
            (user_id,)
        ).fetchall()

    return render_template('main.html', characters=characters)


@app.route('/character-creator', methods=['GET'])
def character_creator():
    current_user_id()
    return render_template('character-creator.html')

    # username = request.args.get("username", "")
    # password = request.args.get("password", "")

    # if len(username) < 0:
    #     return jsonify({"error": "username is required"}), 400
    # if len(password) < 0:
    #     return jsonify({"error": "password is required"}), 400

    # ===
    # logic for comparing username + password hash to database goes here
    # ===

    '''
    # temporary character saving stuff, once database is fully made this can be changed however we need
    with sqlite3.connect('characters.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name TEXT, player TEXT, class_name TEXT, level INTEGER, alignment TEXT, race TEXT)')
        characters = conn.execute('SELECT id, name, class_name, level FROM characters ORDER BY id DESC').fetchall()
        

    return """
        <head>
            <title>DND Stat Input</title> <!--name of the tab-->
            <link rel="stylesheet" href="../static/styles/skeleton.css" /> <!--connects the stylesheet (css) to the page-->
        </head>

        <body> 
            <center>
            <form action="/character" method="GET"> <!--sends the form data to the /character endpoint in web.py as a string-->
                <label>Character Name: </label> <!--label for text box-->
                <input required name="nameField"> <!--actual text box-->
                <br /> <!--a line breal to separate elements better-->
                
                <label>Player Name: </label>
                <input required name="pNameField">
                <br />
                
                <label>Class: </label>
                <input required name="classField">
                <br />
                
                <label>Level: </label>
                <input required name="lvlField" type="number" min="1" max="20" step="1">
                <br />
                
                <label>Alignment: </label>
                <input required name="alignField">
                <br />
                
                <label>Race: </label>
                <input required name="raceField">
                <br />
                <br />

                <button>Submit</button> <!--submit button-->
                <br />
            </form>
            </center>

            <!--new saved character section of site to list saved characters (what no way)
            <section class="saved-characters">
                <h2>Saved Characters</h2>
                {% if characters %}
                    {% for character in characters %}
                        <p><a href="{{ url_for('saved_character', character_id=character[0]) }}">{{ character[1] }} — {{ character[2] }}, Level {{ character[3] }}</a></p>
                    {% endfor %}
                {% else %}
                    <p>No characters saved yet.</p>
                {% endif %}
            </section>-->
            """,200'''


@app.route('/characters/create', methods=['POST'])
def create_character():
    user_id = current_user_id()
    name = text_field(request.form, 'nameField', 100, True)
    player = text_field(request.form, 'pNameField', 100, True)
    character_class = text_field(request.form, 'classField', 100, True)
    level = integer_field(request.form, 'lvlField', 1, 20)
    alignment = text_field(request.form, 'alignField', 100, True)
    race = text_field(request.form, 'raceField', 100, True)
    # player name remains a creator field 
    with connect_db() as conn:
        party_id = personal_party_id(conn, user_id)
        cursor = conn.execute('''INSERT INTO characters
            (user_id, party_id, character_name, character_class, character_level)
            VALUES (?, ?, ?, ?, ?)''', (user_id, party_id, name, character_class, level))
        character_id = cursor.lastrowid
        conn.execute('''INSERT INTO character_details (character_id, alignment, race)
                        VALUES (?, ?, ?)''', (character_id, alignment, race))
    return redirect(url_for('character_sheet', character_id=character_id))


@app.route('/characters/<int:character_id>', methods=['GET'])
def character_sheet(character_id):
    user_id = current_user_id()
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        character = owned_character(conn, character_id, user_id)
        details = conn.execute('SELECT * FROM character_details WHERE character_id=?', (character_id,)).fetchone()
        items = conn.execute('SELECT * FROM character_items WHERE character_id=? ORDER BY item_id', (character_id,)).fetchall()
        resources = conn.execute('SELECT * FROM character_resources WHERE character_id=? ORDER BY resource_id', (character_id,)).fetchall()
    details = dict(details) if details else {}
    try:
        excel_values = json.loads(details.get('excel_fields', '{}'))
        if not isinstance(excel_values, dict):
            excel_values = {}
    except (ValueError, TypeError):
        excel_values = {}
    prof_skills = json.loads(details.get('skill_proficiencies', '[]'))
    prof_saves = json.loads(details.get('saving_throw_proficiencies', '[]'))
    proficiency_bonus = 2 + (character['character_level'] - 1) // 4
    modifiers = {a: (character[a] - 10) // 2 for a in ABILITIES}
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
            name: 10 + modifiers[SKILLS[name]] + (proficiency_bonus if name in prof_skills else 0) for name in ("Insight", "Investigation", "Perception")
        })


@app.route('/characters/<int:character_id>/save', methods=['POST'])
def save_character(character_id):
    user_id = current_user_id()
    form = request.form
    scores = {
        a: integer_field(form, a, 1, 30) for a in ABILITIES
    }
    hp = integer_field(form, 'hit_points', 0, 9999)
    max_hp = integer_field(form, 'max_hit_points', 1, 9999)
    ac = integer_field(form, 'armor_class', 0, 100)
    gold = integer_field(form, 'gold', 0, 1000000000)
    skill_profs = form.getlist('skill_proficiencies')
    save_profs = form.getlist('saving_throw_proficiencies')
    if any(skill not in SKILLS for skill in skill_profs) or any(a not in ABILITIES for a in save_profs):
        abort(400, description='Invalid proficiency selection')
    fields = ('alignment', 'race', 'languages', 'ideals', 'bonds', 'flaws', 'personality', 'other_notes', 'other_proficiencies')
    text_values = {
        key: text_field(form, key) for key in fields
    }
    item_names = form.getlist('item_name')
    item_quantities = form.getlist('item_quantity')
    item_notes = form.getlist('item_notes')
    resource_names = form.getlist('resource_name')
    resource_current = form.getlist('resource_current')
    resource_max = form.getlist('resource_max')
    if len(item_names) != len(item_quantities) or len(item_names) != len(item_notes):
        abort(400, description='Invalid inventory rows')
    if len(resource_names) != len(resource_current) or len(resource_names) != len(resource_max):
        abort(400, description='Invalid resource rows')
    if len(item_names) > 100 or len(resource_names) > 100:
        abort(400, description='Too many rows')
    items = []
    for name, quantity, note in zip(item_names, item_quantities, item_notes):
        name, note = name.strip(), note.strip()
        if len(name) > 100 or len(note) > 500:
            abort(400, description='Invalid inventory text')
        if name:
            items.append((name, integer_field({'q': quantity}, 'q', 0, 99999), note))
    resources = []
    for name, current, maximum in zip(resource_names, resource_current, resource_max):
        name = name.strip()
        if len(name) > 100:
            abort(400, description='Invalid resource name')
        if name:
            cur = integer_field({'v': current}, 'v', 0, 99999)
            mx = integer_field({'v': maximum}, 'v', 0, 99999)
            if cur > mx:
                abort(400, description='Resource current value exceeds maximum')
            resources.append((name, cur, mx))
    # validate excel-reference entries before saving
    excel_values = {}
    for key in SHEET_KEYS:
        value = text_field(form, 'excel_' + key, 4000)
        if key in SHEET_NUMERIC and value:
            try:
                number = int(value)
            except ValueError:
                abort(400, description='Invalid input: ' + key)
            if number < 0 and key not in ('initiative_bonus', 'spell_attack_bonus'):
                abort(400, description='Invalid input: ' + key)
            if key in ('death_successes', 'death_failures') and number > 3:
                abort(400, description='Invalid death save count')
            if number > 1000000000:
                abort(400, description='Invalid input: ' + key)
        excel_values[key] = value

    with connect_db() as conn:
        owned_character(conn, character_id, user_id)
        conn.execute('''UPDATE characters SET strength=?, dexterity=?, constitution=?,
            intelligence=?, wisdom=?, charisma=?, hit_points=?, armor_class=?, inventory=?
            WHERE character_id=?''', (*scores.values(), hp, ac,
            '\n'.join(f'{q}x {n}' for n, q, _ in items), character_id))
        conn.execute('''INSERT OR IGNORE INTO character_details (character_id) VALUES (?)''', (character_id,))
        conn.execute('''UPDATE character_details SET alignment=?, race=?, languages=?, ideals=?,
            bonds=?, flaws=?, personality=?, other_notes=?, other_proficiencies=?,
            max_hit_points=?, gold=?, skill_proficiencies=?, saving_throw_proficiencies=?
            WHERE character_id=?''',
            (*(text_values[k] for k in fields), max_hp, gold,
             json.dumps(skill_profs), json.dumps(save_profs), character_id))
        # store additional fields without changing existing columns
        conn.execute('UPDATE character_details SET excel_fields=? WHERE character_id=?', (json.dumps(excel_values), character_id))
        # replace child rows after all validation passes
        conn.execute('DELETE FROM character_items WHERE character_id=?', (character_id,))
        conn.executemany('''INSERT INTO character_items
            (character_id, item_name, quantity, notes) VALUES (?, ?, ?, ?)''', [(character_id, *item) for item in items])
        conn.execute('DELETE FROM character_resources WHERE character_id=?', (character_id,))
        conn.executemany('''INSERT INTO character_resources(character_id, resource_name, current_value, max_value) VALUES (?, ?, ?, ?)''', [(character_id, *resource) for resource in resources])
    return redirect(url_for('character_sheet', character_id=character_id))


# Endpoint 1
# status check
@app.route('/status', methods=['GET'])
def home():
    return jsonify({"service": "DND Stat Holder", "status": "running"})


# Endpoint 2 
# returns a character as json or 400 on a bad input
@app.route('/character', methods=['GET'])
def character():
    name = request.args.get('nameField', '').strip()
    level = request.args.get('lvlField', '')
    player = request.args.get('pNameField', '')
    character_class = request.args.get('classField', '')
    alignment = request.args.get('alignField', '')
    race = request.args.get('raceField', '')

    if not name or not level or not level.isdigit() or not 1 <= int(level) <= 20:
        abort(400, description='Invalid input')
    data = {
        'name': name, 'player': player, 'class': character_class, 'level': int(level), 'alignment': alignment, 'race': race
    }

    if request.args.get('sheetCheck'):
        return jsonify(data), 200
    return render_template('legacy-character.html', data=data), 200


@app.route('/docs', methods=['GET'])
def docs():
    return jsonify({
        'service': 'DND Stat Holder', 
        'routes': ['/login', '/main','/character-creator', '/character', '/characters/create', '/characters/<id>', '/characters/<id>/save', '/status']
    })


# @app.route("/send_stats", methods=['POST'])
# def read_form():
#     #these get whatever was put into the form input fields with corresponding names
#     cName = request.form.get("nameField")
#     pName = request.form.get("pNameField")
#     cClass = request.form.get("classField")
#     cLevel = request.form.get("lvlField")
#     cAlign = request.form.get("alignField")
#     cRace = request.form.get("raceField")


    
    
#     #return {"name" : cName}
#     # this ugly string is an entire html file with the user inputs subbed in. the return creates a new page with all of their inputs
#     return f"<head><title>Stat List</title><link rel=\"stylesheet\" href=\"../static/skeleton.css\" /></head><body><div class=\"statsheet\"><h1>Player Stats</h1><h2>Name</h2><p name=\"nameOut\" class=\"inputRes\">{cName}</p><h2>Player</h2><p name=\"pNameOut\" class=\"inputRes\">{pName}</p><h2>Class</h2><p name=\"classOut\" class=\"inputRes\">{cClass}</p><h2>Level</h2><p name=\"lvlOut\" class=\"inputRes\">{cLevel}</p><h2>Alignment</h2><p name=\"alignOut\" class=\"inputRes\">{cAlign}</p><h2>Race</h2><p name=\"raceOut\" class=\"inputRes\">{cRace}</p></div></body>"



@app.route('/dice-roller', methods=['GET', 'POST'])
def dice_roller():
    if request.method == 'POST':
        dice_types = {
            'd4': dice_roll.d4,
            'd6': dice_roll.d6,
            'd8': dice_roll.d8,
            'd10': dice_roll.d10,
            'd12': dice_roll.d12,
            'd20': dice_roll.d20,
            'd100': dice_roll.d100
        }

        try:
            number = int(request.form.get('number', 1))
            modifier = int(request.form.get('modifier', 0))
            dice_type = request.form.get('dice', 'd20')
            roll_type = request.form.get('roll_type', 'normal')

            if dice_type not in dice_types or number < 1 or number > 100:
                abort(400, description='Invalid dice selection.')

            if roll_type not in ('normal', 'advantage', 'disadvantage'):
                abort(400, description='Invalid roll type.')

            if roll_type != 'normal' and (dice_type != 'd20' or number != 1):
                abort(400, description='Advantage and disadvantage require one D20.')

            if roll_type == 'advantage':
                rolls = [dice_roll.advantage()]
            elif roll_type == 'disadvantage':
                rolls = [dice_roll.disadvantage()]
            else:
                result = dice_roll.multiple_dice(number, dice_types[dice_type])
                rolls = result['rolls']

            session['dice_result'] = {
                'rolls': rolls,
                'modifier': modifier,
                'total': sum(rolls) + modifier,
                'dice': f'{number}{dice_type}',
                'roll_type': roll_type
            }

        except ValueError:
            abort(400, description='Invalid dice input.')

    return render_template('dice-roller.html')


if __name__ == '__main__':
    app.run(debug=True)
