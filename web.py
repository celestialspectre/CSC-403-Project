
# flask setup instructions: https://flask.palletsprojects.com/en/stable/installation/#install-flask

import sqlite3
# import hashlib
import os
import json
import secrets
import hashlib
import time
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
from dice_roll import roll_dice
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, session
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

load_dotenv()

app = Flask(__name__)

# temp session verification
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

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
        
# PASSWORD RECOVERY DATABASE

with connect_db() as conn:

    user_columns = {
        row[1]
        for row in conn.execute(
            'PRAGMA table_info(users)'
        )
    }

    if 'email' not in user_columns:
        conn.execute(
            'ALTER TABLE users ADD COLUMN email TEXT'
        )

    conn.execute(
        '''CREATE UNIQUE INDEX IF NOT EXISTS
           idx_users_email_unique
           ON users(email COLLATE NOCASE)
           WHERE email IS NOT NULL'''
    )

    conn.execute(
        '''CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )'''
    )

    conn.execute(
        '''CREATE INDEX IF NOT EXISTS idx_reset_user
           ON password_reset_tokens(user_id)'''
    )


RESET_LIFETIME_SECONDS = 15 * 60
RESET_REQUEST_COOLDOWN = 60


# CSRF PROTECTION

def recovery_csrf_token():

    if 'recovery_csrf' not in session:
        session['recovery_csrf'] = secrets.token_urlsafe(32)

    return session['recovery_csrf']


def check_recovery_csrf():

    submitted = request.form.get('csrf_token', '')
    expected = session.get('recovery_csrf', '')

    if not expected or not secrets.compare_digest(
        submitted, expected
    ):
        abort(
            400,
            description='Invalid form token. Reload the page and try again.'
        )


# SEND PASSWORD RESET LINK

def send_reset_link(email, link):

    # TEMPORARY LOCAL TESTING
    # Prints the reset link instead of sending an email.

    print(
        "\n===================================="
        "\nPASSWORD RESET REQUEST"
        "\nEMAIL: " + email +
        "\nRESET LINK: " + link +
        "\n====================================\n",
        flush=True
    )


# --------------------------------------------------
# FIND RESET TOKEN
# --------------------------------------------------

def reset_token_record(conn, token):

    if len(token) > 200 or len(token) < 32:
        return None

    digest = hashlib.sha256(
        token.encode('utf-8')
    ).hexdigest()

    return conn.execute(
        '''SELECT token_hash, user_id, expires_at, used_at
           FROM password_reset_tokens
           WHERE token_hash = ?''',
        (digest,)
    ).fetchone()


# --------------------------------------------------
# FORGOT PASSWORD ROUTE
# --------------------------------------------------

@app.route('/forgot-password', methods=['GET', 'POST'])

# --------------------------------------------------
# FORGOT PASSWORD ROUTE
# --------------------------------------------------
def forgot_password():

    print("FORGOT PASSWORD ROUTE REACHED", flush=True)
    print("REQUEST METHOD:", request.method, flush=True)

    if request.method == 'POST':

        print("PASSWORD RESET FORM SUBMITTED", flush=True)

        check_recovery_csrf()

        email = request.form.get(
            'email', ''
        ).strip().lower()

        print("EMAIL RECEIVED:", email, flush=True)

        if len(email) > 254 or '@' not in email:

            print("INVALID EMAIL FORMAT", flush=True)

            return render_template(
                'forgot_password.html',
                csrf_token=recovery_csrf_token(),
                error='Enter a valid email address.'
            ), 400

        now = int(time.time())

        with connect_db() as conn:

            user = conn.execute(
                '''SELECT user_id FROM users
                   WHERE email = ? COLLATE NOCASE''',
                (email,)
            ).fetchone()

            if user:

                print("REGISTERED ACCOUNT FOUND", flush=True)

                last = conn.execute(
                    '''SELECT MAX(created_at)
                       FROM password_reset_tokens
                       WHERE user_id = ?''',
                    (user[0],)
                ).fetchone()[0]

                if (
                    last is None
                    or now - last >= RESET_REQUEST_COOLDOWN
                ):

                    print(
                        "GENERATING PASSWORD RESET TOKEN",
                        flush=True
                    )

                    token = secrets.token_urlsafe(32)

                    digest = hashlib.sha256(
                        token.encode('utf-8')
                    ).hexdigest()

                    conn.execute(
                        '''INSERT INTO password_reset_tokens
                           (token_hash, user_id, created_at, expires_at)
                           VALUES (?, ?, ?, ?)''',
                        (
                            digest,
                            user[0],
                            now,
                            now + RESET_LIFETIME_SECONDS
                        )
                    )

                    base = os.getenv(
                        'APP_BASE_URL',
                        'http://127.0.0.1:5000'
                    ).rstrip('/')

                    link = base + url_for(
                        'reset_password',
                        token=token
                    )

                    # LOCAL TESTING ONLY
                    print(
                        "\n====================================\n"
                        "PASSWORD RESET LINK:\n"
                        + link +
                        "\n====================================\n",
                        flush=True
                    )

                else:

                    print(
                        "RESET REQUEST BLOCKED BY COOLDOWN",
                        flush=True
                    )

            else:

                print(
                    "NO REGISTERED ACCOUNT FOUND FOR EMAIL",
                    flush=True
                )

        return render_template(
            'forgot_password.html',
            csrf_token=recovery_csrf_token(),
            message=(
                'If an account uses that email, '
                'a reset link will be sent.'
            )
        )

    return render_template(
        'forgot_password.html',
        csrf_token=recovery_csrf_token()
    )



# RESET PASSWORD ROUTE

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    with connect_db() as conn:

        record = reset_token_record(conn, token)

        valid = bool(
            record
            and record[3] is None
            and record[2] > int(time.time())
        )

    if not valid:

        return render_template(
            'reset_password.html',
            valid=False
        ), 400

    if request.method == 'POST':

        check_recovery_csrf()

        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 8 or len(password) > 1024:

            return render_template(
                'reset_password.html',
                valid=True,
                token=token,
                csrf_token=recovery_csrf_token(),
                error='Password must be at least 8 characters.'
            ), 400

        if password != confirm:

            return render_template(
                'reset_password.html',
                valid=True,
                token=token,
                csrf_token=recovery_csrf_token(),
                error='Passwords do not match.'
            ), 400

        now = int(time.time())

        digest = hashlib.sha256(
            token.encode()
        ).hexdigest()

        with connect_db() as conn:

            cursor = conn.execute(
                '''UPDATE password_reset_tokens
                   SET used_at = ?
                   WHERE token_hash = ?
                   AND used_at IS NULL
                   AND expires_at > ?''',
                (now, digest, now)
            )

            if cursor.rowcount != 1:

                return render_template(
                    'reset_password.html',
                    valid=False
                ), 400

            conn.execute(
                '''UPDATE users
                   SET password_hash = ?
                   WHERE user_id = ?''',
                (
                    generate_password_hash(password),
                    record[1]
                )
            )

            conn.execute(
                '''UPDATE password_reset_tokens
                   SET used_at = ?
                   WHERE user_id = ?
                   AND used_at IS NULL''',
                (now, record[1])
            )

        session.clear()

        return redirect(
            url_for('login', reset='success')
        )

    return render_template(
        'reset_password.html',
        valid=True,
        token=token,
        csrf_token=recovery_csrf_token()
    )



# Add unique access codes to parties.
# Existing parties receive codes automatically.

with connect_db() as conn:
    columns = [
        row[1]
        for row in conn.execute("PRAGMA table_info(parties)")
    ]

    if "access_code" not in columns:
        conn.execute(
            "ALTER TABLE parties ADD COLUMN access_code TEXT"
        )

    existing_codes = {
        row[0]
        for row in conn.execute(
            "SELECT access_code FROM parties WHERE access_code IS NOT NULL"
        )
    }

    parties_without_codes = conn.execute(
        """SELECT party_id FROM parties
           WHERE access_code IS NULL OR access_code = ''"""
    ).fetchall()

    for party in parties_without_codes:
        code = secrets.token_hex(4).upper()

        while code in existing_codes:
            code = secrets.token_hex(4).upper()

        conn.execute(
            "UPDATE parties SET access_code = ? WHERE party_id = ?",
            (code, party[0])
        )

        existing_codes.add(code)



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
        conn.execute(
            'INSERT OR IGNORE INTO party_members (party_id, user_id) VALUES (?, ?)',
            (row[0], user_id)
        )
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

        username = request.form.get(
            'username', ''
        ).strip()

        password = request.form.get('password', '')

        if not username or not password:

            return render_template(
                'login.html',
                error='Please enter your username and password.'
            )

        with connect_db() as conn:

            user = conn.execute(
                '''SELECT username, password_hash
                   FROM users
                   WHERE username = ?''',
                (username,)
            ).fetchone()

        if (
            user
            and user[1]
            and check_password_hash(user[1], password)
        ):

            session.clear()
            session['username'] = user[0]

            return redirect(url_for('main_menu'))

        return render_template(
            'login.html',
            error='Invalid username or password.'
        )

    return render_template(
        'login.html',
        reset_success=(
            request.args.get('reset') == 'success'
        )
    )


# REGISTER

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get(
            'username', ''
        ).strip()

        email = request.form.get(
            'email', ''
        ).strip().lower()

        password = request.form.get('password', '')
        confirm_password = request.form.get(
            'confirm_password', ''
        )

        if len(username) < 3 or len(username) > 40:

            return render_template(
                'register.html',
                error='Username must be 3-40 characters.'
            ), 400

        if (
            len(email) > 254
            or len(email) < 3
            or '@' not in email
            or ' ' in email
        ):

            return render_template(
                'register.html',
                error='Enter a valid email address.'
            ), 400

        if len(password) < 8 or len(password) > 1024:

            return render_template(
                'register.html',
                error='Password must be at least 8 characters.'
            ), 400

        if password != confirm_password:

            return render_template(
                'register.html',
                error='Passwords do not match.'
            ), 400

        try:

            with connect_db() as conn:

                conn.execute(
                    '''INSERT INTO users
                       (username, email, password_hash)
                       VALUES (?, ?, ?)''',
                    (
                        username,
                        email,
                        generate_password_hash(password)
                    )
                )

        except sqlite3.IntegrityError:

            return render_template(
                'register.html',
                error='Username or email is already in use.'
            ), 409

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
        result = db_view_player_page(dm_user_id, party_id, player_id)
        player = result['player']
        return jsonify({
            'player': {'user_id': player[0], 'username': player[1]},
            'characters': [
                {'character_id': c[0], 'character_name': c[1],
                 'character_class': c[2], 'level': c[3]}
                for c in result['characters']
            ],
            'response_seconds': result['response_seconds']
        })
    except PermissionError as error:
        abort(403, description=str(error))
    except ValueError as error:
        abort(404, description=str(error))



# PARTY MANAGEMENT PAGE
@app.route('/parties', methods=['GET'])
def parties_page():
    user_id = current_user_id()
    selected_character = request.args.get('character_id', type=int)

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        personal_party_id(conn, user_id)

        if selected_character is not None:
            owned_character(conn, selected_character, user_id)

        parties = conn.execute(
            '''SELECT p.party_id, p.party_name, p.dm_user_id,
          p.access_code,
          u.username AS dm_name
               FROM parties p
               JOIN party_members pm ON pm.party_id = p.party_id
               JOIN users u ON u.user_id = p.dm_user_id
               WHERE pm.user_id = ?
               ORDER BY p.party_name''',
            (user_id,)
        ).fetchall()

        members = {}
        party_characters = {}

        for party in parties:
            party_id = party['party_id']

            members[party_id] = conn.execute(
                '''SELECT u.user_id, u.username
                   FROM party_members pm
                   JOIN users u ON u.user_id = pm.user_id
                   WHERE pm.party_id = ?
                   ORDER BY u.username''',
                (party_id,)
            ).fetchall()

            party_characters[party_id] = conn.execute(
                '''SELECT c.character_id,
                          c.user_id,
                          c.character_name,
                          c.character_class,
                          c.character_level,
                          c.hit_points,
                          d.max_hit_points,
                          d.race,
                          u.username
                   FROM characters c
                   JOIN party_members pm
                     ON pm.party_id = c.party_id
                    AND pm.user_id = c.user_id
                   JOIN users u ON u.user_id = c.user_id
                   LEFT JOIN character_details d
                     ON d.character_id = c.character_id
                   WHERE c.party_id = ?
                   ORDER BY c.character_name''',
                (party_id,)
            ).fetchall()

        characters = conn.execute(
            '''SELECT character_id, character_name, party_id
               FROM characters
               WHERE user_id = ?
               ORDER BY character_name''',
            (user_id,)
        ).fetchall()

    return render_template(
        'parties.html',
        parties=parties,
        members=members,
        party_characters=party_characters,
        characters=characters,
        selected_character=selected_character,
        user_id=user_id,
        error=request.args.get('error')
    )




# CREATE PARTY
@app.route('/parties/create', methods=['POST'])
@app.route('/parties/new', methods=['POST'])
def create_party():
    user_id = current_user_id()

    party_name = text_field(
        request.form, 'party_name', 100, True
    )

    if party_name.casefold() == 'personal characters':
        return redirect(url_for(
            'parties_page',
            error='That party name is reserved.'
        ))

    with connect_db() as conn:

        access_code = secrets.token_hex(4).upper()

        while conn.execute(
            "SELECT 1 FROM parties WHERE access_code = ?",
            (access_code,)
        ).fetchone():
            access_code = secrets.token_hex(4).upper()

        cursor = conn.execute(
            """INSERT INTO parties
               (party_name, dm_user_id, access_code)
               VALUES (?, ?, ?)""",
            (party_name, user_id, access_code)
        )

        conn.execute(
            """INSERT INTO party_members (party_id, user_id)
               VALUES (?, ?)""",
            (cursor.lastrowid, user_id)
        )

    return redirect(url_for('parties_page'))



# HTML TEMPLATE COMPATIBILITY
# Existing parties.html uses the create_party_page endpoint.
app.add_url_rule('/parties/new-form', endpoint='create_party_page',
                 view_func=create_party, methods=['POST'])



# JOIN PARTY - ACCESS CODE REQUIRED

@app.route('/party/<int:party_id>/join', methods=['POST'])
def join_party(party_id):
    user_id = current_user_id()

    access_code = request.form.get(
        'access_code', ''
    ).strip().upper()

    if not access_code:
        return redirect(url_for(
            'parties_page',
            error='An access code is required to join.'
        ))

    with connect_db() as conn:

        party = conn.execute(
            """SELECT party_name, dm_user_id, access_code
               FROM parties
               WHERE party_id = ?""",
            (party_id,)
        ).fetchone()

        if party is None:
            return redirect(url_for(
                'parties_page',
                error='Party not found.'
            ))

        if party[0] == 'Personal Characters':
            return redirect(url_for(
                'parties_page',
                error='Personal parties cannot be joined.'
            ))

        if not secrets.compare_digest(
            access_code,
            party[2] or ''
        ):
            return redirect(url_for(
                'parties_page',
                error='Incorrect party access code.'
            ))

        conn.execute(
            """INSERT OR IGNORE INTO party_members
               (party_id, user_id)
               VALUES (?, ?)""",
            (party_id, user_id)
        )

    return redirect(url_for('parties_page'))


@app.route('/parties/join', methods=['POST'])
def join_party_page():

    party_id = integer_field(
        request.form, 'party_id', 1, 2147483647
    )

    return join_party(party_id)



# REMOVE PLAYER FROM PARTY
@app.route('/party/<int:party_id>/remove/<int:player_id>', methods=['POST'])
def dm_remove_player(party_id, player_id):
    dm_user_id = current_user_id()
    with connect_db() as conn:
        party = conn.execute(
            'SELECT dm_user_id, party_name FROM parties WHERE party_id = ?',
            (party_id,)
        ).fetchone()
        if party is None:
            abort(404, description='Party not found.')
        if party[0] != dm_user_id or player_id == dm_user_id:
            abort(403, description='Only the DM can remove other members.')
        if party[1] == 'Personal Characters':
            abort(403, description='Personal parties cannot be changed this way.')
        member = conn.execute(
            'SELECT 1 FROM party_members WHERE party_id = ? AND user_id = ?',
            (party_id, player_id)
        ).fetchone()
        if member is None:
            abort(404, description='Player is not in this party.')
        personal_id = personal_party_id(conn, player_id)
        conn.execute(
            'UPDATE characters SET party_id = ? WHERE party_id = ? AND user_id = ?',
            (personal_id, party_id, player_id)
        )
        conn.execute(
            'DELETE FROM party_members WHERE party_id = ? AND user_id = ?',
            (party_id, player_id)
        )
    return redirect(url_for('parties_page'))


# HTML TEMPLATE COMPATIBILITY
@app.route('/parties/<int:party_id>/kick/<int:member_id>', methods=['POST'])
def kick_party_member(party_id, member_id):
    return dm_remove_player(party_id, member_id)


# LEAVE PARTY
@app.route('/parties/<int:party_id>/leave', methods=['POST'])
def leave_party_page(party_id):
    user_id = current_user_id()
    with connect_db() as conn:
        party = conn.execute(
            'SELECT dm_user_id, party_name FROM parties WHERE party_id = ?',
            (party_id,)
        ).fetchone()
        if party is None:
            abort(404, description='Party not found.')
        if party[0] == user_id:
            return redirect(url_for('parties_page', error='The DM cannot leave their own party.'))
        member = conn.execute(
            'SELECT 1 FROM party_members WHERE party_id = ? AND user_id = ?',
            (party_id, user_id)
        ).fetchone()
        if member is None:
            abort(403, description='You are not a member of this party.')
        personal_id = personal_party_id(conn, user_id)
        conn.execute(
            'UPDATE characters SET party_id = ? WHERE party_id = ? AND user_id = ?',
            (personal_id, party_id, user_id)
        )
        conn.execute(
            'DELETE FROM party_members WHERE party_id = ? AND user_id = ?',
            (party_id, user_id)
        )
    return redirect(url_for('parties_page'))


# ASSIGN CHARACTER TO PARTY
@app.route('/characters/<int:character_id>/party', methods=['POST'])
def change_character_party(character_id):
    user_id = current_user_id()
    party_id = integer_field(request.form, 'party_id', 1, 2147483647)
    with connect_db() as conn:
        owned_character(conn, character_id, user_id)
        membership = conn.execute(
            'SELECT 1 FROM party_members WHERE party_id = ? AND user_id = ?',
            (party_id, user_id)
        ).fetchone()
        if membership is None:
            abort(403, description='Join the party before assigning a character.')
        conn.execute(
            'UPDATE characters SET party_id = ? WHERE character_id = ? AND user_id = ?',
            (party_id, character_id, user_id)
        )
    return redirect(url_for('parties_page', character_id=character_id))


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



@app.route('/dice_roller', methods=['GET', 'POST'])
@app.route('/dice-roller', methods=['GET', 'POST'])
def dice_roller():

    current_user_id()

    if request.method == 'GET':
        return render_template('dice_roller.html')

    dice_type = request.form.get('dice_type', 'd20').lower()
    roll_type = request.form.get('roll_type', 'normal').lower()

    try:
        number = int(request.form.get('number', 1))
        modifier = int(request.form.get('modifier', 0))

        result = roll_dice(
            dice_type=dice_type,
            number=number,
            modifier=modifier,
            roll_type=roll_type
        )

    except (ValueError, TypeError) as error:
        return jsonify({
            'error': str(error)
        }), 400

    return jsonify(result)





# START FLASK
if __name__ == '__main__':
    app.run(debug=True)
