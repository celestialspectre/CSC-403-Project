from database import connect_db, create_database


ABILITIES = [
    "Strength", 
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma"
]

# (Skill Name, Ability)
SKILLS = [
    ("Acrobatics", "Dexterity"),
    ("Animal Handling", "Wisdom"),
    ("Arcana", "Intelligence"),
    ("Athletics", "Strength"),
    ("Deception", "Charisma"),
    ("History", "Intelligence"),
    ("Insight", "Wisdom"),
    ("Intimidation", "Charisma"),
    ("Investigation", "Intelligence"),
    ("Medicine", "Wisdom"),
    ("Nature", "Intelligence"),
    ("Perception", "Wisdom"),
    ("Performance", "Charisma"),
    ("Persuasion", "Charisma"),
    ("Religion", "Intelligence"),
    ("Sleight of Hand", "Dexterity"),
    ("Stealth", "Dexterity"),
    ("Survival", "Wisdom")
]

# (Class Name, Hit Dice, Skill Proficiencies (to choose from))
CLASSES = [
    ("Barbarian", 12, 2),
    ("Bard", 8, 3),
    ("Cleric", 8, 2),
    ("Druid", 8, 2),
    ("Fighter", 10, 2),
    ("Monk", 8, 2),
    ("Paladin", 10, 2),
    ("Ranger", 10, 3),
    ("Rogue", 8, 4),
    ("Sorcerer", 6, 2),
    ("Warlock", 8, 2),
    ("Wizard", 6, 2)
]

# options for each class to choose from
CLASS_SKILLS = {
    "Barbarian": [
        "Animal Handling", "Athletics", "Intimidation",
        "Nature", "Perception", "Survival"
    ],
    "Bard": [
        "Acrobatics", "Animal Handling", "Arcana",
        "Athletics", "Deception", "History",
        "Insight", "Intimidation", "Investigation",
        "Medicine", "Nature", "Perception",
        "Performance", "Persuasion", "Religion",
        "Sleight of Hand", "Stealth", "Survival"
    ],
    "Cleric": [
        "History", "Insight", "Medicine",
        "Persuasion", "Religion"
    ],
    "Druid": [
        "Arcana", "Animal Handling", "Insight",
        "Medicine", "Nature", "Perception",
        "Religion", "Survival"
    ],
    "Fighter": [
        "Acrobatics", "Animal Handling", "Athletics",
        "History", "Insight", "Intimidation",
        "Perception", "Survival"
    ],
    "Monk": [
        "Acrobatics", "Athletics", "History",
        "Insight", "Religion", "Stealth"
    ],
    "Paladin": [
        "Athletics", "Insight", "Intimidation",
        "Medicine", "Persuasion", "Religion"
    ],
    "Ranger": [
        "Animal Handling", "Athletics", "Insight",
        "Investigation", "Nature", "Perception",
        "Stealth", "Survival"
    ],
    "Rogue": [
        "Acrobatics", "Athletics", "Deception",
        "Insight", "Intimidation", "Investigation",
        "Perception", "Performance", "Persuasion",
        "Sleight of Hand", "Stealth"
    ],
    "Sorcerer": [
        "Arcana", "Deception", "Insight",
        "Intimidation", "Persuasion", "Religion"
    ],
    "Warlock": [
        "Arcana", "Deception", "History",
        "Intimidation", "Investigation",
        "Nature", "Religion"
    ],
    "Wizard": [
        "Arcana", "History", "Insight",
        "Investigation", "Medicine", "Religion"
    ]
}

CLASS_SAVING_THROWS = {
    "Barbarian": ["Strength", "Constitution"],
    "Bard": ["Dexterity", "Charisma"],
    "Cleric": ["Wisdom", "Charisma"],
    "Druid": ["Intelligence", "Wisdom"],
    "Fighter": ["Strength", "Constitution"],
    "Monk": ["Strength", "Dexterity"],
    "Paladin": ["Wisdom", "Charisma"],
    "Ranger": ["Strength", "Dexterity"],
    "Rogue": ["Dexterity", "Intelligence"],
    "Sorcerer": ["Constitution", "Charisma"],
    "Warlock": ["Wisdom", "Charisma"],
    "Wizard": ["Intelligence", "Wisdom"]
}

RACES = [
    ("Dragonborn", 30),
    ("Dwarf", 25),
    ("Elf", 30),
    ("Gnome", 25),
    ("Half-Elf", 30),
    ("Half-Orc", 30),
    ("Halfling", 25),
    ("Human", 30),
    ("Tiefling", 30)
]

SUBRACES = [
    ("Dwarf", "Hill"),
    ("Dwarf", "Mountain"),
    ("Elf", "Dark"),
    ("Elf", "High"),
    ("Elf", "Wood"),
    ("Gnome", "Forest"),
    ("Gnome", "Rock"),
    ("Halfling", "Lightfoot"),
    ("Halfling", "Stout")
]

RACE_ABILITY_BONUSES = [
    ("Dwarf", None, "Constitution", 2),
    ("Dwarf", "Hill", "Wisdom", 1),
    ("Dwarf", "Mountain", "Strength", 2),

    ("Elf", None, "Dexterity", 2),
    ("Elf", "High", "Intelligence", 1),
    ("Elf", "Wood", "Wisdom", 1),
    ("Elf", "Dark", "Charisma", 1),

    ("Halfling", None, "Dexterity", 2),
    ("Halfling", "Lightfoot", "Charisma", 1),
    ("Halfling", "Stout", "Constitution", 1),

    ("Human", None, "Strength", 1),
    ("Human", None, "Dexterity", 1),
    ("Human", None, "Constitution", 1),
    ("Human", None, "Intelligence", 1),
    ("Human", None, "Wisdom", 1),
    ("Human", None, "Charisma", 1),

    ("Dragonborn", None, "Strength", 2),
    ("Dragonborn", None, "Charisma", 1),

    ("Gnome", None, "Intelligence", 2),
    ("Gnome", "Forest", "Dexterity", 1),
    ("Gnome", "Rock", "Constitution", 1),

    ("Half-Elf", None, "Charisma", 2),

    ("Half-Orc", None, "Strength", 2),
    ("Half-Orc", None, "Constitution", 1),

    ("Tiefling", None, "Intelligence", 1),
    ("Tiefling", None, "Charisma", 2)
]

def fill_abilities(conn):
    conn.executemany("""
        INSERT OR IGNORE INTO abilities (ability_name)
        VALUES (?)
        """,
        [(ability,) for ability in ABILITIES]
    )

    print("Abilities added successfully.")

def fill_skills(conn):

    cursor = conn.execute("""
        SELECT ability_id, ability_name
        FROM abilities
    """)

    # name: id
    ability_ids = {row[1]: row[0] for row in cursor.fetchall()}

    skill_data = [(skill_name, ability_ids[ability_name]) for skill_name, ability_name in SKILLS]

    conn.executemany("""
        INSERT OR IGNORE INTO skills (skill_name, ability_id)
        VALUES (?, ?)
        """,
        skill_data
    )

    print("Skills added successfully.")

def fill_classes(conn):
    conn.executemany("""
        INSERT OR IGNORE INTO classes (class_name, hit_dice, starting_skills)
        VALUES (?, ?, ?)
        """,
        CLASSES
    )

    print("Classes added successfully.")

def fill_class_skills(conn):
    cursor = conn.execute("""
        SELECT class_id, class_name
        FROM classes
    """)

    class_ids = {
        row[1]: row[0] for row in cursor.fetchall()
    }

    cursor = conn.execute("""
        SELECT skill_id, skill_name
        FROM skills
    """)

    skill_ids = {
        row[1]: row[0] for row in cursor.fetchall()
    }

    # holds class id and skill id relationships
    class_skill_data = []

    for class_name, skills in CLASS_SKILLS.items():
        for skill_name in skills:
            class_skill_data.append((class_ids[class_name], skill_ids[skill_name]))

    conn.executemany("""
        INSERT OR IGNORE INTO class_skills
            (class_id, skill_id)
        VALUES (?, ?)
        """,
        class_skill_data
    )

    print("Class skill proficiencies added successfully.")

def fill_class_saving_throws(conn):
    cursor = conn.execute("""
        SELECT class_id, class_name
        FROM classes
    """)

    class_ids = {row[1]: row[0] for row in cursor.fetchall()}

    cursor = conn.execute("""
        SELECT ability_id, ability_name
        FROM abilities
    """)

    ability_ids = {row[1]: row[0] for row in cursor.fetchall()}

    saving_throw_data = []

    for class_name, abilities in CLASS_SAVING_THROWS.items():
        for ability_name in abilities:
            saving_throw_data.append((
                class_ids[class_name],
                ability_ids[ability_name]
            ))

    conn.executemany("""
        INSERT OR IGNORE INTO class_saving_throws
            (class_id, ability_id)
        VALUES (?, ?)
        """,
        saving_throw_data
    )

    print("Class saving throws added successfully.")

def fill_races(conn):
    conn.executemany("""
        INSERT OR IGNORE INTO races (race_name, speed)
        VALUES (?, ?)
        """,
        RACES
    )

    print("Races added successfully.")

def fill_subraces(conn):
    cursor = conn.execute("""
        SELECT race_id, race_name
        FROM races
    """)

    race_ids = {row[1]: row[0] for row in cursor.fetchall()}

    subrace_data = [(race_ids[race_name], subrace_name)
        for race_name, subrace_name in SUBRACES]

    conn.executemany("""
        INSERT OR IGNORE INTO subraces (race_id, subrace_name)
        VALUES (?, ?)
        """,
        subrace_data
    )

    print("Subraces added successfully.")

def fill_race_ability_bonuses(conn):
    race_ids = {row[1]: row[0] for row in conn.execute("""
            SELECT race_id, race_name FROM races
        """).fetchall()
    }

    subrace_ids = {(row[1], row[2]): row[0] for row in conn.execute("""
            SELECT subrace_id, race_id, subrace_name
            FROM subraces
        """).fetchall()
    }

    # Retrieve ability IDs
    ability_ids = {row[1]: row[0] for row in conn.execute("""
            SELECT ability_id, ability_name FROM abilities
        """).fetchall()
    }

    bonus_data = []

    for race_name, subrace_name, ability_name, bonus in RACE_ABILITY_BONUSES:
        race_id = race_ids[race_name]

        if subrace_name is not None:
            subrace_id = subrace_ids[(race_id, subrace_name)]
        else: 
            subrace_id = None

        bonus_data.append((race_id, subrace_id, ability_ids[ability_name], bonus))

    conn.executemany("""
        INSERT OR IGNORE INTO race_ability_bonuses
            (race_id, subrace_id, ability_id, bonus)
        VALUES (?, ?, ?, ?)
        """,
        bonus_data
    )

    print("Racial ability bonuses added successfully.")

def fill_database():
    with connect_db() as conn:
        fill_abilities(conn)
        fill_skills(conn)

        fill_classes(conn)
        fill_class_skills(conn)
        fill_class_saving_throws(conn)

        fill_races(conn)
        fill_subraces(conn)
        fill_race_ability_bonuses(conn)

        conn.commit()
        print("Database filled successfully.")

if __name__ == "__main__":
    create_database()
    fill_database()