# -*- coding: utf-8 -*-
"""
installer.py — Diagnóstico e instalación controlada de dependencias para GEEGPRPheno.

IMPORTANTE v1.3.0:
- El plugin NO instala paquetes automáticamente durante el arranque de QGIS.
- La instalación puede lanzarse manualmente desde el menú del plugin.
- Esto evita bucles de carga/reinicio, sobre todo en Windows/OSGeo4W.
"""
import sys
import importlib
import os
import subprocess
import shlex
from pathlib import Path

CORE_PACKAGES = {
    "numpy": "numpy>=1.21.0",
}

OPTIONAL_PACKAGES = {
    "rasterio": "rasterio>=1.3.0  (lectura/escritura GeoTIFF)",
    "ee": "earthengine-api>=0.1.370  (solo descarga/autenticación GEE)",
}

PIP_INSTALL_SPECS = [
    "earthengine-api>=0.1.370",
    "rasterio>=1.3.0",
]


def _add_user_site_to_path():
    """Agrega rutas de usuario a sys.path para que QGIS encuentre paquetes ya instalados."""
    try:
        import site
    except Exception:
        site = None

    paths_to_add = []
    user_site = os.path.expanduser(
        f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    paths_to_add.append(user_site)
    if site is not None:
        try:
            paths_to_add.append(site.getusersitepackages())
        except Exception:
            pass

    for p in paths_to_add:
        if p and p not in sys.path:
            sys.path.insert(0, p)


def _missing_packages(package_map):
    missing = []
    for module_name, pip_spec in package_map.items():
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append((module_name, pip_spec))
    return missing


def dependency_report():
    """Retorna diagnóstico simple de dependencias."""
    _add_user_site_to_path()
    rows = []
    for kind, pkg_map in (("requerida", CORE_PACKAGES), ("opcional", OPTIONAL_PACKAGES)):
        for module_name, pip_spec in pkg_map.items():
            try:
                m = importlib.import_module(module_name)
                ver = getattr(m, "__version__", "?")
                rows.append((kind, module_name, pip_spec, True, ver))
            except Exception:
                rows.append((kind, module_name, pip_spec, False, "NO instalada"))
    return rows


def qgis_python_executable():
    """Intenta localizar el Python correcto asociado a QGIS en Windows, macOS y Linux."""
    candidates = []
    exe = Path(sys.executable)
    candidates.append(exe)

    if sys.platform == "win32":
        osgeo = os.environ.get("OSGEO4W_ROOT") or os.environ.get("OSGEO4WROOT")
        if osgeo:
            candidates.extend([
                Path(osgeo) / "bin" / "python.exe",
                Path(osgeo) / "apps" / "Python312" / "python.exe",
                Path(osgeo) / "apps" / "Python311" / "python.exe",
                Path(osgeo) / "apps" / "Python39" / "python.exe",
            ])
        # Intentos comunes si QGIS fue instalado desde el instalador independiente.
        for root in [Path("C:/OSGeo4W"), Path("C:/OSGeo4W64"), Path("C:/Program Files/QGIS 3.40.1")]:
            candidates.extend([
                root / "bin" / "python.exe",
                root / "apps" / "Python312" / "python.exe",
                root / "apps" / "Python311" / "python.exe",
            ])
    elif sys.platform == "darwin":
        candidates.extend([
            Path("/Applications/QGIS.app/Contents/MacOS/bin/python3"),
            Path("/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3"),
        ])
    else:
        candidates.extend([Path("/usr/bin/python3"), Path("/usr/local/bin/python3")])

    for c in candidates:
        try:
            if c and c.exists() and c.is_file():
                return str(c)
        except Exception:
            continue
    return sys.executable


def install_command():
    """Comando pip recomendado para el Python activo de QGIS."""
    py = qgis_python_executable()
    cmd = [py, "-m", "pip", "install", "--upgrade", "pip"]
    cmd2 = [py, "-m", "pip", "install", "--upgrade"] + PIP_INSTALL_SPECS
    return cmd, cmd2


def _cmd_to_text(cmd):
    return " ".join(shlex.quote(str(x)) for x in cmd)


def manual_install_instructions():
    """Instrucciones conservadoras para instalar fuera del arranque del plugin."""
    cmd1, cmd2 = install_command()
    auto = _cmd_to_text(cmd1) + "\n" + _cmd_to_text(cmd2)
    if sys.platform == "win32":
        return (
            "WINDOWS / QGIS OSGeo4W\n"
            "Opción recomendada: usar el menú del plugin: 'Instalar/actualizar dependencias Python'.\n\n"
            "Instalación manual alternativa:\n"
            "1) Cierra QGIS completamente.\n"
            "2) Abre 'OSGeo4W Shell' desde el menú Inicio de Windows.\n"
            "3) Ejecuta:\n\n"
            f"   {auto}\n\n"
            "4) Abre QGIS nuevamente.\n\n"
            "Nota: evita instalar dependencias durante el arranque de QGIS."
        )
    if sys.platform == "darwin":
        return (
            "macOS / QGIS.app\n"
            "Opción recomendada: usar el menú del plugin: 'Instalar/actualizar dependencias Python'.\n\n"
            "Instalación manual alternativa:\n"
            "1) Cierra QGIS completamente.\n"
            "2) Abre Terminal.\n"
            "3) Ejecuta:\n\n"
            f"   {auto}\n\n"
            "4) Abre QGIS nuevamente."
        )
    return (
        "Linux / Ubuntu / Zorin\n"
        "Opción recomendada: usar el menú del plugin: 'Instalar/actualizar dependencias Python'.\n\n"
        "Instalación manual alternativa:\n"
        "1) Cierra QGIS completamente.\n"
        "2) Abre Terminal.\n"
        "3) Ejecuta:\n\n"
        f"   {auto}\n\n"
        "   # Si el sistema usa PEP 668 y rechaza pip:\n"
        f"   {_cmd_to_text([qgis_python_executable(), '-m', 'pip', 'install', '--upgrade', '--break-system-packages'] + PIP_INSTALL_SPECS)}\n\n"
        "4) Abre QGIS nuevamente."
    )


def run_dependency_install(log_path=None):
    """Ejecuta pip de forma explícita. No se llama automáticamente al arrancar QGIS."""
    cmd1, cmd2 = install_command()
    if log_path is None:
        log_path = os.path.join(Path.home(), "GEEGPRPheno_dependency_install.log")
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("GEEGPRPheno dependency installer\n")
        log.write(f"Python: {qgis_python_executable()}\n")
        for cmd in (cmd1, cmd2):
            log.write("\n$ " + _cmd_to_text(cmd) + "\n")
            log.flush()
            p = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
            log.write(f"\nexit_code={p.returncode}\n")
            if p.returncode != 0:
                return False, log_path, p.returncode
    _add_user_site_to_path()
    return True, log_path, 0


def check_and_install():
    """
    Verifica dependencias críticas sin instalar automáticamente.
    Las dependencias opcionales se diagnostican o instalan manualmente desde el menú.
    """
    _add_user_site_to_path()
    missing_core = _missing_packages(CORE_PACKAGES)
    if not missing_core:
        return True

    try:
        from qgis.PyQt.QtWidgets import QMessageBox
        txt = "\n".join(f"• {spec}" for _, spec in missing_core)
        QMessageBox.critical(
            None,
            "GEEGPRPheno — dependencia crítica faltante",
            "Faltan dependencias requeridas para cargar el plugin:\n\n"
            f"{txt}\n\n"
            "Instálalas manualmente fuera del arranque de QGIS.\n\n"
            + manual_install_instructions()
        )
    except Exception:
        pass
    return False


def verify_structure():
    """Imprime en la consola de QGIS el estado del plugin y sus dependencias."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "__init__.py", "plugin.py", "processing_provider.py",
        "s2boa_models.py", "gpr_algorithms.py", "algo_spectral_prediction.py",
        "algo_gapfilling.py", "algo_lsp.py", "algo_gee_pipeline.py",
        "metadata.txt", "requirements.txt", "installer.py", "qgis_utils.py",
    ]

    plat = {"win32": "Windows", "darwin": "macOS"}.get(sys.platform, "Linux/Zorin")
    print(f"\n=== GEEGPRPheno — Verificación ({plat} | Python {sys.version.split()[0]}) ===")
    all_ok = True
    for f in required_files:
        path = os.path.join(plugin_dir, f)
        exists = os.path.exists(path)
        status = "✓" if exists else "✗ FALTA"
        if not exists:
            all_ok = False
        print(f"  {status}  {f}")

    print("\n  --- Dependencias Python ---")
    for kind, mod, spec, ok, ver in dependency_report():
        status = "✓" if ok else "⚠"
        print(f"  {status}  {mod:<10} {ver:<15} [{kind}] {spec}")
    print("=" * 70 + "\n")
    return all_ok
