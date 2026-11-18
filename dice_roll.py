
import random


# Roll a specific number of dice using the possible values provided.
def roll_dice(number, die_values):
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
