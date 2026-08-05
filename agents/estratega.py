"""
Agente 4: Estratega (agents/estratega.py)
Implementación del scoring ponderado de 14 dimensiones y la función del Valor Esperado (EV)
enfocada en ecosistemas Web3 y Smart Contracts, incluyendo la verificación de la red de pago
(Ethereum, Polygon, Arbitrum, Optimism) y estimación de gas/costes de red.
"""

import json
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SUPPORTED_NETWORKS = {
    "ethereum": {"reliability": 1.0, "estimated_gas_usd": 15.0},
    "base": {"reliability": 0.99, "estimated_gas_usd": 0.05},
    "polygon": {"reliability": 0.98, "estimated_gas_usd": 0.05},
    "arbitrum": {"reliability": 0.99, "estimated_gas_usd": 0.10},
    "optimism": {"reliability": 0.99, "estimated_gas_usd": 0.10}
}


class ViabilityScore(BaseModel):
    legitimacy: float = 10.0
    clarity: float = 8.0
    fit: float = 9.0
    viability_tech: float = 8.5
    viability_time: float = 8.0
    payment_reliability: float = 9.0
    reward_attractiveness: float = 8.5
    prob_winning: float = 8.0
    differentiation: float = 7.5
    reputation_val: float = 7.0
    reusability: float = 8.0
    risk_total: float = 2.0
    competition_level: float = 3.0
    operating_cost: float = 2.0


# Aliases para compatibilidad de importación
ScoringDimensions = ViabilityScore


class ViabilityAnalysis(BaseModel):
    bounty_id: str
    final_score: float
    expected_value: float
    recommendation: str
    payment_network: str


class EstrategaAgent:
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir:
            self.output_dir = os.path.abspath(output_dir) if os.path.isabs(output_dir) else os.path.join(PROJECT_ROOT, output_dir)
        else:
            self.output_dir = os.path.join(PROJECT_ROOT, "outputs", "viability")
        os.makedirs(self.output_dir, exist_ok=True)

    def verify_payment_network(self, network_name: Optional[str]) -> Dict[str, Any]:
        """
        Verifica la red de pago (Ethereum, Polygon, Arbitrum, Optimism)
        y devuelve el factor de confiabilidad y coste de gas estimado.
        """
        net_key = (network_name or "ethereum").lower().strip()
        if net_key in SUPPORTED_NETWORKS:
            info = SUPPORTED_NETWORKS[net_key]
            return {
                "verified": True,
                "network": net_key.capitalize(),
                "reliability_multiplier": info["reliability"],
                "estimated_gas_usd": info["estimated_gas_usd"]
            }
        else:
            return {
                "verified": False,
                "network": net_key.capitalize() if net_key else "Ethereum",
                "reliability_multiplier": 0.90,
                "estimated_gas_usd": 10.0
            }

    def evaluate_viability(
        self,
        bounty: Dict[str, Any],
        net_reward: float = 100.0,
        prob_acceptance: float = 0.85,
        prob_payment: float = 0.95,
        costs: float = 5.0,
        risk_penalty: float = 10.0,
        opportunity_cost: float = 15.0
    ) -> Dict[str, Any]:
        """
        Calcula la puntuación ponderada y el Valor Esperado (EV) incluyendo la verificación de la red de pago.
        Fórmula EV Web3:
        EV = (RecompensaNeta * P_Aceptacion * P_Cobro * NetworkReliability) - GasEst - Costes - PenalizacionRiesgo - CosteOportunidad
        """
        bounty_id = bounty.get("bounty_id", "unknown")
        reward_currency = bounty.get("reward_currency", "USDC")
        raw_reward = bounty.get("reward_amount", net_reward)
        payment_net_input = bounty.get("payment_network", "Ethereum")

        # Verificación de la Red de Pago Web3
        net_audit = self.verify_payment_network(payment_net_input)
        net_reliability = net_audit["reliability_multiplier"]
        gas_cost = net_audit["estimated_gas_usd"]

        scores = ViabilityScore()
        
        # Puntuación Base
        base_score = (
            (scores.legitimacy * 0.12) +
            (scores.clarity * 0.08) +
            (scores.fit * 0.12) +
            (scores.viability_tech * 0.10) +
            (scores.viability_time * 0.08) +
            (scores.payment_reliability * 0.10) +
            (scores.reward_attractiveness * 0.10) +
            (scores.prob_winning * 0.12) +
            (scores.differentiation * 0.06) +
            (scores.reputation_val * 0.05) +
            (scores.reusability * 0.07)
        )

        # Penalizaciones
        penalties = (
            (scores.risk_total * 0.07) +
            (scores.competition_level * 0.04) +
            (scores.operating_cost * 0.04)
        )

        final_score = round(base_score - penalties, 2)

        # Función del Valor Esperado Web3
        expected_value = (
            (raw_reward * prob_acceptance * prob_payment * net_reliability)
            - gas_cost
            - costs
            - risk_penalty
            - opportunity_cost
        )
        expected_value = round(max(expected_value, 0.0), 2)

        recommendation = "SELECCIONADO" if final_score >= 5.0 and expected_value > 0 else "DESCARTADO"

        analysis_report = {
            "bounty_id": bounty_id,
            "title": bounty.get("title", ""),
            "reward_amount": raw_reward,
            "reward_currency": reward_currency,
            "payment_network_verified": net_audit["verified"],
            "payment_network": net_audit["network"],
            "network_reliability_multiplier": net_reliability,
            "estimated_gas_cost_usd": gas_cost,
            "base_score": round(base_score, 2),
            "penalties": round(penalties, 2),
            "final_score": final_score,
            "expected_value": expected_value,
            "recommendation": recommendation,
            "details": scores.model_dump()
        }

        # Guardar informe JSON
        os.makedirs(self.output_dir, exist_ok=True)
        viability_file = os.path.join(self.output_dir, f"viability_{bounty_id}.json")
        with open(viability_file, "w", encoding="utf-8") as out:
            json.dump(analysis_report, out, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "viability_file": viability_file,
            "analysis": analysis_report
        }


def evaluate_bounty_viability(bounty: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, Any]:
    agent = EstrategaAgent(output_dir=output_dir)
    return agent.evaluate_viability(bounty)
