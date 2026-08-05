"""
Agente 3: Analista de Requisitos (agents/analista_req.py)
Extracción de requisitos y generación de la Matriz de Requisitos (Obligatorio, Deseable, Implícito, Ambiguo).
Analiza el cuerpo completo del issue (body) para extraer tareas específicas (contratos, tests, esquemas técnicos)
y guardar la matriz en JSON UTF-8 con sangría de 2 espacios.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class RequirementItem(BaseModel):
    id: str
    requirement: str
    source: str
    type: str  # OBLIGATORIO, DESEABLE, IMPLICITO, AMBIGUO
    priority: str
    status: str
    validation_method: str
    expected_evidence: str
    risk_level: str


class RequirementMatrix(BaseModel):
    bounty_id: str
    platform: str
    total_requirements: int
    mandatory_count: int
    desirable_count: int
    implicit_count: int
    ambiguous_count: int
    requirements: List[RequirementItem] = Field(default_factory=list)
    specific_tasks: List[Dict[str, Any]] = Field(default_factory=list)


class AnalistaReqAgent:
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir:
            self.output_dir = os.path.abspath(output_dir) if os.path.isabs(output_dir) else os.path.join(PROJECT_ROOT, output_dir)
        else:
            self.output_dir = os.path.join(PROJECT_ROOT, "outputs", "matrix")
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_and_build_matrix(self, bounty: Dict[str, Any]) -> Dict[str, Any]:
        bounty_id = bounty.get("bounty_id", "unknown")
        platform = bounty.get("platform", "github_issues")
        title = bounty.get("title", "")
        description = bounty.get("description", "")
        full_text = f"{title} {description}".lower()

        reqs: List[RequirementItem] = []

        # 1. Requisitos Obligatorios
        reqs.append(RequirementItem(
            id="REQ-01",
            requirement=f"Resolver la funcionalidad descrita en '{title}'",
            source="Issue Description (body)",
            type="OBLIGATORIO",
            priority="ALTA",
            status="PENDIENTE",
            validation_method="Sandbox Execution & Unit Tests",
            expected_evidence="Suite de pruebas en verde y código en src/",
            risk_level="MEDIO"
        ))

        reqs.append(RequirementItem(
            id="REQ-02",
            requirement="Garantizar compatibilidad con versiones y dependencias Web3/Python/Solidity",
            source="Project Stack Specs",
            type="OBLIGATORIO",
            priority="ALTA",
            status="PENDIENTE",
            validation_method="Docker Isolation",
            expected_evidence="Contenedor Sandbox compilado sin warnings",
            risk_level="BAJO"
        ))

        # 2. Requisitos Deseables
        reqs.append(RequirementItem(
            id="REQ-03",
            requirement="Optimización de código y documentación técnica clara en README/Schema",
            source="Best Practices",
            type="DESEABLE",
            priority="MEDIA",
            status="PENDIENTE",
            validation_method="Static Analysis",
            expected_evidence="Comentarios limpios y reporte de arquitectura",
            risk_level="BAJO"
        ))

        # 3. Requisitos Implícitos
        reqs.append(RequirementItem(
            id="REQ-04",
            requirement="Ausencia total de secretos, llaves privadas o vulnerabilidades conocidas",
            source="Security Guardrails (AGENTS.md)",
            type="IMPLICITO",
            priority="CRITICA",
            status="PENDIENTE",
            validation_method="Red Team Audit",
            expected_evidence="Red Team Audit Score >= 8.0/10",
            risk_level="ALTO"
        ))

        # Detección de tareas específicas basadas en el prompt del issue
        specific_tasks = []
        if "contract" in full_text or "solidity" in full_text:
            specific_tasks.append({
                "type": "smart_contract",
                "filename": f"src/contract_{bounty_id}.sol",
                "description": "Desarrollar y verificar contrato inteligente Solidity."
            })
        if "test" in full_text or "contract test" in full_text:
            specific_tasks.append({
                "type": "test_suite",
                "filename": f"tests/test_{bounty_id}.py",
                "description": "Implementar suite de pruebas E2E automatizada."
            })
        if "schema" in full_text or "refactor" in full_text or "inventory" in full_text:
            specific_tasks.append({
                "type": "technical_schema",
                "filename": f"src/technical_schema_{bounty_id}.md",
                "description": "Redactar esquema técnico y arquitectura del subsistema."
            })

        if not specific_tasks:
            specific_tasks.append({
                "type": "code_solution",
                "filename": f"src/solution_{bounty_id}.py",
                "description": "Generar implementación principal de la solución."
            })

        matrix = RequirementMatrix(
            bounty_id=bounty_id,
            platform=platform,
            total_requirements=len(reqs),
            mandatory_count=2,
            desirable_count=1,
            implicit_count=1,
            ambiguous_count=0,
            requirements=reqs,
            specific_tasks=specific_tasks
        )

        # Guardar en archivo JSON UTF-8
        os.makedirs(self.output_dir, exist_ok=True)
        matrix_file = os.path.join(self.output_dir, f"matrix_{bounty_id}.json")
        with open(matrix_file, "w", encoding="utf-8") as out:
            json.dump(matrix.model_dump(), out, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "matrix_file": matrix_file,
            "matrix": matrix.model_dump()
        }


def extract_requirements(bounty: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, Any]:
    agent = AnalistaReqAgent(output_dir=output_dir)
    return agent.analyze_and_build_matrix(bounty)
