
# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

from flask import *
import sqlite3
# import hashlib
import os
import json
from log_ai import summarize_session
from api_helper import parse_description
import requests

from werkzeug.security import generate_password_hash, check_password_hash

from database.database import (
    connect_db,
    create_database,
    create_sheet_tables,
    add_excel_sheet_fields,
    view_player_page as db_view_player_page,
    remove_player as db_remove_player,
    make_spell_table,
    add_spells
    # get_user_characters as db_get_user_characters
)

app = Flask(__name__)

# temp session verification
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# temp stuff for character sheet
create_database()
create_sheet_tables()
add_excel_sheet_fields()

#more stuff for the spell list
#make_spell_table()
#add_spells()


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

#api parameters. append desired destination to url w/ concatenation
url = "https://www.dnd5eapi.co/api/2024/" #api base url
data = '{"query"}'


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

def has_log_permission(conn, party_id, user_id):
    result = conn.execute(
        """
        SELECT 1
        FROM party_log_roles
        WHERE party_id = ? AND user_id = ?
        """,
        (party_id, user_id)
    ).fetchone()

    return result is not None

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
def empty():
    return redirect(url_for('login'))

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
                conn.commit()

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
@app.route('/main', methods=['GET', 'POST'])
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
        conn.commit()

    return jsonify({
        "success": True,
        "party_id": party_id,
        "party_name": party_name
    }), 201


### ASSIGN LOG ROLE TO PARTY MEMBER
@app.route(
    '/party/<int:party_id>/log-role/<int:player_id>',
    methods=['POST']
)
def assign_log_role(party_id, player_id):

    dm_user_id = current_user_id()

    with connect_db() as conn:

        # Verify the user is the party's DM
        party = conn.execute(
            """
            SELECT dm_user_id
            FROM parties
            WHERE party_id = ?
            """,
            (party_id,)
        ).fetchone()

        if party is None:
            abort(404, description="Party not found.")

        if party[0] != dm_user_id:
            abort(403, description="Only the DM can assign Log roles.")

        # Verify the selected player belongs to the party
        member = conn.execute(
            """
            SELECT 1
            FROM party_members
            WHERE party_id = ? AND user_id = ?
            """,
            (party_id, player_id)
        ).fetchone()

        if member is None:
            abort(404, description="Player is not in this party.")

        # Assign or replace the party's Log player
        conn.execute(
            """
            INSERT INTO party_log_roles (party_id, user_id)
            VALUES (?, ?)
            ON CONFLICT(party_id)
            DO UPDATE SET user_id = excluded.user_id
            """,
            (party_id, player_id)
        )

    return jsonify({
        "success": True,
        "party_id": party_id,
        "log_user_id": player_id
    })

@app.route('/party/<int:party_id>/logs/save', methods=['POST'])
def save_party_log(party_id):
    user_id = current_user_id()

    session_number = request.form.get('session_number', type=int)
    session_title = request.form.get('session_title', '').strip()
    session_notes = request.form.get('log_text', '').strip()

    if session_number is None or session_number < 1:
        abort(400, description="Invalid session number.")

    if not session_title:
        abort(400, description="Session title is required.")

    with connect_db() as conn:

        # Only the assigned Log player can save notes
        if not has_log_permission(conn, party_id, user_id):
            abort(403, description="You do not have the Log role.")

        # Create a new session log, or update its draft
        existing = conn.execute(
            """
            SELECT log_id, status
            FROM party_logs
            WHERE party_id = ? AND session_number = ?
            """,
            (party_id, session_number)
        ).fetchone()

        if existing:
            if existing[1] == 'published':
                abort(403, description="Published logs cannot be edited.")

            conn.execute(
                """
                UPDATE party_logs
                SET session_title = ?,
                    session_notes = ?,
                    ai_summary = NULL,
                    status = 'draft',
                    updated_at = CURRENT_TIMESTAMP
                WHERE log_id = ?
                """,
                (session_title, session_notes, existing[0])
            )
            log_id = existing[0]

        else:
            cursor = conn.execute(
                """
                INSERT INTO party_logs
                (party_id, author_id, session_number,
                 session_title, session_notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (party_id, user_id, session_number,
                 session_title, session_notes)
            )
            log_id = cursor.lastrowid
        conn.commit()

    return redirect(url_for('main_menu'))
    #return jsonify({
    #    "success": True,
    #    "log_id": log_id,
    #    "party_id": party_id,
    #    "session_number": session_number,
    #    "status": "draft"
    #})


###ORGANIZES PARTY LOG SESSIONS
@app.route('/party/<int:party_id>/logs', methods=['GET'])
def get_party_logs(party_id):
    user_id = current_user_id()
    can_edit=False

    with connect_db() as conn:

        # Verify the user belongs to this party
        member = conn.execute(
            """
            SELECT 1
            FROM party_members
            WHERE party_id = ? AND user_id = ?
            """,
            (party_id, user_id)
        ).fetchone()

        if member is None:
            abort(403, description="You are not a party member.")

        # Check whether this user is the Log player
        can_edit = has_log_permission(conn, party_id, user_id)

        if can_edit:
            # Log player can see drafts and original notes
            logs = conn.execute(
                """
                SELECT log_id, session_number,
                       session_title, session_notes,
                       ai_summary, status,
                       created_at, updated_at
                FROM party_logs
                WHERE party_id = ?
                ORDER BY session_number DESC
                """,
                (party_id,)
            ).fetchall()

        else:
            # Other party members see published summaries only
            logs = conn.execute(
                """
                SELECT log_id, session_number, session_title, ai_summary,
                status, created_at, updated_at
                FROM party_logs
                WHERE party_id = ?
                AND status = 'published'
                ORDER BY session_number DESC
                """,
                (party_id,)
            ).fetchall()

    if can_edit:
        result = [
            {
                "log_id": log[0],
                "session_number": log[1],
                "session_title": log[2],
                "session_notes": log[3],
                "ai_summary": log[4],
                "status": log[5],
                "created_at": log[6],
                "updated_at": log[7]
            }
            for log in logs
        ]
    else:
        result = [
            {
                "log_id": log[0],
                "session_number": log[1],
                "session_title": log[2],
                "ai_summary": log[3],
                "status": log[4],
                "created_at": log[5],
                "updated_at": log[6]
            }
            for log in logs
        ]

    return render_template("log.html", log_contents='', session_title='', user_id=user_id, party_id=party_id)
    #return jsonify({
    #    "party_id": party_id,
    #    "can_edit": can_edit,
    #    "logs": result
    #})


###LOG SUMMARY ROUTE
@app.route(
    '/party/<int:party_id>/logs/<int:log_id>/summarize',
    methods=['POST']
)
def generate_party_log_summary(party_id, log_id):
    user_id = current_user_id()

    with connect_db() as conn:
        if not has_log_permission(conn, party_id, user_id):
            abort(403, description="Log role required.")

        log = conn.execute(
            """
            SELECT session_notes, status, session_title
            FROM party_logs
            WHERE party_id = ?
            """,
            (party_id,)
        ).fetchone()

        if log is None:
            abort(404, description="Log not found.")

        if log[1] == "published":
            abort(403, description="Log is already published.")

        notes = log[0]

        if not notes.strip():
            abort(400, description="No session notes to summarize.")

    try:
        summary = summarize_session(notes)
    except (requests.RequestException, ValueError):
        app.logger.exception("Ollama summarization failed")
        abort(503, description="Could not generate AI summary.")

    with connect_db() as conn:
        cursor = conn.execute(
            """
            UPDATE party_logs
            SET ai_summary = ?,
                status = 'review',
                updated_at = CURRENT_TIMESTAMP
            WHERE log_id = ?
              AND party_id = ?
              AND status != 'published'
              AND session_notes = ?
            """,
            (summary, log_id, party_id, notes)
        )

        if cursor.rowcount == 0:
            abort(409, description="Log changed during summarization.")

    return render_template("log.html", log_contents=summary, session_title=log[2])


@app.route('/log/save', methods=['GET', 'POST'])
def log_save():
    new_contents = ''
    user_id = current_user_id()
    if request.method == 'POST':
        new_contents = request.form.get('log_text')
        session_title = request.form.get('session_title')

        with connect_db() as conn:
            #set entry in db to new_contents
            campaign_id = personal_party_id(conn, user_id)
            conn.execute(
                "insert into campaign_logs (author_id, campaign_id, session_notes, session_title) values (?, ?, ?, ?)",
                (user_id, campaign_id, new_contents, session_title)
            )
            conn.commit()
    return redirect(url_for('log', box_contents=new_contents))




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
        conn.commit()

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
        conn.commit()

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


@app.route('/conditions', methods=['GET'])
def conditions():
    conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 'restrained', 'stunned', 'unconscious']

    dictList = []

    for cond in conditions:
        append = f"conditions/{cond}"

        payload = {}
        headers = {
            'Accept': 'application/json'
        }

        response = requests.request("GET", url+append, headers=headers, data=payload) #queries the api. "conditions/blinded gives the output for the blinded condition"

        #condition json output from api: index, name, description, url, updated_at
        dict = json.loads(response.text) #splits json output into a dictinoary 

        dict["description"] = parse_description(dict["description"])
        dictList += [dict]

    return render_template("statuses.html", conditions=dictList), 200

@app.route('/spells', methods=['GET', 'POST'])
def spells_pg():
    user_class = request.form.get('sel_class')
    print(user_class)
    return render_template("spells.html"), 200

@app.route('/spells/next', methods=['GET', 'POST'])
def filter_spells():
    spells = []
    user_class = request.form.get('sel_class')

    append = f"classes/{user_class}/spells"
    payload = {}
    headers = {
        'Accept': 'application/json'
    }

    response = requests.request("GET", url+append, headers=headers, data=payload)

    dict = json.loads(response.text)

    class_spells = []
    for result in dict["results"]:
        class_spells.append(result["index"])

    for spell in class_spells:
        with connect_db() as conn:
            curr_spell = conn.execute(
                """
                select name, level, range, description
                from spells
                where spell_index = ?
                """,
                (spell)
            ).fetchone()
            spells.append(curr_spell)
    return render_template("spells.html", spells=spells), 200





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
