"""
Agente 6: Arquitecto (agents/arquitecto.py)
Diseño de la solución, arquitectura limpia, descomposición en tareas y plan de pruebas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ArchitectureTask(BaseModel):
    task_id: str
    name: str
    description: str
    input_artifacts: List[str] = Field(default_factory=list)
    output_artifacts: List[str] = Field(default_factory=list)
    test_criteria: str = ""


class SolutionArchitecturePlan(BaseModel):
    bounty_id: str
    architecture_pattern: str = "Clean Architecture / Modular Design"
    components: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    tasks: List[ArchitectureTask] = Field(default_factory=list)
    test_plan: List[str] = Field(default_factory=list)
    optimization_priorities: List[str] = Field(default_factory=lambda: [
        "1. Cumplimiento de Requisitos",
        "2. Corrección",
        "3. Seguridad",
        "4. Reproducibilidad",
        "5. Mantenibilidad"
    ])


class ArquitectoAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def design_solution(
        self,
        bounty: Dict[str, Any],
        matrix: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Diseña la arquitectura y plan de resolución detallado para el bounty.
        """
        bounty_id = bounty.get("bounty_id", "unknown")
        title = bounty.get("title", "Solución de Bounty")
        
        # 1. Definir componentes principales
        components = [
            "core_logic",
            "utils_and_helpers",
            "test_suite",
            "documentation"
        ]

        # 2. Descomponer el plan en tareas modulares
        tasks = [
            ArchitectureTask(
                task_id="TASK-1",
                name="Setup de Entorno y Estructura Base",
                description="Crear archivos iniciales, dependencias y configuración en entorno aislado.",
                input_artifacts=["matrix_requirements.json"],
                output_artifacts=["src/main.py", "requirements.txt"],
                test_criteria="Verificar inicialización de dependencias y sintaxis."
            ),
            ArchitectureTask(
                task_id="TASK-2",
                name="Implementación de Funcionalidad Principal",
                description=f"Desarrollar lógica central para resolver: {title}",
                input_artifacts=["src/main.py"],
                output_artifacts=["src/core.py"],
                test_criteria="Ejecución funcional sin excepciones runtime."
            ),
            ArchitectureTask(
                task_id="TASK-3",
                name="Implementación de Suite de Pruebas Automatizadas",
                description="Crear pruebas unitarias y de integración cubriendo casos límite.",
                input_artifacts=["src/core.py"],
                output_artifacts=["tests/test_core.py"],
                test_criteria="100% de tests pasando en entorno sandbox."
            ),
            ArchitectureTask(
                task_id="TASK-4",
                name="Documentación y Empaquetado",
                description="Redactar README con instrucciones reproducibles de instalación y uso.",
                input_artifacts=["src/core.py", "tests/test_core.py"],
                output_artifacts=["README.md"],
                test_criteria="Pasos de instalación verificables de forma independiente."
            )
        ]

        test_plan = [
            "Pruebas unitarias de funciones base",
            "Prueba de integración en entorno aislado (sandbox)",
            "Prueba de casos límite (entradas nulas, límites de timeout)",
            "Prueba de análisis estático y seguridad"
        ]

        plan = SolutionArchitecturePlan(
            bounty_id=bounty_id,
            components=components,
            dependencies=self.config.get("tecnologias_dominadas", ["python"]),
            tasks=tasks,
            test_plan=test_plan
        )

        return {
            "status": "success",
            "architecture_plan": plan.model_dump()
        }
