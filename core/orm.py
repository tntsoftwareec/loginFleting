
# core/orm.py
class ForeignKey:
    def __init__(self, table: str, local: str, remote: str = "id"):
        self.table = table
        self.local = local
        self.remote = remote

    def resolve(self, cursor, value):
        cursor.execute(
            f"SELECT * FROM {self.table} WHERE {self.remote} = ?",
            (value,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    def __repr__(self):
        return f"<ForeignKey {self.local} → {self.table}.{self.remote}>"

class HasMany:
    def __init__(self, table: str, foreign_key: str):
        self.table = table
        self.foreign_key = foreign_key

    def resolve(self, cursor, value):
        cursor.execute(
            f"SELECT * FROM {self.table} WHERE {self.foreign_key} = ?",
            (value,)
        )
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in rows]

    def __repr__(self):
        return f"<HasMany {self.table} via {self.foreign_key}>"

 