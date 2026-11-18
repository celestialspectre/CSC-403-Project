import random
import re
from collections import Counter

ALLOWED_SIDES = {4, 6, 8, 10, 12, 20, 100}
MAX_DICE = 30
MAX_SPAN = 1500
MAX_MODIFIER = 10000


# parse sums of pos dice terms and signed integer modifiers
def parse_expression(expression):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 160:
        raise ValueError('Invalid dice expression.')
    compact = re.sub(r'\s+', '', expression.lower())
    if not re.fullmatch(r'[+\-]?(?:\d*d\d+|\d+)(?:[+\-](?:\d*d\d+|\d+))*', compact):
        raise ValueError('Use an expression such as 1d20 + 1d4 + 3.')
    terms = re.findall(r'[+\-]?(?:\d*d\d+|\d+)', compact)
    dice = []
    modifier = 0
    for term in terms:
        sign = -1 if term.startswith('-') else 1
        unsigned = term.lstrip('+-')
        if 'd' in unsigned:
            if sign < 0:
                raise ValueError('Subtracting dice is not supported; use signed modifiers.')
            number_text, sides_text = unsigned.split('d')
            number = int(number_text) if number_text else 1
            sides = int(sides_text)
            if number < 1 or sides not in ALLOWED_SIDES:
                raise ValueError('Dice must be positive and use d4, d6, d8, d10, d12, d20, or d100.')
            dice.append((number, sides))
        else:
            modifier += sign * int(unsigned)
    if not dice or sum(n for n, _ in dice) > MAX_DICE:
        raise ValueError('Include between 1 and 30 dice.')
    if abs(modifier) > MAX_MODIFIER:
        raise ValueError('Modifier must be between -10000 and 10000.')
    if sum(n * (s - 1) for n, s in dice) > MAX_SPAN:
        raise ValueError('Dice expression is too large to graph.')
    return dice, modifier

# returns probability in percent
def exact_distribution(dice, modifier=0, roll_type='normal'):
    if roll_type in ('advantage', 'disadvantage'):
        if dice != [(1, 20)]:
            raise ValueError('Advantage/disadvantage require exactly one d20.')
        counts = Counter()
        for first in range(1, 21):
            for second in range(1, 21):
                chosen = max(first, second) if roll_type == 'advantage' else min(first, second)
                counts[chosen + modifier] += 1
    else:
        counts = Counter({0: 1})
        for number, sides in dice:
            for _ in range(number):
                next_counts = Counter()
                for subtotal, ways in counts.items():
                    for face in range(1, sides + 1):
                        next_counts[subtotal + face] += ways
                counts = next_counts
        counts = Counter({total + modifier: ways for total, ways in counts.items()})
    combinations = sum(counts.values())
    return {total: ways * 100 / combinations for total, ways in sorted(counts.items())}

# returns rolled dice and the final total
def roll_dice(dice, modifier=0, roll_type='normal'):
    if roll_type in ('advantage', 'disadvantage'):
        first, second = random.randint(1, 20), random.randint(1, 20)
        chosen = max(first, second) if roll_type == 'advantage' else min(first, second)
        return [{'sides': 20, 'values': [first, second]}], chosen + modifier
    groups = []
    total = modifier
    for number, sides in dice:
        values = [random.randint(1, sides) for _ in range(number)]
        groups.append({'sides': sides, 'values': values})
        total += sum(values)
    return groups, total


def probability_at_least(probabilities, target):
    return sum(prob for total, prob in probabilities.items() if total >= target)


# split bars by success/failure
def render_probability_chart(probabilities, target):
    import pygal
    from pygal.style import Style
    chart = pygal.Bar(
        title='Probability by Roll Total',
        x_title='Final roll total',
        y_title='Probability (%)',
        show_legend=True,
        show_dots=False,
        truncate_label=-1,
        x_label_rotation=45,
        height=410,
        style=Style(colors=('#a44840', '#328566'), background='transparent', plot_background='#fffaf0', foreground='#30291e', foreground_strong='#30291e', foreground_subtle='#857967'),)
    totals = list(probabilities)
    chart.x_labels = [str(t) for t in totals]
    failed = []
    succeeded = []
    for total, probability in probabilities.items():
        tooltip = (f'Total {total}: exactly {probability:.2f}%; 'f'{probability_at_least(probabilities, total):.2f}% chance of {total} or higher')
        point = {
            'value': probability, 
            'label': tooltip
        }
        failed.append(point if total < target else None)
        succeeded.append(point if total >= target else None)
    chart.add('Below target', failed)
    chart.add('Above target', succeeded)
    return chart.render_data_uri()
