"""
Módulo de Subagentes para Bounty Hunter AI.
Exporta la suite completa de los 10 subagentes especialistas del orquestador:
1. RadarAgent (Agente 1)
2. VerificadorAgent (Agente 2)
3. AnalistaReqAgent (Agente 3)
4. EstrategaAgent (Agente 4)
5. CumplimientoAgent (Agente 5)
6. ArquitectoAgent (Agente 6)
7. ConstructorAgent (Agente 7)
8. RedTeamAgent (Agente 8)
9. RevisorAgent (Agente 9)
10. AuditorAgent (Agente 10)
"""

from .radar import RadarAgent, BountyCandidate
from .verificador import VerificadorAgent, VerificationResult
from .analista_req import AnalistaReqAgent, RequirementMatrix
from .estratega import EstrategaAgent, ViabilityAnalysis, ScoringDimensions
from .cumplimiento import CumplimientoAgent, ComplianceAuditResult
from .arquitecto import ArquitectoAgent, SolutionArchitecturePlan
from .constructor import ConstructorAgent, BuildDeliverable
from .red_team import RedTeamAgent, RedTeamAuditReport
from .revisor import RevisorAgent, SubmissionPackage
from .auditor import AuditorAgent, FinalAuditReport

__all__ = [
    "RadarAgent",
    "BountyCandidate",
    "VerificadorAgent",
    "VerificationResult",
    "AnalistaReqAgent",
    "RequirementMatrix",
    "EstrategaAgent",
    "ViabilityAnalysis",
    "ScoringDimensions",
    "CumplimientoAgent",
    "ComplianceAuditResult",
    "ArquitectoAgent",
    "SolutionArchitecturePlan",
    "ConstructorAgent",
    "BuildDeliverable",
    "RedTeamAgent",
    "RedTeamAuditReport",
    "RevisorAgent",
    "SubmissionPackage",
    "AuditorAgent",
    "FinalAuditReport"
]
