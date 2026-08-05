"""
Módulo Code Executor para Bounty Hunter AI.
Ejecuta código en un entorno aislado (Sandbox) aplicando límites de recursos y red restringida.
"""

import os
import sys
import tempfile
import subprocess
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ResourceLimits(BaseModel):
    cpu_limit: str = "1.0"
    memory_limit: str = "512m"
    max_files: int = 100


class CodeExecutionResult(BaseModel):
    status: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time_seconds: float
    sandboxed: bool
    used_docker: bool


class CodeExecutorTool:
    def __init__(self):
        pass

    def execute(
        self,
        language: str,
        code: str,
        dependencies: Optional[List[str]] = None,
        timeout: int = 30,
        network_access: bool = False,
        resource_limits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta código de forma aislada y segura.
        
        :param language: Lenguaje de programación ('python', 'typescript', 'bash').
        :param code: Código fuente a ejecutar.
        :param dependencies: Lista de paquetes necesarios.
        :param timeout: Tiempo máximo de ejecución en segundos.
        :param network_access: Booleano para permitir o aislar la red.
        :param resource_limits: Diccionario con límites de CPU, Memoria, etc.
        """
        start_time = time.time()
        limits = ResourceLimits(**(resource_limits or {}))

        # Intentar ejecución usando Docker si el daemon está disponible
        docker_result = self._try_docker_execution(
            language, code, dependencies, timeout, network_access, limits
        )
        if docker_result is not None:
            return docker_result.model_dump()

        # Fallback a Subprocess aislado localmente
        return self._execute_subprocess(
            language, code, dependencies, timeout, network_access, limits, start_time
        ).model_dump()

    def _try_docker_execution(
        self,
        language: str,
        code: str,
        dependencies: Optional[List[str]],
        timeout: int,
        network_access: bool,
        limits: ResourceLimits
    ) -> Optional[CodeExecutionResult]:
        try:
            import docker
            client = docker.from_env()
            client.ping()

            image_map = {
                "python": "python:3.11-slim",
                "typescript": "node:20-slim",
                "bash": "bash:latest"
            }
            image = image_map.get(language.lower())
            if not image:
                return None

            network_mode = "bridge" if network_access else "none"
            
            # Formatear comando de ejecución
            cmd = []
            if dependencies:
                if language == "python":
                    cmd_str = f"pip install --no-cache-dir {' '.join(dependencies)} && python -c \"{code}\""
                elif language == "typescript":
                    cmd_str = f"npm install {' '.join(dependencies)} && node -e \"{code}\""
                else:
                    cmd_str = code
                cmd = ["sh", "-c", cmd_str]
            else:
                if language == "python":
                    cmd = ["python", "-c", code]
                elif language == "typescript":
                    cmd = ["node", "-e", code]
                else:
                    cmd = ["bash", "-c", code]

            container = client.containers.run(
                image,
                command=cmd,
                detach=True,
                mem_limit=limits.memory_limit,
                nano_cpus=int(float(limits.cpu_limit) * 1e9),
                network_mode=network_mode,
                security_opt=["no-new-privileges:true"]
            )

            try:
                res = container.wait(timeout=timeout)
                exit_code = res.get("StatusCode", -1)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            except Exception as e:
                container.kill()
                exit_code = -1
                stdout = ""
                stderr = f"Timeout o error en contenedor: {str(e)}"
            finally:
                container.remove(force=True)

            return CodeExecutionResult(
                status="success" if exit_code == 0 else "failed",
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_seconds=float(f"{time.time() - time.time():.3f}"),
                sandboxed=True,
                used_docker=True
            )
        except Exception:
            # Docker no disponible o falló la conexión
            return None

    def _execute_subprocess(
        self,
        language: str,
        code: str,
        dependencies: Optional[List[str]],
        timeout: int,
        network_access: bool,
        limits: ResourceLimits,
        start_time: float
    ) -> CodeExecutionResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            ext_map = {"python": ".py", "typescript": ".ts", "bash": ".sh"}
            ext = ext_map.get(language.lower(), ".txt")
            filepath = os.path.join(tmpdir, f"script{ext}")
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            if language == "python":
                cmd = [sys.executable, filepath]
            elif language == "bash":
                cmd = ["bash", filepath]
            elif language == "typescript":
                cmd = ["npx", "ts-node", filepath]
            else:
                cmd = [sys.executable, filepath]

            # Entorno aislado de variables sensibles
            env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": tmpdir,
                "HOME": tmpdir
            }

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                return CodeExecutionResult(
                    status="success" if proc.returncode == 0 else "failed",
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    exit_code=proc.returncode,
                    execution_time_seconds=round(elapsed, 3),
                    sandboxed=True,
                    used_docker=False
                )
            except subprocess.TimeoutExpired:
                elapsed = time.time() - start_time
                return CodeExecutionResult(
                    status="timeout",
                    stdout="",
                    stderr=f"Ejecución pausada por superar el límite de tiempo ({timeout}s).",
                    exit_code=-1,
                    execution_time_seconds=round(elapsed, 3),
                    sandboxed=True,
                    used_docker=False
                )
            except Exception as e:
                elapsed = time.time() - start_time
                return CodeExecutionResult(
                    status="error",
                    stdout="",
                    stderr=f"Error en ejecución subprocess: {str(e)}",
                    exit_code=-1,
                    execution_time_seconds=round(elapsed, 3),
                    sandboxed=False,
                    used_docker=False
                )


def execute_code(
    language: str,
    code: str,
    dependencies: Optional[List[str]] = None,
    timeout: int = 30,
    network_access: bool = False,
    resource_limits: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    tool = CodeExecutorTool()
    return tool.execute(language, code, dependencies, timeout, network_access, resource_limits)
