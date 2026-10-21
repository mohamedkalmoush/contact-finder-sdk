import csv
import io
import json
import os
import re

from contact_finder_sdk.config import config


# ── extension → format dispatch (authoritative, no sniffing) ──
_COMMENT_PREFIXES = ("#", "//")
_TEXT_EXTS = {"", ".txt", ".list", ".urls", ".log", ".dat"}
_DELIMITED_EXTS = {".csv": ",", ".tsv": "\t"}
_JSON_EXTS = {".json", ".jsonl"}
_SUPPORTED_HINT = ".csv .tsv .txt .list .urls .log .dat .json .jsonl"


def _is_comment(line: str) -> bool:
    return line.startswith(_COMMENT_PREFIXES)


# ── auto-detect: two regexes ──────────────────────────────────────
# Priority by alternation order: url > website > domain
_HEADER_RE = re.compile(r"urls?|websites?|domains?", re.IGNORECASE)
_VALUE_RE = re.compile(r"^(?:https?://|www\.|[\w-]+\.[a-z]{2,})", re.IGNORECASE)
_HEADER_WORDS = ("url", "urls", "website", "websites", "domain", "domains")


def _header_priority(cell: str):
    """0 = url, 1 = website, 2 = domain, None = no match."""
    m = _HEADER_RE.search(str(cell))
    if not m:
        return None
    w = m.group(0).lower()
    return 0 if w.startswith("url") else 1 if w.startswith("website") else 2


def _is_url_value(value: str) -> bool:
    return bool(_VALUE_RE.search(str(value).strip()))


def _auto_detect_column(rows):
    """Return (col, has_header, reason) or (None, False, '')."""
    if not rows:
        return None, False, ""

    header = [str(h).strip() for h in rows[0]]

    # Pattern 1 — header keyword, priority by alternation order
    best_prio, best_col = None, None
    for col, cell in enumerate(header):
        p = _header_priority(cell)
        if p is not None and (best_prio is None or p < best_prio):
            best_prio, best_col = p, col
    if best_col is not None:
        return best_col, True, f"header '{header[best_col]}'"

    # Pattern 2 — content: first column where most values are URLs
    n = max((len(r) for r in rows), default=0)
    for col in range(n):
        vals = [r[col].strip() for r in rows if len(r) > col and r[col].strip()][:50]
        if vals and sum(1 for v in vals if _is_url_value(v)) / len(vals) >= 0.5:
            row0 = header[col] if col < len(header) else ""
            return col, not _is_url_value(row0), "content"

    return None, False, ""


class URLManager:
    def __init__(self, urls_file_path: str = None, field_name: str = "auto", project_config=None):
        self.config = project_config if project_config is not None else config
        self.urls_file_path = urls_file_path
        self.field_name = (field_name or "auto").strip().lower()

    def normalize_url(self, url: str) -> str:
        if not url: return ""
        url = url.strip().lower().split("://", 1)[-1].rstrip("/")
        return url[4:] if url.startswith("www.") else url





    def load_urls(self, path: str = None) -> list[str]:
        path = path or self.urls_file_path or self.config.URLS_FILE_PATH
        if not path:
            return []

        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"SDK cannot find file: {abs_path}")

        ext = os.path.splitext(abs_path)[1].lower()
        text = self._read_text(abs_path)

        if ext in _TEXT_EXTS:
            return self._load_text(text)
        if ext in _DELIMITED_EXTS:
            return self._load_delimited(text, _DELIMITED_EXTS[ext], source=abs_path)
        if ext in _JSON_EXTS:
            return self._load_json(text, source=abs_path)

        raise ValueError(
            f"Unsupported file extension {ext!r} for {os.path.basename(abs_path)}. "
            f"Supported extensions: {_SUPPORTED_HINT}"
        )

    def _load_text(self, text: str) -> list[str]:
        field = self.field_name
        out: list[str] = []
        first_line = True
        for raw in text.splitlines():
            line = raw.strip().lstrip("\ufeff")
            if not line:
                continue
            if _is_comment(line):
                continue
            if first_line:
                first_line = False
                if field == "auto":
                    if line.lower() in _HEADER_WORDS and not _is_url_value(line):
                        continue
                elif line.lower() == field:
                    continue
            out.append(line)
        return out

    def _load_json(self, text: str, source: str = "") -> list[str]:
        text = text.strip().lstrip("\ufeff")
        if not text:
            return []

        try:
            return self._extract_json_urls(json.loads(text))
        except json.JSONDecodeError:
            pass

        out: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or _is_comment(line):
                continue
            try:
                out.extend(self._extract_json_urls(json.loads(line)))
            except json.JSONDecodeError:
                continue
        return out

    def _extract_json_urls(self, obj) -> list[str]:
        field = self.field_name
        auto = (field == "auto")

        if isinstance(obj, str):
            s = obj.strip()
            if not s:
                return []
            return [s] if (not auto or _is_url_value(s)) else []

        if isinstance(obj, list):
            out: list[str] = []
            for item in obj:
                out.extend(self._extract_json_urls(item))
            return out

        if isinstance(obj, dict):
            if auto:
                keys = [k for word in _HEADER_WORDS for k in obj if k.lower() == word]
            else:
                keys = [field]
            for key in keys:
                v = obj.get(key)
                if isinstance(v, str) and v.strip():
                    return [v.strip()]
            out: list[str] = []
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    out.extend(self._extract_json_urls(v))
            return out
        return []

    def _load_delimited(self, text: str, delimiter: str, source: str = "") -> list[str]:
        text = text.lstrip("\ufeff")
        if not text.strip():
            return []

        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
        rows = [r for r in rows if r and any(c.strip() for c in r)]
        if not rows:
            return []

        field = self.field_name

        if field == "auto":
            col, has_header, reason = _auto_detect_column(rows)
            if col is None:
                header = [h.strip() for h in rows[0]]
                raise ValueError(
                    f"Could not auto-detect a URL column in "
                    f"{os.path.basename(source) or 'input'}. "
                    f"Detected columns: {header}. "
                    f"Pass url_field_name=... explicitly, "
                    f"or a numeric index (e.g. '0') if the file has no header."
                )
            print(f"[auto-detect] column {col + 1} ({reason}) in "
                  f"{os.path.basename(source) or 'input'}")
            body = rows[1:] if has_header else rows
        elif field.isdigit():
            col = int(field)
            max_cols = max(len(r) for r in rows)
            if col >= max_cols:
                raise ValueError(
                    f"Column index {col} out of range for "
                    f"{os.path.basename(source) or 'input'} "
                    f"(file has {max_cols} column(s))."
                )
            body = rows
        else:
            header = [h.strip().lower() for h in rows[0]]
            if field not in header:
                shown_cols = header[:10]
                cols_str = ", ".join(f"'{c}'" for c in shown_cols)
                if len(header) > 10:
                    cols_str += f" (and {len(header) - 10} more)"
                raise ValueError(
                    f"Column '{field}' not found. "
                    f"Available columns: {cols_str}. "
                    f"Please check the column name."
                )
            col = header.index(field)
            body = rows[1:]

        out: list[str] = []
        for r in body:
            if len(r) > col:
                v = r[col].strip()
                if v and not _is_comment(v):
                    out.append(v)
        return out

    def _read_text(self, path: str) -> str:
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                with open(path, "r", encoding=enc, newline="") as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        # latin-1 maps every byte, so this is unreachable; kept as safety net.
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            return f.read()

    def ensure_data_dir(self) -> None:
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        # os.makedirs(self.config.URLS_DIR, exist_ok=True)

    @staticmethod
    def remove_duplicates(items: list[str]) -> list[str]:
        """Removes exact duplicate strings while preserving original order."""
        return list(dict.fromkeys(i for i in items if i))
