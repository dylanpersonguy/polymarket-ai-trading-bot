"""Alerting system — multi-channel notifications.

Sends alerts for:
  - Trade executions
  - Large P&L moves
  - Drawdown warnings
  - Kill switch activation
  - Error conditions
  - Daily summaries

Supported channels:
  - Console (always)
  - Telegram
  - Discord (webhook)
  - Slack (webhook)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.config import load_config
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class Alert:
    """An alert to be sent."""
    level: str  # "info" | "warning" | "critical"
    title: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    channels_sent: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class AlertManager:
    """Send alerts through configured channels."""

    def __init__(self, config: Any | None = None):
        cfg = config or load_config()
        self.alerts_config = cfg.alerts
        self._history: list[Alert] = []
        self._cooldowns: dict[str, float] = {}
        self._min_level = self.alerts_config.min_alert_level

    async def send(
        self,
        level: str,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        cooldown_key: str | None = None,
        cooldown_secs: float = 300,
    ) -> Alert:
        """Send an alert through all configured channels.

        Args:
            cooldown_key: If set, prevents duplicate alerts within cooldown_secs
        """
        # Check cooldown
        if cooldown_key:
            last_sent = self._cooldowns.get(cooldown_key, 0)
            if time.time() - last_sent < cooldown_secs:
                log.debug("alerts.cooldown", key=cooldown_key)
                return Alert(level=level, title=title, message="[cooldown]")
            self._cooldowns[cooldown_key] = time.time()

        # Check minimum level
        levels = {"info": 0, "warning": 1, "critical": 2}
        if levels.get(level, 0) < levels.get(self._min_level, 0):
            return Alert(level=level, title=title, message="[below min level]")

        alert = Alert(
            level=level,
            title=title,
            message=message,
            data=data or {},
        )

        # Always log to console
        log_fn = log.info if level == "info" else (
            log.warning if level == "warning" else log.critical
        )
        log_fn("alert.sent", level=level, title=title, message=message[:200])
        alert.channels_sent.append("console")

        # Send to configured channels
        if self.alerts_config.telegram_token and self.alerts_config.telegram_chat_id:
            try:
                await self._send_telegram(alert)
                alert.channels_sent.append("telegram")
            except Exception as e:
                log.error("alert.telegram_error", error=str(e))

        if self.alerts_config.discord_webhook:
            try:
                await self._send_discord(alert)
                alert.channels_sent.append("discord")
            except Exception as e:
                log.error("alert.discord_error", error=str(e))

        if self.alerts_config.slack_webhook:
            try:
                await self._send_slack(alert)
                alert.channels_sent.append("slack")
            except Exception as e:
                log.error("alert.slack_error", error=str(e))

        self._history.append(alert)
        if len(self._history) > 500:
            self._history = self._history[-250:]

        return alert

    async def _send_telegram(self, alert: Alert) -> None:
        """Send alert via Telegram Bot API."""
        import aiohttp

        token = self.alerts_config.telegram_token
        chat_id = self.alerts_config.telegram_chat_id
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(
            alert.level, "📢"
        )
        text = f"{emoji} *{alert.title}*\n\n{alert.message}"

        async with aiohttp.ClientSession() as session:
            await session.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=aiohttp.ClientTimeout(total=10),
            )

    async def _send_discord(self, alert: Alert) -> None:
        """Send alert via Discord webhook."""
        import aiohttp

        color = {
            "info": 0x3498DB,
            "warning": 0xF39C12,
            "critical": 0xE74C3C,
        }.get(alert.level, 0x95A5A6)

        payload = {
            "embeds": [{
                "title": alert.title,
                "description": alert.message,
                "color": color,
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(alert.timestamp)
                ),
            }]
        }

        async with aiohttp.ClientSession() as session:
            await session.post(
                self.alerts_config.discord_webhook,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            )

    async def _send_slack(self, alert: Alert) -> None:
        """Send alert via Slack webhook."""
        import aiohttp

        emoji = {"info": ":information_source:", "warning": ":warning:", "critical": ":rotating_light:"}.get(
            alert.level, ":bell:"
        )

        payload = {
            "text": f"{emoji} *{alert.title}*\n{alert.message}",
        }

        async with aiohttp.ClientSession() as session:
            await session.post(
                self.alerts_config.slack_webhook,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            )

    # Convenience methods

    async def trade_alert(
        self,
        market_id: str,
        question: str,
        direction: str,
        size_usd: float,
        edge: float,
    ) -> Alert:
        """Alert for a trade execution."""
        return await self.send(
            level="info",
            title="🎯 Trade Executed",
            message=(
                f"**{direction}** on: {question[:80]}\n"
                f"Size: ${size_usd:.2f} | Edge: {edge:.2%}"
            ),
            data={"market_id": market_id, "size": size_usd, "edge": edge},
        )

    async def drawdown_alert(
        self,
        drawdown_pct: float,
        heat_level: int,
        is_killed: bool,
    ) -> Alert:
        """Alert for drawdown events."""
        if is_killed:
            level = "critical"
            title = "🚨 KILL SWITCH ACTIVATED"
            msg = f"Drawdown reached {drawdown_pct:.1%}. All trading halted."
        elif heat_level >= 2:
            level = "warning"
            title = f"⚠️ Drawdown Heat Level {heat_level}"
            msg = f"Drawdown at {drawdown_pct:.1%}. Position sizing reduced."
        else:
            level = "info"
            title = f"📊 Drawdown Update"
            msg = f"Current drawdown: {drawdown_pct:.1%}"

        return await self.send(
            level=level,
            title=title,
            message=msg,
            cooldown_key=f"drawdown_{heat_level}",
            cooldown_secs=600,
        )

    async def pnl_alert(self, pnl: float, market_id: str, reason: str) -> Alert:
        """Alert for significant P&L events."""
        if pnl >= 0:
            emoji = "💰"
            level = "info"
        else:
            emoji = "📉"
            level = "warning" if abs(pnl) > 50 else "info"

        return await self.send(
            level=level,
            title=f"{emoji} P&L: ${pnl:+.2f}",
            message=f"Market: {market_id}\nReason: {reason}",
            data={"pnl": pnl, "market_id": market_id},
        )

    async def error_alert(self, error: str, context: str = "") -> Alert:
        """Alert for error conditions."""
        return await self.send(
            level="critical",
            title="❌ Error",
            message=f"{error}\n\nContext: {context}" if context else error,
            cooldown_key=f"error_{error[:50]}",
            cooldown_secs=300,
        )

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent alerts for dashboard."""
        return [a.to_dict() for a in self._history[-limit:]]
