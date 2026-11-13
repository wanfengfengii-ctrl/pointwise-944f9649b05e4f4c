import hashlib
import json
import sqlite3
from fractions import Fraction


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def calculate(rows, day, start, end, scale_ppm):
    if not isinstance(day, str) or not day:
        raise ValueError('DAY')
    if type(start) is not int or type(end) is not int or start >= end:
        raise ValueError('WINDOW')
    if type(scale_ppm) is not int or scale_ppm <= 0:
        raise ValueError('SCALE')
    if not isinstance(rows, list):
        raise ValueError('ROWS')
    latest, versions = {}, {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError('ROW')
        ident, rev, at, station, value, deleted = row
        if (not isinstance(ident, str) or not ident or
                type(rev) is not int or rev <= 0 or type(at) is not int or
                not isinstance(station, str) or not station or
                type(value) is not int or type(deleted) is not bool):
            raise ValueError('ROW')
        key = (ident, rev)
        if key in versions and versions[key] != row:
            raise ValueError('REVISION_CONFLICT')
        versions[key] = row
        if ident not in latest or rev > latest[ident][1]:
            latest[ident] = row
    groups = {}
    for ident, rev, at, station, value, deleted in latest.values():
        if not deleted and start <= at < end:
            count, total = groups.get(station, (0, 0))
            groups[station] = (count + 1, total + value)
    result = []
    for station, (count, total) in sorted(groups.items()):
        amount = Fraction(total * scale_ppm, 1000000)
        result.append([station, count, amount.numerator, amount.denominator])
    return {'day': day, 'stations': result}


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute(
            'CREATE TABLE IF NOT EXISTS receipts('
            'job TEXT PRIMARY KEY, request TEXT NOT NULL, receipt TEXT NOT NULL)')

    def close(self):
        self.db.close()

    def publish(self, job, binding, rows, day, start, end, scale_ppm):
        if not isinstance(job, str) or not job or not isinstance(binding, str) or not binding:
            raise ValueError('IDENTITY')
        request = canonical([binding, rows, day, start, end, scale_ppm])
        digest = hashlib.sha256(request.encode('utf-8')).hexdigest()
        result = calculate(rows, day, start, end, scale_ppm)
        receipt = {'job': job, 'binding': binding, 'result': result}
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old = self.db.execute(
                'SELECT request, receipt FROM receipts WHERE job=?', (job,)).fetchone()
            if old:
                if old[0] != digest:
                    raise ValueError('JOB_CONFLICT')
                receipt = json.loads(old[1])
            else:
                self.db.execute('INSERT INTO receipts VALUES(?,?,?)',
                                (job, digest, canonical(receipt)))
            self.db.execute('COMMIT')
            return receipt
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def read(self):
        return [json.loads(row[0]) for row in self.db.execute(
            'SELECT receipt FROM receipts ORDER BY job')]
