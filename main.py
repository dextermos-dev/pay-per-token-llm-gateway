"""
Bounty Hunter AI — Orquestador Autónomo Principal (main.py)
Implementa el ciclo de vida 100% autónomo para ecosistemas Web3 y Smart Contracts.
Extrae tareas específicas del issue, genera archivos en src/ e realiza el reclamo (/claim)
y la entrega oficial vía la API de GitHub en Nivel B, marcando el estado final como SUBMITTED.
"""

import json
import os
import sys
import time
from typing import Dict, Any, List

from dotenv import load_dotenv

load_dotenv()

# Importar Suite de Herramientas
from tools import (
    WebSearchTool,
    ScraperTool,
    CodeExecutorTool,
    RepositoryManagerTool,
    SubmissionManagerTool,
    manage_submission
)

# Importar Suite de Subagentes
from agents import (
    RadarAgent,
    VerificadorAgent,
    AnalistaReqAgent,
    EstrategaAgent,
    CumplimientoAgent,
    ArquitectoAgent,
    ConstructorAgent,
    RedTeamAgent,
    RevisorAgent,
    AuditorAgent
)
from agents.auto_refinement import AutoRefinementAgent
from tools.telegram_notifier import notify_event


class BountyHunterOrchestrator:
    def __init__(
        self,
        config_path: str = "config/config.json",
        guardrails_path: str = "config/rules_guardrails.json"
    ):
        print("=== Inicializando Bounty Hunter AI (Versión 2.0 - Web3 100% Autónomo) ===")
        
        self.config = self._load_json(config_path)
        self.guardrails = self._load_json(guardrails_path)

        self.config["api_keys"] = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "github": os.getenv("GITHUB_TOKEN", ""),
            "serpapi": os.getenv("SERPAPI_KEY", ""),
            "tavily": os.getenv("TAVILY_API_KEY", "")
        }

        self.wallet_address = os.getenv("WEB3_WALLET_ADDRESS", "0x8366bCe3a2D379De7656D7A67015789FaF999f20")

        self.radar = RadarAgent(config=self.config)
        self.verificador = VerificadorAgent(config=self.config)
        self.analista_req = AnalistaReqAgent(output_dir="outputs/matrix")
        self.estratega = EstrategaAgent(output_dir="outputs/viability")
        self.cumplimiento = CumplimientoAgent(guardrails_path=guardrails_path)
        self.arquitecto = ArquitectoAgent(config=self.config)
        self.constructor = ConstructorAgent(config=self.config)
        self.red_team = RedTeamAgent(config=self.config)
        self.revisor = RevisorAgent(config=self.config)
        self.auditor = AuditorAgent(output_dir="outputs")
        self.submission_mgr = SubmissionManagerTool(log_dir="outputs/submissions")

        print(f"[*] Nivel de Autonomía Configurado: {self.config.get('nivel_autonomia', 'B')}")
        print(f"[*] Billetera Web3 de Cobro: {self.wallet_address}")
        print(f"[*] Categorías Permitidas: {self.config.get('categorias_permitidas', [])}")
        
        keys_status = [f"{k.upper()}: {'CONFIGURADO' if v and 'tu_' not in v else 'NO CONFIGURADO'}" for k, v in self.config["api_keys"].items()]
        print(f"[*] Estado de Llaves API (.env): {', '.join(keys_status)}")

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def run_pipeline(self):
        nivel_autonomia = self.config.get("nivel_autonomia", "B")
        print(f"\n--- PASO 1: Descubrimiento Web3 (Radar) [Nivel {nivel_autonomia}] ---")
        scan_res = self.radar.scan_bounties(max_results_per_query=10)
        candidates = scan_res.get("candidates", [])
        
        print(f"[+] Total de bounties reales descubiertos: {scan_res.get('total_real_discovered', 0)}")
        print(f"[+] Candidatos válidos con recompensa >= ${self.config.get('recompensa_minima', 100)} USDC: {scan_res.get('valid_reward_candidates', 0)}")

        if not candidates:
            print("\n[!] No se encontraron bounties en este momento que cumplan los filtros Web3.")
            return

        max_to_process = min(10, len(candidates))
        print(f"\n[*] Procesando los mejores {max_to_process} candidatos reales...")

        for idx, candidate in enumerate(candidates[:max_to_process], 1):
            b_id = candidate.get("bounty_id", f"bounty_{idx}")
            print(f"\n=======================================================")
            print(f"PROCESANDO BOUNTY REAL [{idx}/{max_to_process}]: {b_id}")
            print(f"Título: {candidate.get('title')}")
            print(f"URL: {candidate.get('url')}")
            print(f"Recompensa Estimada: ${candidate.get('reward_amount')} {candidate.get('reward_currency')}")
            print(f"=======================================================")

            # PASO 2: Verificación (Verificador)
            print("\n--- PASO 2: Verificación de Estado y Legitimidad (Verificador) ---")
            verif_res = self.verificador.verify_bounty(candidate)
            print(f"[*] Estado de Legitimidad: {verif_res.get('status')} | Score: {verif_res.get('legitimacy_score')}/10")
            
            if verif_res.get("status") == "DESCARTADO":
                print(f"[!] Bounty descartado por verificación.")
                continue

            # PASO 3: Auditoría Ética (Cumplimiento)
            print("\n--- PASO 3: Auditoría Ética y Guardrails (Cumplimiento) ---")
            audit_ethical = self.cumplimiento.audit_bounty_or_action(candidate)
            print(f"[*] Resultado Auditoría: {audit_ethical.get('summary')}")

            if audit_ethical.get("veto_applied"):
                print("[CRÍTICO] Veto aplicado. Abortando candidato.")
                continue

            # PASO 4: Extracción de Requisitos y Tareas Específicas (AnalistaReq)
            print("\n--- PASO 4: Matriz de Requisitos & Tareas Específicas (AnalistaReq) ---")
            matrix_res = self.analista_req.analyze_and_build_matrix(candidate)
            print(f"[+] Matriz guardada en: {matrix_res.get('matrix_file')}")
            print(f"[+] Tareas Específicas Extraídas: {[t.get('filename') for t in matrix_res.get('matrix', {}).get('specific_tasks', [])]}")

            # PASO 5: Scoring y Valor Esperado (Estratega)
            print("\n--- PASO 5: Scoring y Valor Esperado (Estratega) ---")
            viab_res = self.estratega.evaluate_viability(
                bounty=candidate,
                net_reward=candidate.get("reward_amount", 100.0)
            )
            analysis = viab_res.get("analysis", {})
            print(f"[*] Red de Pago: {analysis.get('payment_network')} | Gas Est: ${analysis.get('estimated_gas_cost_usd')} USD")
            print(f"[*] Puntuación Final: {analysis.get('final_score')}/10 | Valor Esperado: ${analysis.get('expected_value')}")

            if analysis.get("recommendation") == "DESCARTADO":
                print(f"[!] Candidato desestimado por viabilidad.")
                continue

            # PASO 6: Diseño de Arquitectura (Arquitecto)
            print("\n--- PASO 6: Diseño de Arquitectura (Arquitecto) ---")
            arch_res = self.arquitecto.design_solution(candidate, matrix_res)

            # PASO 7: Generación de Código y Pruebas Sandbox (Constructor)
            print("\n--- PASO 7: Generación de Solución en src/ y Sandbox (Constructor) ---")
            build_res = self.constructor.build_and_test_solution(
                bounty=candidate,
                architecture_plan=arch_res.get("architecture_plan", {}),
                matrix_data=matrix_res.get("matrix", {})
            )
            print(f"[*] Archivos Generados: {build_res.get('deliverable', {}).get('code_files', [])}")
            print(f"[*] Estado Sandbox: {build_res.get('status')}")

            # PASO 8: Auditoría Adversaria Interna (Red Team)
            print("\n--- PASO 8: Auditoría Adversaria Interna (Red Team) ---")
            red_team_res = self.red_team.audit_adversarial(candidate, build_res.get("deliverable", {}))
            passed_red_team = red_team_res.get("report", {}).get("passed_red_team", False)
            print(f"[*] Score Adversario: {red_team_res.get('report', {}).get('score_adversarial')}/10 | Pasa Red Team: {passed_red_team}")

            if not passed_red_team:
                print(f"[!] Candidato no superó las pruebas del Red Team. Pausando entrega.")
                continue

            # PASO 9: Formateo de Pull Request (Revisor)
            print("\n--- PASO 9: Formateo de Entrega (Revisor) ---")
            rev_res = self.revisor.prepare_submission_package(
                candidate,
                build_res.get("deliverable", {}),
                red_team_res.get("report", {})
            )

            # PASO 10: Matriz de Trazabilidad e Informe (Auditor)
            print("\n--- PASO 10: Matriz de Trazabilidad e Informe (Auditor) ---")
            final_audit = self.auditor.generate_final_audit(
                candidate,
                matrix_res,
                build_res.get("deliverable", {})
            )
            print(f"[+] Informe de Auditoría guardado en: {final_audit.get('audit_file')}")

            # PASO 11: Ejecución Automática: Reclamo (/claim), Publicación y Marcado SUBMITTED
            print(f"\n--- PASO 11: Reclamo (/claim), Publicación e Integración GitHub API (Nivel {nivel_autonomia}) ---")
            sub_res = self.submission_mgr.manage(
                platform=candidate.get("platform", "github_issues"),
                bounty_id=b_id,
                account_id="bounty_hunter_ai_v2",
                submission=rev_res.get("package", {}),
                action="presentar",
                nivel_autonomia=nivel_autonomia
            )
            print(f"[*] Estado Final de Entrega: {sub_res.get('status')}")
            print(f"[*] Mensaje de Ejecución: {sub_res.get('message')}")
            if sub_res.get("pull_request_url"):
                print(f"[🚀] Pull Request Oficial Publicada: {sub_res.get('pull_request_url')}")
            print(f"[*] Billetera Web3 Asociada: {sub_res.get('web3_wallet_address')}")
            print("\n[✔] Ciclo 100% autónomo completado con éxito para este candidato.")

        # Actualizar automáticamente el dataset consolidado del Dashboard Nivel Dios
        try:
            from dashboard.data_builder import update_dashboard_data_file
            update_dashboard_data_file()
        except Exception as e:
            print(f"[!] Aviso: No se pudo actualizar dashboard/data.json automáticamente: {e}")


def main():
    orchestrator = BountyHunterOrchestrator()
    orchestrator.run_pipeline()


if __name__ == "__main__":
    main()
