from datetime import datetime


def utc(text):
    return int(datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp())


SPRING = [
    ['previous1', 1, utc('2026-03-27T12:00:00Z'), 'north', 4, False],
    ['previous2', 1, utc('2026-03-28T12:00:00Z'), 'south', 6, False],
    ['a', 1, utc('2026-03-28T23:00:00Z'), 'north', 10, False],
    ['b', 1, utc('2026-03-29T00:30:00Z'), 'north', 20, False],
    ['b', 2, utc('2026-03-29T01:30:00Z'), 'south', 25, False],
    ['c', 1, utc('2026-03-29T20:00:00Z'), 'north', -5, False],
    ['edge', 1, utc('2026-03-29T22:00:00Z'), 'north', 100, False],
    ['gone', 1, utc('2026-03-29T12:00:00Z'), 'north', 50, False],
    ['gone', 2, utc('2026-03-29T12:00:00Z'), 'north', 50, True],
]
AUTUMN = [
    ['early', 1, utc('2026-10-24T22:00:00Z'), 'north', 3, False],
    ['fold0', 1, utc('2026-10-25T00:30:00Z'), 'north', 7, False],
    ['fold1', 1, utc('2026-10-25T01:30:00Z'), 'north', 11, False],
    ['edge', 1, utc('2026-10-25T23:00:00Z'), 'north', 100, False],
]
SPRING_WINDOW = (utc('2026-03-28T23:00:00Z'), utc('2026-03-29T22:00:00Z'))
AUTUMN_WINDOW = (utc('2026-10-24T22:00:00Z'), utc('2026-10-25T23:00:00Z'))
