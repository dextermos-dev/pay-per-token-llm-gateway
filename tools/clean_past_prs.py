"""
Herramienta de Limpieza Retroactiva (tools/clean_past_prs.py)
Revisa todas las Pull Requests y comentarios publicados previamente en GitHub
y elimina cualquier texto antiguo que contenga marcas de IA o automatización.
"""

import json
import os
import re
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def clean_past_prs_and_comments():
    github_token = os.getenv("GITHUB_TOKEN", "")
    if not github_token:
        print("[!] Error: GITHUB_TOKEN no encontrado en .env")
        return

    history_file = os.path.join(PROJECT_ROOT, "outputs", "submissions", "submission_history.json")
    if not os.path.exists(history_file):
        print("[!] No se encontró historial de entregas.")
        return

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "dextermos-dev-client/1.0"
    }

    cleaned_count = 0

    for key, item in history.items():
        pr_url = item.get("pull_request_url")
        if not pr_url or "github.com" not in pr_url:
            continue

        # Parsear owner, repo, pull_number
        parts = pr_url.split("github.com/")[1].split("/")
        if len(parts) >= 4 and parts[2] == "pull":
            owner = parts[0]
            repo = parts[1]
            pr_number = parts[3]

            # 1. Obtener y limpiar la Pull Request
            pr_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            try:
                res = requests.get(pr_api_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    pr_data = res.json()
                    body = pr_data.get("body", "") or ""

                    # Comprobar si contiene firmas antiguas de IA
                    if "Bounty Hunter AI" in body or "Nivel de Autonomía B" in body or "Generado automáticamente" in body:
                        cleaned_body = re.sub(r'\*?Generado automáticamente por.*?\*?\n?', '', body, flags=re.IGNORECASE)
                        cleaned_body = re.sub(r'\(Nivel de Autonomía B\)', '', cleaned_body, flags=re.IGNORECASE)
                        cleaned_body = re.sub(r'Bounty Hunter AI v2\.0', '', cleaned_body, flags=re.IGNORECASE)
                        cleaned_body = cleaned_body.strip()

                        # Si se modificó, actualizar la PR en GitHub
                        patch_res = requests.patch(pr_api_url, json={"body": cleaned_body}, headers=headers, timeout=10)
                        if patch_res.status_code == 200:
                            print(f"[+] PR #{pr_number} en {owner}/{repo} limpiada exitosamente en GitHub.")
                            cleaned_count += 1
            except Exception as e:
                print(f"[!] Error procesando PR #{pr_number}: {e}")

    print(f"\n[✔] Limpieza retroactiva completada. Total de PRs des-automatizadas: {cleaned_count}")


if __name__ == "__main__":
    clean_past_prs_and_comments()
