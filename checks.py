import copy
import json
import sys
from pipeline import Store, calculate
from samples import SPRING, AUTUMN, SPRING_WINDOW, AUTUMN_WINDOW


def normal():
    expected = {'day': '2026-03-29',
                'stations': [['north', 2, 15, 2], ['south', 1, 75, 2]]}
    start, end = SPRING_WINDOW
    assert end - start == 23 * 3600
    assert calculate(SPRING, '2026-03-29', start, end, 1500000) == expected
    assert calculate(list(reversed(SPRING)), '2026-03-29', start, end, 1500000) == expected
    start2, end2 = AUTUMN_WINDOW
    assert end2 - start2 == 25 * 3600
    assert calculate(AUTUMN, '2026-10-25', start2, end2, 1000000) == {
        'day': '2026-10-25', 'stations': [['north', 3, 21, 1]]}
    store = Store(':memory:')
    try:
        first = store.publish('2026-03-29', 'manual-r1', SPRING,
                              '2026-03-29', start, end, 1500000)
        assert first['result'] == expected
        assert store.publish('2026-03-29', 'manual-r1', SPRING,
                             '2026-03-29', start, end, 1500000) == first
        before = store.read()
        try:
            store.publish('2026-03-29', 'manual-r2', SPRING,
                          '2026-03-29', start, end, 1000000)
        except ValueError as exc:
            assert str(exc) == 'JOB_CONFLICT'
        else:
            raise AssertionError('conflicting publication accepted')
        assert store.read() == before
        bad = copy.deepcopy(SPRING)
        bad.append(list(SPRING[0]))
        bad[-1][4] += 1
        try:
            store.publish('bad', 'manual-r1', bad,
                          '2026-03-29', start, end, 1500000)
        except ValueError as exc:
            assert str(exc) == 'REVISION_CONFLICT'
        else:
            raise AssertionError('invalid snapshot accepted')
        assert store.read() == before
        assert calculate([], '2026-03-29', start, end, 1000000) == {
            'day': '2026-03-29', 'stations': []}
        print('NORMAL_REGRESSION_OK')
        print(json.dumps(before, ensure_ascii=False, sort_keys=True))
    finally:
        store.close()


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] != 'normal':
        raise SystemExit('usage: python3 checks.py normal')
    normal()
