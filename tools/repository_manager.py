"""
Módulo Repository Manager para Bounty Hunter AI.
Gestiona ramas, commits y pull requests en repositorios autorizados verificando la ausencia de secretos.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class RepositoryFileChange(BaseModel):
    path: str
    content: str


class RepositoryManagerTool:
    SECRET_PATTERNS = [
        r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        r"(?i)secret[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
        r"ghp_[A-Za-z0-9]{36}",
        r"glpat-[A-Za-z0-9\-]{20}",
        r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"  # JWT token pattern
    ]

    def __init__(self):
        pass

    def _scan_for_secrets(self, content: str) -> List[str]:
        """Detecta posibles claves o secretos en el contenido antes de permitir commits."""
        detected = []
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, content):
                detected.append(pattern)
        return detected

    def manage(
        self,
        repository: str,
        action: str,
        branch: str = "main",
        files: Optional[List[Dict[str, str]]] = None,
        commit_message: str = "auto: update repository solution",
        pull_request_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta acciones de control de versión sobre un repositorio.
        
        :param repository: Ruta local o URL del repositorio.
        :param action: Acción a realizar ('create_branch', 'commit', 'status', 'pull_request').
        :param branch: Nombre de la rama destino.
        :param files: Lista de archivos a modificar/crear, e.g. [{'path': 'src/main.py', 'content': '...'}]
        :param commit_message: Mensaje explicativo para el commit.
        :param pull_request_metadata: Metadatos para la PR (título, descripción, etc.).
        """
        # 1. Auditoría preventiva de secretos en los archivos a modificar
        if files:
            for f in files:
                filepath = f.get("path", "")
                content = f.get("content", "")
                secrets_found = self._scan_for_secrets(content)
                if secrets_found:
                    return {
                        "status": "blocked",
                        "reason": "SECRETS_DETECTED",
                        "message": f"Se detectó un posible secreto/credencial en {filepath}. Operación cancelada por seguridad.",
                        "file": filepath
                    }

        # 2. Ejecutar la acción correspondiente
        if action == "create_branch":
            return self._create_branch(repository, branch)
        elif action == "commit":
            return self._commit_files(repository, branch, files or [], commit_message)
        elif action == "status":
            return self._get_status(repository)
        elif action == "pull_request":
            return self._prepare_pull_request(repository, branch, pull_request_metadata or {}, commit_message)
        else:
            return {
                "status": "error",
                "message": f"Acción '{action}' no soportada. Acciones válidas: create_branch, commit, status, pull_request"
            }

    def _create_branch(self, repo_path: str, branch: str) -> Dict[str, Any]:
        if not os.path.exists(repo_path):
            return {"status": "error", "message": f"El repositorio {repo_path} no existe localmente."}

        res = subprocess.run(["git", "checkout", "-b", branch], cwd=repo_path, capture_output=True, text=True)
        if res.returncode != 0 and "already exists" in res.stderr:
            res = subprocess.run(["git", "checkout", branch], cwd=repo_path, capture_output=True, text=True)

        return {
            "status": "success" if res.returncode == 0 else "error",
            "branch": branch,
            "stdout": res.stdout,
            "stderr": res.stderr
        }

    def _commit_files(self, repo_path: str, branch: str, files: List[Dict[str, str]], commit_message: str) -> Dict[str, Any]:
        if not os.path.exists(repo_path):
            return {"status": "error", "message": f"Ruta de repositorio {repo_path} no válida."}

        changed_paths = []
        for f in files:
            rel_path = f["path"]
            full_path = os.path.join(repo_path, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as out:
                out.write(f["content"])
            changed_paths.append(rel_path)

        subprocess.run(["git", "add"] + changed_paths, cwd=repo_path, check=False)
        commit_res = subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, capture_output=True, text=True)

        return {
            "status": "success" if commit_res.returncode == 0 else "warning",
            "commit_message": commit_message,
            "files_changed": changed_paths,
            "stdout": commit_res.stdout,
            "stderr": commit_res.stderr
        }

    def _get_status(self, repo_path: str) -> Dict[str, Any]:
        if not os.path.exists(repo_path):
            return {"status": "error", "message": f"Ruta {repo_path} no existe."}
        res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
        return {
            "status": "success",
            "clean": len(res.stdout.strip()) == 0,
            "output": res.stdout
        }

    def _prepare_pull_request(self, repo_path: str, branch: str, metadata: Dict[str, Any], commit_msg: str) -> Dict[str, Any]:
        return {
            "status": "prepared",
            "repository": repo_path,
            "branch": branch,
            "pr_title": metadata.get("title", f"Fix/Feature for {branch}"),
            "pr_description": metadata.get("description", commit_msg),
            "requires_human_approval": True,
            "message": "Pull Request preparada con éxito. Requiere aprobación humana antes de realizar el envío."
        }


def manage_repository(
    repository: str,
    action: str,
    branch: str = "main",
    files: Optional[List[Dict[str, str]]] = None,
    commit_message: str = "auto: update repository solution",
    pull_request_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    tool = RepositoryManagerTool()
    return tool.manage(repository, action, branch, files, commit_message, pull_request_metadata)
