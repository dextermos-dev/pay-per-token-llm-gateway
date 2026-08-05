"""
Suite de Pruebas Automatizadas del Sistema Bounty Hunter AI v2.0
Verifica la funcionalidad e integración de todas las herramientas y los 10 subagentes.
"""

import json
import os
import unittest
from dotenv import load_dotenv

load_dotenv()

# Importar Herramientas
from tools import (
    WebSearchTool,
    ScraperTool,
    CodeExecutorTool,
    RepositoryManagerTool,
    SubmissionManagerTool
)

# Importar Subagentes
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


class TestBountyHunterSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = {
            "nivel_autonomia": "B",
            "categorias_permitidas": ["desarrollo", "codigo_abierto"],
            "tecnologias_dominadas": ["python", "typescript", "docker", "rest_api"],
            "recompensa_minima": 50,
            "api_keys": {
                "github": os.getenv("GITHUB_TOKEN", "")
            }
        }
        cls.sample_bounty = {
            "bounty_id": "test_bounty_999",
            "title": "Fix memory leak in parser utility",
            "url": "https://github.com/issues/test-bounty-999",
            "platform": "github_issues",
            "organizer": "github.com/example",
            "category": "desarrollo",
            "reward_amount": 150.0,
            "reward_currency": "USD",
            "technologies": ["python"],
            "description": "Fix memory leak, add pytest suite and Docker container support."
        }

    def test_01_tools_initialization(self):
        """Verifica que todas las herramientas se instancian correctamente."""
        self.assertIsNotNone(WebSearchTool())
        self.assertIsNotNone(ScraperTool())
        self.assertIsNotNone(CodeExecutorTool())
        self.assertIsNotNone(RepositoryManagerTool())
        self.assertIsNotNone(SubmissionManagerTool())

    def test_02_code_executor_sandbox(self):
        """Prueba la ejecución segura de código en el Sandbox."""
        executor = CodeExecutorTool()
        res = executor.execute(
            language="python",
            code="print('Hello Bounty Hunter AI')",
            timeout=10
        )
        self.assertEqual(res.get("status"), "success")
        self.assertIn("Hello Bounty Hunter AI", res.get("stdout"))
        self.assertTrue(res.get("sandboxed"))

    def test_03_subagents_pipeline(self):
        """Ejecuta la simulación completa de los 10 subagentes en cadena."""
        # 1. Radar
        radar = RadarAgent(config=self.config)
        self.assertIsNotNone(radar)

        # 2. Verificador
        verificador = VerificadorAgent(config=self.config)
        verif_res = verificador.verify_bounty(self.sample_bounty)
        self.assertIn("status", verif_res)

        # 3. Cumplimiento
        cumplimiento = CumplimientoAgent()
        audit_ethical = cumplimiento.audit_bounty_or_action(self.sample_bounty)
        self.assertFalse(audit_ethical.get("veto_applied"))

        # 4. Analista de Requisitos
        analista = AnalistaReqAgent(output_dir="outputs/matrix")
        matrix_res = analista.analyze_and_build_matrix(self.sample_bounty)
        self.assertEqual(matrix_res.get("status"), "success")
        self.assertTrue(os.path.exists(matrix_res.get("matrix_file")))

        # 5. Estratega
        estratega = EstrategaAgent(output_dir="outputs/viability")
        viab_res = estratega.evaluate_viability(self.sample_bounty)
        self.assertEqual(viab_res.get("analysis", {}).get("recommendation"), "SELECCIONADO")

        # 6. Arquitecto
        arquitecto = ArquitectoAgent(config=self.config)
        arch_res = arquitecto.design_solution(self.sample_bounty, matrix_res)
        self.assertEqual(arch_res.get("status"), "success")

        # 7. Constructor
        constructor = ConstructorAgent(config=self.config)
        build_res = constructor.build_and_test_solution(self.sample_bounty, arch_res.get("architecture_plan"))
        self.assertEqual(build_res.get("status"), "success")

        # 8. Red Team
        red_team = RedTeamAgent(config=self.config)
        red_res = red_team.audit_adversarial(self.sample_bounty, build_res.get("deliverable"))
        self.assertTrue(red_res.get("report", {}).get("passed_red_team"))

        # 9. Revisor
        revisor = RevisorAgent(config=self.config)
        rev_res = revisor.prepare_submission_package(
            self.sample_bounty, build_res.get("deliverable"), red_res.get("report")
        )
        self.assertEqual(rev_res.get("status"), "success")

        # 10. Auditor
        auditor = AuditorAgent(output_dir="outputs")
        final_audit = auditor.generate_final_audit(
            self.sample_bounty, matrix_res, build_res.get("deliverable")
        )
        self.assertTrue(final_audit.get("report", {}).get("final_audit_passed"))
        self.assertTrue(os.path.exists(final_audit.get("audit_file")))


if __name__ == "__main__":
    unittest.main()
