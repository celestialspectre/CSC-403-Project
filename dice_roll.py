
import random

# Roll a specific number of dice with a certain number of sides
def roll_dice(number, sides):
    rolls = []

    for i in range(number):
        rolls.append(random.randint(1, sides))

    return rolls


# Shortcuts for common D&D dice
def d4():
    return roll_dice(1, 4)


def d6():
    return roll_dice(1, 6)


def d8():
    return roll_dice(1, 8)


def d10():
    return roll_dice(1, 10)


def d12():
    return roll_dice(1, 12)


def d20():
    return roll_dice(1, 20)


def d100():
    return roll_dice(1, 100)


# Advantage: roll two d20s and keep the highest
def advantage():
    rolls = roll_dice(2, 20)
    return max(rolls)


# Disadvantage: roll two d20s and keep the lowest
def disadvantage():
    rolls = roll_dice(2, 20)
    return min(rolls)


# Roll multiple dice of a specific type
def multiple_dice(number, sides):
    rolls = roll_dice(number, sides)
    total = sum(rolls)

    return {
        "rolls": rolls,
        "total": total
    }


# Roll dice with a modifier (example: 1d20 + 5)
def roll_with_modifier(number, sides, modifier):
    rolls = roll_dice(number, sides)
    total = sum(rolls) + modifier

    return {
        "rolls": rolls,
        "modifier": modifier,
        "total": total
    }
