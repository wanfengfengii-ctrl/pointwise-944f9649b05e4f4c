import argparse
import json
from pathlib import Path
from pipeline import Store
from samples import SPRING, SPRING_WINDOW


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    fixture = sub.add_parser('fixture')
    fixture.add_argument('out')
    run = sub.add_parser('run')
    for name in ('db', 'input', 'job', 'binding', 'day'):
        run.add_argument(name)
    for name in ('start', 'end', 'scale_ppm'):
        run.add_argument(name, type=int)
    args = parser.parse_args()
    if args.command == 'fixture':
        Path(args.out).write_text(json.dumps(SPRING, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({'input': args.out, 'records': len(SPRING)}))
        return
    if args.command == 'demo':
        store = Store(':memory:')
        try:
            receipt = store.publish('2026-03-29', 'manual-r1', SPRING,
                                    '2026-03-29', *SPRING_WINDOW, 1500000)
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        finally:
            store.close()
        return
    rows = json.loads(Path(args.input).read_text(encoding='utf-8'))
    store = Store(args.db)
    try:
        receipt = store.publish(args.job, args.binding, rows, args.day,
                                args.start, args.end, args.scale_ppm)
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    finally:
        store.close()


if __name__ == '__main__':
    main()
