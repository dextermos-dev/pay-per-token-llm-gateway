"""
Agente 2: Verificador (agents/verificador.py)
Responsable de comprobar la vigencia, legitimidad, fiabilidad del organizador y estado activo del bounty.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from tools.scraper import scrape


class VerificationResult(BaseModel):
    bounty_id: str
    status: str  # VERIFICADO, PARCIALMENTE VERIFICADO, NO VERIFICADO, SOSPECHOSO, DESCARTADO
    is_active: bool
    legitimacy_score: float  # 0.0 a 10.0
    organizer_verified: bool
    payment_terms_clear: bool
    kyc_required: bool
    reasons: list


class VerificadorAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def verify_bounty(self, bounty: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la auditoría de vigencia y legitimidad sobre un candidato de bounty.
        """
        bounty_id = bounty.get("bounty_id", "unknown")
        url = bounty.get("url", "")
        reasons = []
        legitimacy_score = 5.0  # Base neutral

        # 1. Comprobar accesibilidad y vigencia pública de la URL
        if not url:
            return VerificationResult(
                bounty_id=bounty_id,
                status="DESCARTADO",
                is_active=False,
                legitimacy_score=0.0,
                organizer_verified=False,
                payment_terms_clear=False,
                kyc_required=False,
                reasons=["URL no especificada o inválida."]
            ).model_dump()

        scrape_res = scrape(source_url=url, legal_basis="Verificación de estado de bounty")
        
        if scrape_res.get("status") == "blocked":
            reasons.append("Acceso bloqueado por robots.txt o restricciones de dominio.")
            legitimacy_score -= 2.0
        elif scrape_res.get("status") != "success":
            return VerificationResult(
                bounty_id=bounty_id,
                status="DESCARTADO",
                is_active=False,
                legitimacy_score=1.0,
                organizer_verified=False,
                payment_terms_clear=False,
                kyc_required=False,
                reasons=[f"No se pudo acceder a la página fuente: {scrape_res.get('message')}"]
            ).model_dump()

        # 2. Análisis del contenido de la fuente para detectar estado de cierre
        page_text = (scrape_res.get("raw_text_snippet", "") + " " + bounty.get("description", "")).lower()
        
        closed_keywords = ["closed", "resuelto", "completed", "awarded", "bounty claimed", "finalizado"]
        is_closed = any(kw in page_text for kw in closed_keywords)
        
        if is_closed:
            return VerificationResult(
                bounty_id=bounty_id,
                status="DESCARTADO",
                is_active=False,
                legitimacy_score=0.0,
                organizer_verified=False,
                payment_terms_clear=False,
                kyc_required=False,
                reasons=["El bounty aparece marcado como cerrado, resuelto o adjudicado."]
            ).model_dump()

        # 3. Evaluar legitimidad del organizador y términos
        organizer_verified = False
        domain = bounty.get("platform", "").lower()
        if "github.com" in domain or "gitcoin" in domain or "code4rena" in domain:
            organizer_verified = True
            legitimacy_score += 3.0
            reasons.append("Organizador en plataforma de alta reputación.")

        payment_terms_clear = False
        if any(term in page_text for term in ["usd", "$", "usdt", "eth", "pago", "reward", "prize"]):
            payment_terms_clear = True
            legitimacy_score += 2.0
            reasons.append("Términos de recompensa claramente indicados.")

        kyc_required = "kyc" in page_text or "identity verification" in page_text
        if kyc_required:
            reasons.append("Requiere verificación KYC/KYB previo al pago (Exige supervisión humana).")

        # 4. Clasificación final
        legitimacy_score = min(10.0, max(0.0, legitimacy_score))
        
        if legitimacy_score >= 8.0:
            status_tag = "VERIFICADO"
        elif legitimacy_score >= 5.0:
            status_tag = "PARCIALMENTE VERIFICADO"
        elif legitimacy_score >= 3.0:
            status_tag = "NO VERIFICADO"
        else:
            status_tag = "SOSPECHOSO"

        return VerificationResult(
            bounty_id=bounty_id,
            status=status_tag,
            is_active=True,
            legitimacy_score=legitimacy_score,
            organizer_verified=organizer_verified,
            payment_terms_clear=payment_terms_clear,
            kyc_required=kyc_required,
            reasons=reasons
        ).model_dump()
