from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Deque, Dict

from app.core.constants import (
    ANTIBRUTE_MAX_ATTEMPTS, ANTIBRUTE_WINDOW_SEC,
    ANTIBRUTE_BLOCK_SEC, ANTIBRUTE_FAIL_DELAY
)

log = logging.getLogger("admin_auth.antibrute")


class AntiBrute:
    """
    Очень простой in-memory анти-brютфорс.
    Считает неудачные попытки для ключа (ip|email) в окне времени.
    При превышении порога — блокирует на BLOCK_SEC.
    """

    def __init__(
        self,
        max_attempts: int = ANTIBRUTE_MAX_ATTEMPTS,
        window_sec: int = ANTIBRUTE_WINDOW_SEC,
        block_sec: int = ANTIBRUTE_BLOCK_SEC,
        fail_delay: float = ANTIBRUTE_FAIL_DELAY,
    ) -> None:
        self.MAX_ATTEMPTS = max_attempts
        self.WINDOW_SEC = window_sec
        self.BLOCK_SEC = block_sec
        self.FAIL_DELAY = fail_delay
        self._attempts: Dict[str, Deque[float]] = {}
        self._blocked_until: Dict[str, float] = {}

    @staticmethod
    def key(ip: str | None, email: str) -> str:
        return f"{(ip or 'unknown').strip()}|{email.strip().lower()}"

    def is_blocked(self, key: str, now: float | None = None) -> bool:
        now = now or time.time()
        return now < self._blocked_until.get(key, 0.0)

    def _clean_old(self, key: str, now: float) -> None:
        dq = self._attempts.get(key)
        if not dq:
            return
        border = now - self.WINDOW_SEC
        while dq and dq[0] <= border:
            dq.popleft()

    async def fail(self, key: str) -> None:
        """Отмечаем неудачу и чуть замедляем ответ (усложняет перебор)."""
        now = time.time()
        dq = self._attempts.setdefault(key, deque())
        self._clean_old(key, now)
        dq.append(now)

        if len(dq) >= self.MAX_ATTEMPTS:
            self._blocked_until[key] = now + self.BLOCK_SEC
            dq.clear()
            log.warning("antibrute: BLOCK key=%s for=%ss", key, self.BLOCK_SEC)

        if self.FAIL_DELAY > 0:
            await asyncio.sleep(self.FAIL_DELAY)

    def ok(self, key: str) -> None:
        """Сбрасываем счётчики на успешном входе."""
        self._attempts.pop(key, None)
        self._blocked_until.pop(key, None)


anti_brute = AntiBrute()
