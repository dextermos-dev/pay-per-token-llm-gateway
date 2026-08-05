"""
Agente 8: Red Team Interno (agents/red_team.py)
Ejecución de pruebas adversarias internas, casos límite y simulación de objeciones del evaluador.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RedTeamFinding(BaseModel):
    issue_id: str
    severity: str  # ALTA, MEDIA, BAJA
    category: str  # CASO_LIMITE, SEGURIDAD, OBJECION_EVALUADOR, RENDIMIENTO
    description: str
    recommendation: str
    is_resolved: bool = False


class RedTeamAuditReport(BaseModel):
    bounty_id: str
    score_adversarial: float  # 0.0 a 10.0
    findings: List[RedTeamFinding] = Field(default_factory=list)
    evaluator_objections: List[str] = Field(default_factory=list)
    passed_red_team: bool


class RedTeamAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def audit_adversarial(
        self,
        bounty: Dict[str, Any],
        deliverable: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta pruebas adversarias sobre la solución y simula las objeciones del evaluador.
        """
        bounty_id = bounty.get("bounty_id", "unknown")
        findings: List[RedTeamFinding] = []
        objections: List[str] = []

        code_files = deliverable.get("code_files", [])
        main_code = ""
        if isinstance(code_files, dict):
            main_code = code_files.get("src/main.py", "")
        elif isinstance(code_files, list):
            main_code = " ".join(str(f) for f in code_files)

        # 1. Auditar manejo de casos límite
        if "None" not in main_code and "try" not in main_code:
            findings.append(RedTeamFinding(
                issue_id="RED-001",
                severity="MEDIA",
                category="CASO_LIMITE",
                description="La solución no contiene manejo explícito de excepciones try/except para entradas anómalas.",
                recommendation="Añadir bloques try/except alrededor de las llamadas de entrada/salida."
            ))
            objections.append("El evaluador podría rechazar la entrega si falla ante un input malformado.")

        # 2. Auditar secretos o valores hardcodeados
        if "password" in main_code.lower() or "secret" in main_code.lower():
            findings.append(RedTeamFinding(
                issue_id="RED-002",
                severity="ALTA",
                category="SEGURIDAD",
                description="Se encontraron variables de nombres sensibles en el código fuente.",
                recommendation="Utilizar variables de entorno a través de python-dotenv."
            ))
            objections.append("Inseguridad potencial: Se detectaron posibles credenciales expuestas.")

        # 3. Evaluar simplicidad e instalación
        if "README" not in deliverable.get("code_files", {}) and "doc" not in str(deliverable):
            findings.append(RedTeamFinding(
                issue_id="RED-003",
                severity="BAJA",
                category="OBJECION_EVALUADOR",
                description="Falta documentación explícita en el paquete entregable.",
                recommendation="Incluir un README.md detallado con ejemplos de ejecución."
            ))
            objections.append("Dificultad de evaluación: El revisor no encontrará instrucciones inmediatas.")

        high_severity_count = sum(1 for f in findings if f.severity == "ALTA")
        passed = (high_severity_count == 0)

        # Calcular nota adversaria (10 base menos penalizaciones)
        adversarial_score = max(0.0, 10.0 - (len(findings) * 1.5))

        report = RedTeamAuditReport(
            bounty_id=bounty_id,
            score_adversarial=adversarial_score,
            findings=findings,
            evaluator_objections=objections,
            passed_red_team=passed
        )

        return {
            "status": "passed" if passed else "rejected_by_red_team",
            "report": report.model_dump()
        }
