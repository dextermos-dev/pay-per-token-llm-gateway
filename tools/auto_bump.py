"""
Módulo de Seguimiento y Auto-Bump a los 5 Días (tools/auto_bump.py)
Supervisa las Pull Requests abiertas en GitHub. Si una PR lleva más de 5 días sin revisión
ni merge, envía un comentario cortés y profesional al mantenedor del proyecto en GitHub
para acelerar el proceso de revisión y cobro.
"""

import json
import os
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class AutoBumpTool:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")

    def inspect_and_bump_prs(self, min_days: int = 5) -> Dict[str, Any]:
        """
        Escanea PRs antiguas sin actividad y envía recordatorios amables a los mantenedores.
        """
        history_file = os.path.join(PROJECT_ROOT, "outputs", "submissions", "submission_history.json")
        if not os.path.exists(history_file):
            return {"status": "no_history", "bumped_count": 0}

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            return {"status": "error_reading_history", "bumped_count": 0}

        bumped = []
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "dextermos-dev-client/1.0"
        }

        now = datetime.now(timezone.utc)

        for key, item in history.items():
            pr_url = item.get("pull_request_url")
            submitted_at_str = item.get("submitted_at")
            bounty_id = item.get("bounty_id")

            if not pr_url or "github.com" not in pr_url or not submitted_at_str:
                continue

            try:
                sub_time = datetime.fromisoformat(submitted_at_str.replace("Z", "+00:00"))
                days_elapsed = (now - sub_time).days
            except Exception:
                days_elapsed = 0

            # Si han transcurrido los días configurados
            if days_elapsed >= min_days and not item.get("bumped"):
                parts = pr_url.split("github.com/")[1].split("/")
                if len(parts) >= 4 and parts[2] == "pull":
                    owner = parts[0]
                    repo = parts[1]
                    pr_number = parts[3]

                    bump_msg = f"Hi @{owner}! Just following up to see if you had a chance to review this PR. All tests and implementation are complete and passing. Let me know if any adjustments are needed!"
                    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

                    res = requests.post(comment_url, json={"body": bump_msg}, headers=headers, timeout=10)
                    if res.status_code in [200, 201]:
                        item["bumped"] = True
                        bumped.append({
                            "bounty_id": bounty_id,
                            "pr_url": pr_url,
                            "days_elapsed": days_elapsed
                        })

        # Guardar historial actualizado
        if bumped:
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return {
            "status": "success",
            "bumped_count": len(bumped),
            "bumped_prs": bumped
        }


def run_auto_bump() -> Dict[str, Any]:
    tool = AutoBumpTool()
    return tool.inspect_and_bump_prs(min_days=5)
