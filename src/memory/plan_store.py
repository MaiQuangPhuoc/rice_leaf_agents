import sqlite3
import json
from datetime import datetime
from typing import Optional


class PlanStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Bước 3.1: Tạo bảng plans nếu chưa có."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id     TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    thread_id   TEXT NOT NULL,
                    disease     TEXT,
                    duration_days INTEGER,
                    location    TEXT,
                    rice_stage  TEXT,
                    status      TEXT DEFAULT 'skeleton',
                    skeleton    TEXT,   -- JSON list[str]
                    steps       TEXT,   -- JSON list[dict]
                    created_at  TEXT,
                    updated_at  TEXT
                )
            """)
            conn.commit()

    # ── Bước 3.2: CRUD ──────────────────────────────────────────

    def create(self, plan: dict) -> None:
        """Lưu plan mới vào DB. plan_id phải unique."""
        # now = datetime.utcnow().isoformat() + "Z"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO plans
                (plan_id, user_id, thread_id, disease, duration_days,
                 location, rice_stage, status, skeleton, steps, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan["plan_id"],
                plan["user_id"],
                plan["thread_id"],
                plan.get("disease"),
                plan.get("duration_days"),
                plan.get("location"),
                plan.get("rice_stage"),
                plan.get("status", "skeleton"),
                json.dumps(plan.get("skeleton", []), ensure_ascii=False),
                json.dumps(plan.get("steps", []), ensure_ascii=False),
                plan.get("created_at", now),
                now,
            ))
            conn.commit()

    def read(self, plan_id: str) -> Optional[dict]:
        """Lấy plan theo plan_id. Trả về None nếu không tìm thấy."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    def read_by_user(self, user_id: str) -> list[dict]:
        """Lấy tất cả plan của một user."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM plans WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def read_by_thread(self, thread_id: str) -> list[dict]:
        """Lấy tất cả plan trong một session/thread."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM plans WHERE thread_id = ? ORDER BY updated_at DESC",
                (thread_id,)
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update(self, plan_id: str, updates: dict) -> bool:
        """
        Cập nhật một phần plan theo plan_id.
        updates: dict chứa các field cần thay đổi.
        Trả về True nếu thành công, False nếu không tìm thấy.
        """
        if not updates:
            return False

        # now = datetime.utcnow().isoformat() + "Z"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates["updated_at"] = now

        # Serialize list fields
        for field in ("skeleton", "steps"):
            if field in updates and isinstance(updates[field], list):
                updates[field] = json.dumps(updates[field], ensure_ascii=False)

        fields = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [plan_id]

        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE plans SET {fields} WHERE plan_id = ?", values
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, plan_id: str) -> bool:
        """Xóa plan theo plan_id."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM plans WHERE plan_id = ?", (plan_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_dict(self, row: tuple) -> dict:
        keys = [
            "plan_id", "user_id", "thread_id", "disease", "duration_days",
            "location", "rice_stage", "status", "skeleton", "steps",
            "created_at", "updated_at"
        ]
        d = dict(zip(keys, row))
        d["skeleton"] = json.loads(d["skeleton"]) if d["skeleton"] else []
        d["steps"] = json.loads(d["steps"]) if d["steps"] else []
        return d
    

# store = PlanStore(db_path="D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\clients\chat_memory.db")

# # create
# store.create(plan_dict)

# # read
# plan = store.read("template_rice_blast_prevention_14d")

# # update status + steps
# store.update("plan_id_123", {"status": "detail", "steps": [...]})

# # read all plans của user
# plans = store.read_by_user("user_001")