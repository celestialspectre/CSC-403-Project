
import random

DICE_OPTIONS = {
    'd4': 4,
    'd6': 6,
    'd8': 8,
    'd10': 10,
    'd12': 12,
    'd20': 20,
    'd100': 100
}


def roll_dice(dice_type='d20', number=1, modifier=0, roll_type='normal'):

    dice_type = str(dice_type).lower()
    roll_type = str(roll_type).lower()

    if dice_type not in DICE_OPTIONS:
        raise ValueError('Invalid dice selection.')

    if not 1 <= number <= 100:
        raise ValueError('Number of dice must be between 1 and 100.')

    if roll_type not in ('normal', 'advantage', 'disadvantage'):
        raise ValueError('Invalid roll type.')

    sides = DICE_OPTIONS[dice_type]

    if roll_type == 'normal':
        rolls = [
            random.randint(1, sides)
            for _ in range(number)
        ]

        total = sum(rolls) + modifier

    else:
        if dice_type != 'd20' or number != 1:
            raise ValueError(
                'Advantage and disadvantage require exactly one D20.'
            )

        first_roll = random.randint(1, 20)
        second_roll = random.randint(1, 20)

        rolls = [first_roll, second_roll]

        if roll_type == 'advantage':
            chosen_roll = max(rolls)
        else:
            chosen_roll = min(rolls)

        total = chosen_roll + modifier

    return {
        'dice_type': dice_type.upper(),
        'rolls': rolls,
        'modifier': modifier,
        'total': total
    }
