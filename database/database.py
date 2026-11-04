
import sqlite3
import time


DATABASE_NAME = "dnd.db"


def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_database():
    ###Consists of four main tables consisting of users, parties, party members and characters 
    with connect_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL DEFAULT 'player'
                CHECK (role IN ('player', 'dm', 'moderator'))
        );

        CREATE TABLE IF NOT EXISTS parties (
            party_id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_name TEXT NOT NULL,
            dm_user_id INTEGER NOT NULL,
            FOREIGN KEY (dm_user_id)
                REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS party_members (
            party_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (party_id, user_id),
            FOREIGN KEY (party_id)
                REFERENCES parties(party_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS characters (
            character_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            party_id INTEGER NOT NULL,
            character_name TEXT NOT NULL,
            character_class TEXT,
            character_level INTEGER DEFAULT 1,
            strength INTEGER DEFAULT 10,
            dexterity INTEGER DEFAULT 10,
            constitution INTEGER DEFAULT 10,
            intelligence INTEGER DEFAULT 10,
            wisdom INTEGER DEFAULT 10,
            charisma INTEGER DEFAULT 10,
            hit_points INTEGER DEFAULT 10,
            armor_class INTEGER DEFAULT 10,
            inventory TEXT,
            backstory TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (party_id) REFERENCES parties(party_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_members_user
            ON party_members(user_id);

        CREATE INDEX IF NOT EXISTS idx_characters_party
            ON characters(party_id);

        CREATE INDEX IF NOT EXISTS idx_characters_user
            ON characters(user_id);
        """)


def is_dm_of_party(conn, dm_user_id, party_id):
    """Check whether the user is the assigned DM or a moderator."""

    result = conn.execute("""
        SELECT 1
        FROM users u
        JOIN parties p ON p.party_id = ?
        WHERE u.user_id = ?
          AND (
              p.dm_user_id = u.user_id
              OR u.role = 'moderator')
    """, (party_id, dm_user_id)).fetchone()

    return result is not None


def view_player_page(dm_user_id, party_id, player_id):
    """Return a player's details and characters for an authorized DM."""
    start = time.perf_counter()

    with connect_db() as conn:
        if not is_dm_of_party(conn, dm_user_id, party_id):
            raise PermissionError(
                "You are not authorized to manage this party."
            )

        player = conn.execute("""
            SELECT u.user_id, u.username
            FROM users u
            JOIN party_members pm ON pm.user_id = u.user_id
            WHERE u.user_id = ?
              AND pm.party_id = ?
        """, (player_id, party_id)).fetchone()

        if player is None:
            raise ValueError("Player not found in this party.")

        characters = conn.execute("""
            SELECT character_id, character_name, character_class,
                   character_level, strength, dexterity, constitution,
                   intelligence, wisdom, charisma, hit_points,
                   armor_class, inventory, backstory
            FROM characters
            WHERE user_id = ? AND party_id = ?
        """, (player_id, party_id)).fetchall()

    elapsed = time.perf_counter() - start
    return {
        "player": player,
        "characters": characters,
        "response_seconds": elapsed
    }
####CHARACTER###
def create_character(user_id, party_id, name, character_class=None, level=1):
    """Create a character belonging to a user and party."""

    if not name or len(name) > 100:
        raise ValueError("Invalid character name.")

    if not 1 <= level <= 20:
        raise ValueError("Character level must be between 1 and 20.")

    with connect_db() as conn:
        # Verify user is in party before creating the character.
        member = conn.execute("""
            SELECT 1 FROM party_members
            WHERE party_id = ? AND user_id = ?
        """, (party_id, user_id)).fetchone()

        if member is None:
            raise PermissionError("User is not a member of this party.")

        cursor = conn.execute("""
            INSERT INTO characters
            (user_id, party_id, character_name, character_class, character_level)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, party_id, name, character_class, level))

        character_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO character_details (character_id)
            VALUES (?)
        """, (character_id,))

        return character_id


def get_character(character_id, user_id):
    """Retrieve a character only if it belongs to the requesting user."""

    with connect_db() as conn:
        conn.row_factory = sqlite3.Row

        character = conn.execute("""
            SELECT *
            FROM characters
            WHERE character_id = ? AND user_id = ?""",
            (character_id, user_id)).fetchone()

        if character is None:
            return None

        details = conn.execute("""
            SELECT *
            FROM character_details
            WHERE character_id = ?""",
             (character_id,)).fetchone()

        return {
            "character": dict(character),
            "details": dict(details) if details else {}
        }


def get_user_characters(user_id):
    """Retrieve all characters belonging to a user."""

    with connect_db() as conn:
        return conn.execute("""
            SELECT character_id, character_name,character_class, character_level
            FROM characters
            WHERE user_id = ?
            ORDER BY character_id DESC
        """, (user_id,)).fetchall()


def update_character(character_id, user_id, updates):
    """Update basic character information."""

    allowed_fields = {
        "character_name",
        "character_class",
        "character_level",
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
        "hit_points",
        "armor_class",
        "inventory",
        "backstory"
    }

    if not updates:
        raise ValueError("No updates provided.")

    if not set(updates).issubset(allowed_fields):
        raise ValueError("Invalid character field.")

    if "character_level" in updates:
        if not 1 <= updates["character_level"] <= 20:
            raise ValueError("Invalid character level.")

    columns = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())

    with connect_db() as conn:
        cursor = conn.execute(
            f"""
            UPDATE characters
            SET {columns}
            WHERE character_id = ? AND user_id = ?
            """,
            (*values, character_id, user_id)
        )

        if cursor.rowcount == 0:
            raise ValueError("Character not found.")

def remove_player(dm_user_id, party_id, player_id):
    """Remove a player from a party without deleting their account."""
    start = time.perf_counter()

    with connect_db() as conn:
        if not is_dm_of_party(conn, dm_user_id, party_id):
            raise PermissionError(
                "You are not authorized to manage this party."
            )

        # Do not allow the DM to remove themselves by this function.
        party = conn.execute("""
            SELECT dm_user_id
            FROM parties
            WHERE party_id = ?
        """, (party_id,)).fetchone()

        if party is None:
            raise ValueError("Party not found.")

        if player_id == party[0]:
            raise ValueError("The DM cannot remove themselves.")

        cursor = conn.execute("""
            DELETE FROM party_members
            WHERE party_id = ? AND user_id = ?
        """, (party_id, player_id))

        if cursor.rowcount == 0:
            raise ValueError("Player is not a member of this party.")

    elapsed = time.perf_counter() - start
    return {
        "success": True,
        "response_seconds": elapsed
    }
####ITEMS#####
def add_item(character_id, item_name, quantity=1, notes=""):
    """Add an inventory item to a character."""

    if not item_name or len(item_name) > 100:
        raise ValueError("Invalid item name.")

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    with connect_db() as conn:
        cursor = conn.execute("""
            INSERT INTO character_items
            (character_id, item_name, quantity, notes)
            VALUES (?, ?, ?, ?)
        """, (character_id, item_name, quantity, notes))

        return cursor.lastrowid


def get_inventory(character_id):
    """Retrieve all inventory items for a character."""

    with connect_db() as conn:
        return conn.execute("""
            SELECT item_id, item_name, quantity, notes
            FROM character_items
            WHERE character_id = ?
            ORDER BY item_id
        """, (character_id,)).fetchall()


def remove_item(item_id, character_id):
    """Remove an item belonging to a specific character."""

    with connect_db() as conn:
        cursor = conn.execute("""
            DELETE FROM character_items
            WHERE item_id = ? AND character_id = ?
        """, (item_id, character_id))

        return cursor.rowcount > 0


def update_item(item_id, character_id, quantity, notes=""):
    """Update an item's quantity and notes."""

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    with connect_db() as conn:
        cursor = conn.execute("""
            UPDATE character_items
            SET quantity = ?, notes = ?
            WHERE item_id = ? AND character_id = ?
        """, (quantity, notes, item_id, character_id))

        return cursor.rowcount > 0




###RESOURCES####
def add_resource(character_id, resource_name, current_value=0, max_value=0):
    """Create a character resource."""

    if not resource_name or len(resource_name) > 100:
        raise ValueError("Invalid resource name.")

    if current_value < 0 or max_value < 0:
        raise ValueError("Resource values cannot be negative.")

    if current_value > max_value:
        raise ValueError("Current value cannot exceed maximum.")

    with connect_db() as conn:
        cursor = conn.execute("""
            INSERT INTO character_resources
            (character_id, resource_name, current_value, max_value)
            VALUES (?, ?, ?, ?)
        """, (character_id, resource_name, current_value, max_value))

        return cursor.lastrowid


def get_resources(character_id):
    """Retrieve all resources for a character."""

    with connect_db() as conn:
        return conn.execute("""
            SELECT resource_id, resource_name,
                   current_value, max_value
            FROM character_resources
            WHERE character_id = ?
            ORDER BY resource_id
        """, (character_id,)).fetchall()


def update_resource(resource_id, character_id, current_value, max_value):
    """Update a character resource."""

    if current_value < 0 or max_value < 0:
        raise ValueError("Resource values cannot be negative.")

    if current_value > max_value:
        raise ValueError("Current value cannot exceed maximum.")

    with connect_db() as conn:
        cursor = conn.execute("""
            UPDATE character_resources
            SET current_value = ?, max_value = ?
            WHERE resource_id = ? AND character_id = ?
        """, (current_value, max_value, resource_id, character_id))

        return cursor.rowcount > 0


def remove_resource(resource_id, character_id):
    """Remove a character resource."""

    with connect_db() as conn:
        cursor = conn.execute("""
            DELETE FROM character_resources
            WHERE resource_id = ? AND character_id = ?
        """, (resource_id, character_id))

        return cursor.rowcount > 0



# character sheet extension
def create_sheet_tables():
    # add detail tables without modifying or dropping existing character data
    with connect_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS character_details (
            character_id INTEGER PRIMARY KEY,
            alignment TEXT NOT NULL DEFAULT '',
            race TEXT NOT NULL DEFAULT '',
            max_hit_points INTEGER NOT NULL DEFAULT 10,
            gold INTEGER NOT NULL DEFAULT 0 CHECK(gold >= 0),
            languages TEXT NOT NULL DEFAULT '',
            ideals TEXT NOT NULL DEFAULT '',
            bonds TEXT NOT NULL DEFAULT '',
            flaws TEXT NOT NULL DEFAULT '',
            personality TEXT NOT NULL DEFAULT '',
            other_notes TEXT NOT NULL DEFAULT '',
            skill_proficiencies TEXT NOT NULL DEFAULT '[]',
            saving_throw_proficiencies TEXT NOT NULL DEFAULT '[]',
            other_proficiencies TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS character_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity >= 0),
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS character_resources (
            resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            resource_name TEXT NOT NULL,
            current_value INTEGER NOT NULL DEFAULT 0 CHECK(current_value >= 0),
            max_value INTEGER NOT NULL DEFAULT 0 CHECK(max_value >= 0),
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        );""")

# reference excel sheet that I sent yall
def add_excel_sheet_fields():
    # store supplementary sheet fields as JSON
    with connect_db() as conn:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(character_details)')}
        if 'excel_fields' not in columns:
            conn.execute("ALTER TABLE character_details ADD COLUMN excel_fields TEXT NOT NULL DEFAULT '{}'")

if __name__ == "__main__":
    create_database()
    create_sheet_tables()
    add_excel_sheet_fields()
    print("Database created successfully.")