import sqlite3
import datetime

def estimate_tokens(text: str) -> int:
    # A simple heuristic: ~4 characters per token
    return max(1, len(text) // 4)

class DonkeyBridge:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        # Enable WAL
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS bridges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acronym TEXT UNIQUE NOT NULL,
                    peta TEXT NOT NULL,
                    isi TEXT NOT NULL,
                    tags TEXT,
                    context_tokens INTEGER,
                    payload_tokens INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS bridges_fts USING fts5(
                    acronym, peta, isi, tags, content=bridges, content_rowid=id
                )
            ''')
            self.conn.execute('''
                CREATE TRIGGER IF NOT EXISTS bridges_ai AFTER INSERT ON bridges BEGIN
                    INSERT INTO bridges_fts(rowid, acronym, peta, isi, tags)
                    VALUES (new.id, new.acronym, new.peta, new.isi, new.tags);
                END;
            ''')
            self.conn.execute('''
                CREATE TRIGGER IF NOT EXISTS bridges_ad AFTER DELETE ON bridges BEGIN
                    INSERT INTO bridges_fts(bridges_fts, rowid, acronym, peta, isi, tags)
                    VALUES ('delete', old.id, old.acronym, old.peta, old.isi, old.tags);
                END;
            ''')
            self.conn.execute('''
                CREATE TRIGGER IF NOT EXISTS bridges_au AFTER UPDATE ON bridges BEGIN
                    INSERT INTO bridges_fts(bridges_fts, rowid, acronym, peta, isi, tags)
                    VALUES ('delete', old.id, old.acronym, old.peta, old.isi, old.tags);
                    INSERT INTO bridges_fts(rowid, acronym, peta, isi, tags)
                    VALUES (new.id, new.acronym, new.peta, new.isi, new.tags);
                END;
            ''')

    def add(self, acronym: str, peta: str, isi: str, tags: str = "") -> int:
        payload_tokens = estimate_tokens(isi)
        context_tokens = estimate_tokens(acronym)

        try:
            with self.conn:
                cursor = self.conn.execute('''
                    INSERT INTO bridges (acronym, peta, isi, tags, context_tokens, payload_tokens)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (acronym, peta, isi, tags, context_tokens, payload_tokens))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Acronym '{acronym}' already exists.")

    def index(self) -> str:
        cursor = self.conn.execute('SELECT id, acronym, tags FROM bridges ORDER BY id ASC')
        rows = cursor.fetchall()

        lines = []
        for r in rows:
            tag_str = f" — {r['tags']}" if r['tags'] else ""
            lines.append(f"{r['acronym']}{tag_str} | DB-{r['id']}")

        return "\n".join(lines)

    def recall(self, acronym: str) -> dict:
        cursor = self.conn.execute('SELECT id, peta FROM bridges WHERE acronym = ?', (acronym,))
        row = cursor.fetchone()
        if not row:
            return None
        return {"id": row["id"], "peta": row["peta"]}

    def open(self, db_id: int) -> str:
        cursor = self.conn.execute('SELECT isi FROM bridges WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return row["isi"]

    def search(self, query: str) -> list:
        cursor = self.conn.execute('''
            SELECT rowid, acronym, peta, tags
            FROM bridges_fts
            WHERE bridges_fts MATCH ?
            ORDER BY rank
        ''', (query,))
        return [dict(r) for r in cursor.fetchall()]

    def forget(self, db_id: int) -> bool:
        with self.conn:
            cursor = self.conn.execute('DELETE FROM bridges WHERE id = ?', (db_id,))
            return cursor.rowcount > 0

    def stats(self) -> dict:
        cursor = self.conn.execute('''
            SELECT
                COUNT(*) as total_bridges,
                SUM(context_tokens) as total_context_tokens,
                SUM(payload_tokens) as total_payload_tokens
            FROM bridges
        ''')
        row = cursor.fetchone()
        total_bridges = row["total_bridges"] or 0
        total_context = row["total_context_tokens"] or 0
        total_payload = row["total_payload_tokens"] or 0

        saved = total_payload - total_context
        saved_pct = (saved / total_payload * 100) if total_payload > 0 else 0

        return {
            "total_bridges": total_bridges,
            "context_tokens_used": total_context,
            "payload_tokens_on_ssd": total_payload,
            "tokens_saved": saved,
            "savings_percent": round(saved_pct, 2)
        }
