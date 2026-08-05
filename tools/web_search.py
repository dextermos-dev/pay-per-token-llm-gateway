"""
Modulo de Búsqueda Web para Bounty Hunter AI.
Permite buscar bounties e información pública en internet respetando reglas de veracidad y procedencia.
"""

import time
from typing import List, Dict, Any, Optional
import requests
from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source_domain: str
    retrieved_at: str
    verification_status: str = "NO VERIFICADO"


class WebSearchTool:
    def __init__(self):
        self.headers = {
            "User-Agent": "BountyHunterAI-SearchBot/2.0 (Research & Automated Bounty Hunter)"
        }

    def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        language: str = "es",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Ejecuta una búsqueda pública de bounties.
        
        :param query: Consulta de búsqueda específica.
        :param domains: Dominios permitidos o prioritarios (e.g. ['github.com', 'gitcoin.co']).
        :param date_range: Intervalo temporal, e.g. {'start': '2026-01-01', 'end': '2026-08-04'}.
        :param language: Idioma preferido ('es', 'en').
        :param max_results: Número máximo de resultados a retornar.
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Enriquecer la consulta con dominios si fueron especificados
        full_query = query
        if domains:
            domain_filter = " OR ".join([f"site:{d}" for d in domains])
            full_query = f"{query} ({domain_filter})"
            
        results: List[WebSearchResult] = []
        
        # Intentar consultar API o motores públicos estructurados con fallback robusto
        try:
            # Simulación de respuesta estructurada normalizada para entornos de desarrollo / API integraciones
            results_data = self._execute_http_search(full_query, language, max_results)
            for item in results_data:
                results.append(WebSearchResult(
                    title=item.get("title", "Sin título"),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source_domain=item.get("domain", "desconocido"),
                    retrieved_at=timestamp,
                    verification_status="NO VERIFICADO"
                ))
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error ejecutando búsqueda: {str(e)}",
                "query": full_query,
                "results": []
            }
            
        return {
            "status": "success",
            "query": full_query,
            "date_range": date_range,
            "language": language,
            "total_results": len(results),
            "results": [r.model_dump() for r in results]
        }

    def _execute_http_search(self, query: str, language: str, max_results: int) -> List[Dict[str, str]]:
        # Método auxiliar de búsqueda con fallback a servicios abiertos (e.g. DuckDuckGo HTML / API)
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "kl": f"{language}-{language}"}
        
        response = requests.post(url, data=data, headers=self.headers, timeout=10)
        if response.status_code != 200:
            return []
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        extracted = []
        for result in soup.find_all("div", class_="result")[:max_results]:
            title_tag = result.find("a", class_="result__a")
            snippet_tag = result.find("a", class_="result__snippet")
            if title_tag:
                link = title_tag.get("href", "")
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                domain = link.split("/")[2] if "://" in link else "desconocido"
                extracted.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet,
                    "domain": domain
                })
        return extracted


def web_search(
    query: str,
    domains: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    language: str = "es",
    max_results: int = 10
) -> Dict[str, Any]:
    tool = WebSearchTool()
    return tool.search(query, domains, date_range, language, max_results)
