# core/base_model.py
from core.database import commit, get_connection
from core.orm import ForeignKey, HasMany
from typing import Any


class QuerySet:

    def __init__(self, model, relations=None):
        self.model = model
        self.relations = relations or []

    def _cursor(self):
        # No se toca conn.row_factory: las filas se convierten a dict aquí,
        # evitando que el estado compartido de la conexión afecte a otros
        # consumidores (migraciones/seeds usan tuplas).
        conn = get_connection()
        return conn, conn.cursor()

    @staticmethod
    def _to_dicts(cursor, rows):
        if not rows:
            return []
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in rows]

    def all(self):
        conn, cursor = self._cursor()

        cursor.execute(
            f"SELECT * FROM {self.model.table_name}"
        )
        rows = self._to_dicts(cursor, cursor.fetchall())

        return self._attach_relations(cursor, rows)

    def first(self):
        conn, cursor = self._cursor()
        cursor.execute(
            f"SELECT * FROM {self.model.table_name} LIMIT 1"
        )
        rows = self._to_dicts(cursor, cursor.fetchall())
        if not rows:
            return None
        return self._attach_relations(cursor, rows)[0]

    def find(self, id):
        conn, cursor = self._cursor()

        cursor.execute(
            f"SELECT * FROM {self.model.table_name} WHERE id = ?",
            (id,)
        )
        rows = self._to_dicts(cursor, cursor.fetchall())

        if not rows:
            return None

        return self._attach_relations(cursor, rows)[0]

    def where(self, **filters):
        conn, cursor = self._cursor()

        keys = filters.keys()
        values = tuple(filters.values())
        cond = " AND ".join(f"{k}=?" for k in keys)

        cursor.execute(
            f"SELECT * FROM {self.model.table_name} WHERE {cond}",
            values
        )

        rows = self._to_dicts(cursor, cursor.fetchall())
        return self._attach_relations(cursor, rows)

    def count(self):
        conn, cursor = self._cursor()
        cursor.execute(
            f"SELECT COUNT(*) as total FROM {self.model.table_name}"
        )
        rows = self._to_dicts(cursor, cursor.fetchall())
        return rows[0]["total"] if rows else 0

    def exists(self, **filters):
        return len(self.where(**filters)) > 0

    # =========================
    # Relations
    # =========================

    def _attach_relations(self, cursor, rows):
        if not self.relations:
            return rows

        for row in rows:
            for rel_name in self.relations:
                rel = getattr(self.model, rel_name, None)

                if isinstance(rel, ForeignKey):
                    value = row.get(rel.local)
                    row[rel_name] = rel.resolve(cursor, value)

                elif isinstance(rel, HasMany):
                    value = row.get("id")
                    row[rel_name] = rel.resolve(cursor, value)

        return rows


class BaseModel:
    table_name: str
    # ---------- Query ----------
    @classmethod
    def with_(cls, *relations):
        return QuerySet(cls, relations)

    @classmethod
    def all(cls):
        return cls.with_().all()

    @classmethod
    def first(cls):
        return cls.with_().first()

    @classmethod
    def find(cls, id):
        return cls.with_().find(id)

    @classmethod
    def where(cls, **filters):
        return cls.with_().where(**filters)

    @classmethod
    def count(cls):
        return cls.with_().count()

    @classmethod
    def exists(cls, **filters):
        return cls.with_().exists(**filters)

    # ---------- Write ----------
    @classmethod
    def create(cls, **data):
        conn = get_connection()
        cursor = conn.cursor()

        keys = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        cursor.execute(
            f"INSERT INTO {cls.table_name} ({keys}) VALUES ({placeholders})",
            values
        )
        commit(conn)

        return cls.find(cursor.lastrowid)

    @classmethod
    def update_by_id(cls, id, **data):
        conn = get_connection()
        cursor = conn.cursor()
        assigns = ", ".join(f"{k}=?" for k in data)
        values = tuple(data.values()) + (id,)
        cursor.execute(
            f"UPDATE {cls.table_name} SET {assigns} WHERE id = ?",
            values
        )
        commit(conn)
        return cls.find(id)

    @classmethod
    def delete_by_id(cls, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {cls.table_name} WHERE id = ?",
            (id,)
        )
        commit(conn)
        return True

    def to_dict(self):
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    def save(self):
        data = self.__dict__.copy()

        if "id" in data and data["id"]:
            self.update(**data)
        else:
            obj = self.__class__.create(**data)
            self.id = obj["id"]

        return self

    def update(self, **data):
        conn = get_connection()
        cursor = conn.cursor()

        target_id = data.pop("id", getattr(self, "id", None))
        if not target_id:
            raise ValueError("Update requires id")

        assigns = ", ".join(f"{k}=?" for k in data)
        values = tuple(data.values()) + (target_id,)

        cursor.execute(
            f"UPDATE {self.table_name} SET {assigns} WHERE id = ?",
            values
        )
        commit(conn)
        return self

    def delete(self):
        target_id = getattr(self, "id", None)
        if not target_id:
            raise ValueError("Delete requires id")

        return self.__class__.delete_by_id(target_id)
