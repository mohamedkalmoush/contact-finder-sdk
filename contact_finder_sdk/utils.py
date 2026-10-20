import csv
import io
import json
import os

from contact_finder_sdk.config import config


# ── extension → format dispatch (authoritative, no sniffing) ──
_COMMENT_PREFIXES = ("#", "//")
_TEXT_EXTS = {"", ".txt", ".list", ".urls", ".log", ".dat"}
_DELIMITED_EXTS = {".csv": ",", ".tsv": "\t"}
_JSON_EXTS = {".json", ".jsonl"}
_SUPPORTED_HINT = ".csv .tsv .txt .list .urls .log .dat .json .jsonl"


def _is_comment(line: str) -> bool:
    return line.startswith(_COMMENT_PREFIXES)


class URLManager:
    def __init__(self, urls_file_path: str = None, field_name: str = "url", project_config=None):
        self.config = project_config if project_config is not None else config
        self.urls_file_path = urls_file_path
        self.field_name = (field_name or "url").strip().lower()

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
                # Header skip: exact match only (case-insensitive, stripped).
                # A line like "https://a.com" is never mistaken for a header.
                if line.lower() == field:
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
        if isinstance(obj, str):
            s = obj.strip()
            return [s] if s else []
        if isinstance(obj, list):
            out: list[str] = []
            for item in obj:
                out.extend(self._extract_json_urls(item))
            return out
        if isinstance(obj, dict):
            value = obj.get(field)
            if isinstance(value, str) and value.strip():
                return [value.strip()]
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

        # Numeric index = explicit "column N, headerless". No guessing.
        if field.isdigit():
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
                raise ValueError(
                    f"Column {field!r} not found in "
                    f"{os.path.basename(source) or 'input'}. "
                    f"Detected columns: {header}. "
                    f"Pass the matching name via url_field_name=..., "
                    f"or a numeric index (e.g. '0' for column 0) if the file has no header."
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
