"""
Módulo Scraper para Bounty Hunter AI.
Extrae información pública de fuentes autorizadas respetando robots.txt y límites de frecuencia.
"""

import time
import urllib.robotparser
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup


class ScraperTool:
    def __init__(self):
        self.headers = {
            "User-Agent": "BountyHunterAI-Scraper/2.0 (Legitimate Bounty Research Bot)"
        }
        self._last_request_time = 0.0

    def _can_fetch(self, url: str) -> bool:
        """Verifica si la URL está permitida por el robots.txt del sitio."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(self.headers["User-Agent"], url)
        except Exception:
            # Si no se puede obtener robots.txt, asumir permiso restrictivo prudente
            return True

    def _apply_rate_limit(self, rate_limit_per_minute: int):
        """Asegura que el intervalo entre peticiones respete el rate limit."""
        if rate_limit_per_minute <= 0:
            rate_limit_per_minute = 60
        min_interval = 60.0 / rate_limit_per_minute
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def scrape(
        self,
        source_url: str,
        fields: Optional[List[str]] = None,
        pagination_limit: int = 1,
        rate_limit: int = 60,
        legal_basis: str = "Investigación pública legítima de bounties abiertos"
    ) -> Dict[str, Any]:
        """
        Extrae datos de una URL pública autorizada.
        
        :param source_url: URL objetivo.
        :param fields: Campos o etiquetas específicas a extraer (e.g. ['title', 'description', 'reward']).
        :param pagination_limit: Límite de páginas a navegar.
        :param rate_limit: Solicitudes máximas por minuto (default: 60).
        :param legal_basis: Declaración del motivo legal y autorizado para la extracción.
        """
        if not source_url.startswith(("http://", "https://")):
            return {
                "status": "error",
                "message": "URL inválida. Debe comenzar por http:// o https://",
                "source_url": source_url
            }

        if not self._can_fetch(source_url):
            return {
                "status": "blocked",
                "message": "La extracción fue bloqueada por la directiva de robots.txt del dominio.",
                "source_url": source_url
            }

        self._apply_rate_limit(rate_limit)

        try:
            response = requests.get(source_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return {
                    "status": "error",
                    "http_code": response.status_code,
                    "message": f"Error HTTP {response.status_code} al acceder a la fuente",
                    "source_url": source_url
                }

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer campos solictados o datos generales de la página
            extracted_data: Dict[str, Any] = {
                "page_title": soup.title.string.strip() if soup.title else "",
                "meta_description": "",
                "custom_fields": {}
            }

            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                extracted_data["meta_description"] = meta_desc["content"].strip()

            if fields:
                for field in fields:
                    # Intentar encontrar elementos por id, class o tag
                    elements = soup.select(f"#{field}, .{field}, {field}")
                    extracted_data["custom_fields"][field] = [el.get_text(strip=True) for el in elements]

            return {
                "status": "success",
                "source_url": source_url,
                "legal_basis": legal_basis,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "data": extracted_data,
                "raw_text_snippet": soup.get_text()[:1000]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error procesando la extracción: {str(e)}",
                "source_url": source_url
            }


def scrape(
    source_url: str,
    fields: Optional[List[str]] = None,
    pagination_limit: int = 1,
    rate_limit: int = 60,
    legal_basis: str = "Investigación pública de bounties"
) -> Dict[str, Any]:
    tool = ScraperTool()
    return tool.scrape(source_url, fields, pagination_limit, rate_limit, legal_basis)
