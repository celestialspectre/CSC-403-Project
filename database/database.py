
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
        JOIN parties p ON p.dm_user_id = u.user_id
        WHERE u.user_id = ?
          AND p.party_id = ?
          AND u.role IN ('dm', 'moderator')
    """, (dm_user_id, party_id)).fetchone()

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


if __name__ == "__main__":
    create_database()
    print("Database created successfully.")



