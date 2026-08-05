"""
Módulo de Notificaciones Telegram / Mobile Alerts (tools/telegram_notifier.py).
Envía alertas push en tiempo real con enlaces directos e identificación clara de proyectos.
"""

import json
import os
import requests
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TelegramNotifierTool:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def send_notification(self, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje formateado a Telegram si las llaves están configuradas.
        """
        if not self.bot_token or not self.chat_id or "tu_" in self.bot_token:
            return {
                "status": "disabled",
                "message": "Notificaciones de Telegram no configuradas en .env (opcional)."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }

        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return {"status": "sent", "response": res.json()}
            else:
                return {"status": "error", "code": res.status_code, "error": res.text}
        except Exception as e:
            return {"status": "error", "exception": str(e)}


def notify_event(title: str, body: str) -> Dict[str, Any]:
    tool = TelegramNotifierTool()
    msg = f"🚀 *Alerta de Entregas & Cobros Web3*\n\n*_{title}_*\n\n{body}"
    return tool.send_notification(msg)


def notify_bounty_event(title: str, reward_usd: float, issue_url: str, pr_url: Optional[str] = None) -> Dict[str, Any]:
    tool = TelegramNotifierTool()
    msg = (
        f"🚀 *NUEVO BOUNTY EN VIVO DETECTADO*\n\n"
        f"📌 *Proyecto*: `{title[:60]}`\n"
        f"💰 *Recompensa*: `${reward_usd:,.2f} USDC`\n"
        f"🔗 *Issue Original*: [Abrir Issue en GitHub]({issue_url})\n"
    )
    if pr_url:
        msg += f"🚀 *Pull Request Oficial*: [Abrir PR en GitHub]({pr_url})\n"
    msg += f"💳 *Wallet Receptor*: `0x8366bCe3a2D379De7656D7A67015789FaF999f20`"
    return tool.send_notification(msg)
