import os
from typing import TypedDict
from ._meta import FileMeta, file_meta

LANG_MAP: dict[str, str] = {
    ".py": "python", ".pyw": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".jsx": "javascript (jsx)", ".tsx": "typescript (tsx)",
    ".c": "c", ".h": "c header",
    ".cpp": "c++", ".cxx": "c++", ".cc": "c++",
    ".hpp": "c++ header", ".hxx": "c++ header",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin script",
    ".r": "r", ".R": "r",
    ".pl": "perl", ".pm": "perl module",
    ".lua": "lua",
    ".sh": "shell", ".bash": "bash", ".zsh": "zsh",
    ".bat": "batch", ".cmd": "batch",
    ".ps1": "powershell",
    ".cs": "c#",
    ".fs": "f#", ".fsx": "f# script",
    ".scala": "scala",
    ".dart": "dart",
    ".ex": "elixir", ".exs": "elixir script",
    ".erl": "erlang",
    ".hs": "haskell",
    ".ml": "ocaml", ".mli": "ocaml interface",
    ".clj": "clojure",
    ".lisp": "lisp", ".el": "emacs lisp",
    ".vim": "vimscript",
    ".sql": "sql",
    ".graphql": "graphql", ".gql": "graphql",
    ".proto": "protobuf",
    ".tf": "terraform", ".hcl": "hcl",
}


class CodeResult(FileMeta):
    """Parsed source code file metadata."""
    type: str
    content: str
    language: str
    lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int


def _count_lines(text: str, lang: str) -> dict[str, int]:
    """Count total, blank, comment, and code lines."""
    lines = text.splitlines()
    total = len(lines)
    blank = sum(1 for l in lines if l.strip() == "")

    comment_prefixes = {
        "python", "ruby", "shell", "bash", "zsh", "perl", "r",
        "yaml", "toml", "elixir", "dart", "swift", "kotlin",
        "lua", "vimscript", "hcl", "terraform",
    }
    c_style = {
        "c", "c header", "c++", "c++ header", "java", "javascript",
        "typescript", "javascript (jsx)", "typescript (tsx)", "go",
        "rust", "php", "c#", "scala", "kotlin script",
    }

    comment_lines = 0
    in_block = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if lang in comment_prefixes:
            if stripped.startswith("#"):
                comment_lines += 1
        elif lang in c_style:
            if in_block:
                comment_lines += 1
                if "*/" in stripped:
                    in_block = False
            elif stripped.startswith("//"):
                comment_lines += 1
            elif stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped:
                    in_block = True
        elif lang in ("haskell", "ocaml", "ocaml interface"):
            if stripped.startswith("--"):
                comment_lines += 1

    code_lines = total - blank - comment_lines

    return {"total": total, "blank": blank, "comment": comment_lines, "code": code_lines}


def parse_code(path: str) -> CodeResult:
    """Parse a source code file.

    Detects language by extension, counts lines and comments.

    Args:
        path: str — path to the source code file.

    Returns:
        dict: {
            "type": str — always "code",
            "content": str — file content with stats header,
            "language": str — detected programming language,
            "lines": int — total line count,
            "blank_lines": int — blank line count,
            "comment_lines": int — comment line count,
            "code_lines": int — code line count,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    ext = os.path.splitext(path)[1].lower()
    language = LANG_MAP.get(ext, ext.lstrip(".") or "unknown")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    counts = _count_lines(text, language)

    header = [
        f"Language: {language}",
        f"Lines: {counts['total']} (code: {counts['code']}, comments: {counts['comment']}, blank: {counts['blank']})",
        "",
    ]

    return {
        "type": "code",
        "content": "\n".join(header) + text,
        "language": language,
        "lines": counts["total"],
        "blank_lines": counts["blank"],
        "comment_lines": counts["comment"],
        "code_lines": counts["code"],
        **file_meta(path),
    }
