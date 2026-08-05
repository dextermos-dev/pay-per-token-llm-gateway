"""
Módulo de Contabilidad y Reportes Financieros Web3 (tools/financial_ledger.py).
Genera informes contables detallados en CSV, JSON y HTML/Imprimible para
seguimiento de ingresos, gastos de gas L2, beneficios netos y auditoría fiscal.
"""

import csv
import json
import os
import time
from typing import Dict, Any, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(PROJECT_ROOT, "dashboard", "data.json")
REPORT_DIR = os.path.join(PROJECT_ROOT, "outputs", "financial_reports")


class FinancialLedgerTool:
    def __init__(self):
        os.makedirs(REPORT_DIR, exist_ok=True)
        self.wallet = os.getenv("WEB3_WALLET_ADDRESS", "0x8366bCe3a2D379De7656D7A67015789FaF999f20")

    def load_dashboard_data(self) -> Dict[str, Any]:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"bounties": []}

    def generate_accounting_summary(self) -> Dict[str, Any]:
        return self.generate_full_financial_report()

    def export_csv_report(self) -> str:
        data = self.load_dashboard_data()
        bounties = data.get("bounties", [])
        
        csv_path = os.path.join(REPORT_DIR, "informe_contable_bounties.csv")
        fieldnames = [
            "ID_Bounty",
            "Fecha_Registro",
            "Nombre_Proyecto",
            "Recompensa_USDC",
            "Gas_Estimado_L2_USD",
            "Beneficio_Neto_USD",
            "Red_Blockchain",
            "Estado_Cobro",
            "Wallet_Receptora",
            "Pull_Request_URL",
            "Issue_URL"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for b in bounties:
                reward = float(b.get("reward_amount", 0.0))
                gas_fee = 0.05 if b.get("payment_network", "").lower() in ["base", "polygon", "arbitrum"] else 2.50
                net_profit = reward - gas_fee

                writer.writerow({
                    "ID_Bounty": b.get("bounty_id", ""),
                    "Fecha_Registro": time.strftime("%Y-%m-%d", time.localtime()),
                    "Nombre_Proyecto": b.get("title", ""),
                    "Recompensa_USDC": f"{reward:.2f}",
                    "Gas_Estimado_L2_USD": f"{gas_fee:.2f}",
                    "Beneficio_Neto_USD": f"{net_profit:.2f}",
                    "Red_Blockchain": b.get("payment_network", "Ethereum"),
                    "Estado_Cobro": b.get("payout_status", "EN_REVISION"),
                    "Wallet_Receptora": self.wallet,
                    "Pull_Request_URL": b.get("pull_request_url", ""),
                    "Issue_URL": b.get("url", "")
                })

        return csv_path

    def generate_full_financial_report(self) -> Dict[str, Any]:
        data = self.load_dashboard_data()
        bounties = data.get("bounties", [])

        total_pipeline = sum(float(b.get("reward_amount", 0.0)) for b in bounties)
        submitted_bounties = [b for b in bounties if b.get("pull_request_url")]
        submitted_val = sum(float(b.get("reward_amount", 0.0)) for b in submitted_bounties)
        paid_bounties = [b for b in bounties if b.get("payout_status") in ["COBRADO", "PAID"]]
        paid_val = sum(float(b.get("reward_amount", 0.0)) for b in paid_bounties)

        network_breakdown = {}
        for b in bounties:
            net = b.get("payment_network", "Ethereum")
            network_breakdown[net] = network_breakdown.get(net, 0.0) + float(b.get("reward_amount", 0.0))

        csv_file = self.export_csv_report()

        return {
            "status": "success",
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "wallet_receptora": self.wallet,
            "total_bounties_registrados": len(bounties),
            "pull_requests_activas": len(submitted_bounties),
            "total_potencial_usd": total_pipeline,
            "valor_en_revision_usd": submitted_val,
            "valor_cobrado_onchain_usd": paid_val,
            "desglose_por_red": network_breakdown,
            "csv_report_path": csv_file
        }


if __name__ == "__main__":
    tool = FinancialLedgerTool()
    report = tool.generate_full_financial_report()
    print("[+] Informe Financiero Generado:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
