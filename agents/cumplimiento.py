"""
Agente 5: Cumplimiento (agents/cumplimiento.py)
Auditor ético y legal con PODER DE VETO INMEDIATO ante violaciones de guardrails.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ComplianceAuditResult(BaseModel):
    is_compliant: bool
    veto_applied: bool
    prohibited_items_found: List[str]
    requires_human_approval: bool
    approval_reasons: List[str]
    summary: str


class CumplimientoAgent:
    def __init__(self, guardrails_path: str = "config/rules_guardrails.json"):
        self.guardrails_path = guardrails_path
        self._load_guardrails()

    def _load_guardrails(self):
        if os.path.exists(self.guardrails_path):
            with open(self.guardrails_path, "r", encoding="utf-8") as f:
                self.rules = json.load(f)
        else:
            self.rules = {
                "prohibiciones_absolutas": [
                    "malware", "ransomware", "doxxing", "elusion_de_captchas",
                    "acceso_no_autorizado", "robo_de_datos", "manipulacion_de_votos", "spam"
                ],
                "exige_aprobacion_humana": [
                    "enviar_submissions", "realizar_pagos", "aceptar_contratos",
                    "kyc_kyb", "pruebas_sobre_sistemas_reales"
                ]
            }

    def audit_bounty_or_action(
        self,
        bounty_or_action: Dict[str, Any],
        action_type: str = "evaluacion"
    ) -> Dict[str, Any]:
        """
        Audita un bounty o acción y aplica VETO INMEDIATO si se detecta cualquier prohibición.
        
        :param bounty_or_action: Diccionario con la información del bounty o la acción propuesta.
        :param action_type: Tipo de acción ('evaluacion', 'implementacion', 'submission', 'ejecucion').
        """
        text_corpus = (
            str(bounty_or_action.get("title", "")) + " " +
            str(bounty_or_action.get("description", "")) + " " +
            str(bounty_or_action.get("category", "")) + " " +
            str(bounty_or_action.get("code", "")) + " " +
            str(bounty_or_action.get("action", ""))
        ).lower()

        prohibitions = self.rules.get("prohibiciones_absolutas", [])
        human_approval_items = self.rules.get("exige_aprobacion_humana", [])

        detected_prohibitions = []
        approval_reasons = []

        # 1. Comprobación de Prohibiciones Absolutas (VETO)
        for p in prohibitions:
            p_clean = p.replace("_", " ").lower()
            if p_clean in text_corpus:
                detected_prohibitions.append(p)

        # 2. Comprobación de Requisito de Aprobación Humana
        for ha in human_approval_items:
            ha_clean = ha.replace("_", " ").lower()
            if ha_clean in text_corpus or action_type in ["submission", "pagos", "contratos"]:
                approval_reasons.append(f"Acción '{action_type}' marcada para aprobación humana por regla '{ha}'")

        veto_applied = len(detected_prohibitions) > 0
        is_compliant = not veto_applied

        if veto_applied:
            summary = f"VETO APLICADO INMEDIATAMENTE: Se detectaron prohibiciones absolutas {detected_prohibitions}."
        elif approval_reasons:
            summary = "APROBADO CON RESTRICCIÓN: Cumple guardrails éticos pero requiere aprobación humana explícita."
        else:
            summary = "CUMPLIMIENTO VERIFICADO: El bounty/acción es completamente transparente y legítimo."

        result = ComplianceAuditResult(
            is_compliant=is_compliant,
            veto_applied=veto_applied,
            prohibited_items_found=detected_prohibitions,
            requires_human_approval=len(approval_reasons) > 0,
            approval_reasons=approval_reasons,
            summary=summary
        )

        return result.model_dump()
