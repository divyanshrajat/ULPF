"""
regex_parser.py — ReDoS-safe regex parser.

Execution model:
  * google-re2 available → compile + match inside re2 (linear time, no backtracking).
  * google-re2 unavailable → compile + match via Python's built-in re module,
    but every operation is isolated in a *separate process* with a hard
    REGEX_TIMEOUT_SECONDS wall-clock kill.  A thread timeout is NOT used because
    a CPU-bound catastrophic backtracking thread cannot be interrupted by the GIL.

Process lifecycle:
  * One short-lived subprocess per parse() call.  No persistent worker pool.
  * The subprocess is always joined/terminated in the finally block so there
    are no zombie or orphan processes.
  * Overhead is acceptable: the fallback path already indicates a degraded
    security posture (re2 unavailable); the extra latency is acceptable.
"""
import logging
import multiprocessing
import multiprocessing.context
import re
from typing import Any

logger = logging.getLogger(__name__)

try:
    import re2  # type: ignore
    HAS_RE2 = True
except ImportError:
    HAS_RE2 = False
    logger.warning(
        "google-re2 not installed. Falling back to built-in re module. "
        "ReDoS protection will use subprocess isolation with a hard timeout."
    )

from .base import BaseParser, ParserError, RegexTimeoutError


# ── subprocess worker ─────────────────────────────────────────────────────────

def _re_match_worker(pattern: str, text: str, result_queue: multiprocessing.Queue) -> None:  # type: ignore[type-arg]
    """
    Runs inside a child process.  Puts (True, groups, groupdict) on success,
    (False, None, None) on non-match, or raises (caught and put as None sentinel).
    Never returns sensitive data unnecessarily.
    """
    try:
        compiled = re.compile(pattern)
        m = compiled.search(text)
        if m:
            result_queue.put((True, m.groups(), m.groupdict()))
        else:
            result_queue.put((False, None, None))
    except Exception as exc:
        # Signal a compilation/match error to the parent
        result_queue.put(("error", str(exc), None))


def _run_re_with_timeout(pattern: str, text: str, timeout: float) -> tuple[bool, tuple, dict]:
    """
    Execute `re.search(pattern, text)` in an isolated child process.

    Returns:
        (matched: bool, groups: tuple, groupdict: dict)

    Raises:
        RegexTimeoutError  — operation exceeded `timeout` seconds
        ParserError        — re.compile/re.search raised an error
    """
    ctx = multiprocessing.get_context("spawn")
    q: multiprocessing.Queue = ctx.Queue(maxsize=1)  # type: ignore[type-arg]
    proc = ctx.Process(target=_re_match_worker, args=(pattern, text, q), daemon=True)
    proc.start()
    try:
        proc.join(timeout=timeout)
        if proc.is_alive():
            proc.kill()
            proc.join()  # reap zombie
            raise RegexTimeoutError(
                f"Regex operation exceeded {timeout}s timeout — pattern rejected for safety."
            )
        if not q.empty():
            result = q.get_nowait()
            if result[0] == "error":
                raise ParserError(f"Regex execution error: {result[1]}")
            matched, groups, groupdict = result
            return bool(matched), groups or (), groupdict or {}
        # Process exited cleanly but put nothing in the queue (should not happen)
        raise ParserError("Regex subprocess exited without a result.")
    finally:
        if proc.is_alive():
            proc.kill()
            proc.join()


# ── parser class ──────────────────────────────────────────────────────────────

class RegexParser(BaseParser):
    def __init__(self, parser_def: dict[str, Any], field_mappings: dict[str, str]):
        super().__init__(parser_def, field_mappings)
        pattern = self.parser_def.get("pattern")
        if not pattern:
            raise ParserError("Regex parser requires a 'pattern' definition")

        self._pattern_str = pattern

        if HAS_RE2:
            try:
                self.regex = re2.compile(pattern)
            except Exception as e:
                raise ParserError(f"Invalid regex pattern: {e}")
        else:
            # Validate the pattern is at least syntactically valid via re,
            # but do NOT do a full match here (could hang on compile for some
            # pathological patterns).  Compilation is generally fast; the
            # catastrophic cost is in matching, but we still wrap it in a
            # lightweight try/except for safety.
            try:
                re.compile(pattern)  # syntax check only
            except re.error as e:
                raise ParserError(f"Invalid regex pattern: {e}")
            self.regex = None  # matching goes through subprocess

    def parse(self, raw_event: str) -> dict[str, Any]:
        if HAS_RE2:
            # Fast path: re2 is linear-time, no subprocess needed.
            match = self.regex.search(raw_event)
            if not match:
                raise ParserError("Regex did not match the event")
            extracted = match.groupdict()
            groups = match.groups()
        else:
            # Slow/safe path: subprocess with hard timeout.
            from app.core.config import settings
            timeout = getattr(settings, "REGEX_TIMEOUT_SECONDS", 2.0)

            matched, groups, extracted = _run_re_with_timeout(
                self._pattern_str, raw_event, timeout
            )
            if not matched:
                raise ParserError("Regex did not match the event")

        result = {}
        for capture_key, canonical_field in self.field_mappings.items():
            if capture_key in extracted:
                result[canonical_field] = extracted[capture_key]
            elif capture_key.startswith("capture_"):
                try:
                    idx = int(capture_key.split("_")[1]) - 1
                    if 0 <= idx < len(groups):
                        result[canonical_field] = groups[idx]
                except ValueError:
                    pass

        return result
