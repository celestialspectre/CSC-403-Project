
import random


# Roll a specific number of dice using the possible values provided.
def roll_dice(number, die_values):
    if number < 1:
        raise ValueError("Number of dice must be at least 1.")

    rolls = []

    for i in range(number):
        rolls.append(random.choice(die_values))

    return rolls


# Possible values for each standard D&D die.
D4 = (1, 2, 3, 4)
D6 = (1, 2, 3, 4, 5, 6)
D8 = (1, 2, 3, 4, 5, 6, 7, 8)
D10 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
D12 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
D20 = tuple(range(1, 21))
D100 = tuple(range(1, 101))


# Shortcuts for common D&D dice.
def d4():
    return roll_dice(1, D4)


def d6():
    return roll_dice(1, D6)


def d8():
    return roll_dice(1, D8)


def d10():
    return roll_dice(1, D10)


def d12():
    return roll_dice(1, D12)


def d20():
    return roll_dice(1, D20)


def d100():
    return roll_dice(1, D100)


# Advantage: roll two D20s and keep the highest.
def advantage():
    rolls = roll_dice(2, D20)
    return max(rolls)


# Disadvantage: roll two D20s and keep the lowest.
def disadvantage():
    rolls = roll_dice(2, D20)
    return min(rolls)


# Roll multiple dice of a specific type.
def multiple_dice(number, dice_type):
    rolls = []

    for i in range(number):
        rolls.extend(dice_type())

    total = sum(rolls)

    return {
        "rolls": rolls,
        "total": total
    }


# Roll dice with a modifier (example: 1D20 + 5).
def roll_with_modifier(number, dice_type, modifier):
    result = multiple_dice(number, dice_type)

    total = result["total"] + modifier

    return {
        "rolls": result["rolls"],
        "modifier": modifier,
        "total": total
    }


# Standard D&D dice shortcuts.
DICE = {
    "d4": d4,
    "d6": d6,
    "d8": d8,
    "d10": d10,
    "d12": d12,
    "d20": d20,
    "d100": d100
}


# Roll a custom combination, such as 2d6 or 4d8.
def custom_roll(number, dice_name, modifier=0):
    dice_name = dice_name.lower()

    if dice_name not in DICE:
        raise ValueError("Invalid dice type.")

    result = roll_with_modifier(number, DICE[dice_name], modifier)

    return {
        "dice": f"{number}{dice_name}",
        "rolls": result["rolls"],
        "modifier": modifier,
        "total": result["total"]
    }


# Roll a D20 with advantage or disadvantage.
def d20_check(modifier=0, advantage_roll=False, disadvantage_roll=False):
    if advantage_roll and disadvantage_roll:
        raise ValueError("A roll cannot have both advantage and disadvantage.")

    if advantage_roll or disadvantage_roll:
        rolls = roll_dice(2, D20)

        if advantage_roll:
            kept_roll = max(rolls)
        else:
            kept_roll = min(rolls)
    else:
        rolls = d20()
        kept_roll = rolls[0]

    return {
        "rolls": rolls,
        "kept_roll": kept_roll,
        "modifier": modifier,
        "total": kept_roll + modifier,
        "natural_20": kept_roll == 20,
        "natural_1": kept_roll == 1
    }


# Calculate an ability score modifier.
def ability_modifier(score):
    if score < 1 or score > 30:
        raise ValueError("Ability score must be between 1 and 30.")

    return (score - 10) // 2


# Roll an ability check.
def ability_check(score, advantage_roll=False, disadvantage_roll=False):
    modifier = ability_modifier(score)

    result = d20_check(
        modifier,
        advantage_roll,
        disadvantage_roll
    )

    result["check_type"] = "Ability Check"

    return result


# Roll a saving throw.
def saving_throw(score, proficiency_bonus=0, proficient=False,
                 advantage_roll=False, disadvantage_roll=False):

    modifier = ability_modifier(score)

    if proficient:
        modifier += proficiency_bonus

    result = d20_check(
        modifier,
        advantage_roll,
        disadvantage_roll
    )

    result["check_type"] = "Saving Throw"

    return result


# Roll a skill check using its associated ability score.
def skill_check(score, proficiency_bonus=0, proficient=False,
                advantage_roll=False, disadvantage_roll=False):

    modifier = ability_modifier(score)

    if proficient:
        modifier += proficiency_bonus

    result = d20_check(
        modifier,
        advantage_roll,
        disadvantage_roll
    )

    result["check_type"] = "Skill Check"

    return result


# Roll initiative using Dexterity.
def initiative(dexterity, advantage_roll=False, disadvantage_roll=False):
    result = ability_check(
        dexterity,
        advantage_roll,
        disadvantage_roll
    )

    result["check_type"] = "Initiative"

    return result


# Roll an attack using an attack bonus.
def attack_roll(attack_bonus=0, advantage_roll=False, disadvantage_roll=False):
    result = d20_check(
        attack_bonus,
        advantage_roll,
        disadvantage_roll
    )

    result["check_type"] = "Attack Roll"
    result["hit_critical"] = result["natural_20"]
    result["miss_critical"] = result["natural_1"]

    return result


# Roll damage for an attack or spell.
def damage_roll(number, dice_name, modifier=0, critical=False):
    if critical:
        number *= 2

    result = custom_roll(number, dice_name, modifier)

    result["check_type"] = "Damage Roll"
    result["critical"] = critical

    return result


# Roll a D20 against a difficulty class.
def ability_check_success(score, difficulty_class,
                          advantage_roll=False, disadvantage_roll=False):

    result = ability_check(
        score,
        advantage_roll,
        disadvantage_roll
    )

    result["difficulty_class"] = difficulty_class
    result["success"] = result["total"] >= difficulty_class

    return result
