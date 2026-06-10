# -*- coding: utf-8 -*-
"""
installer.py — Diagnostico seguro de dependencias para GEEGPRPheno.

IMPORTANTE v1.2.1:
No instala paquetes automaticamente durante el arranque de QGIS. La instalacion
mediante pip dentro del ciclo de carga del plugin puede dejar QGIS en un bucle de
reinicios/cargas incompletas, especialmente en Windows/OSGeo4W.
"""
import sys
import importlib
import os

# Dependencias que se importan al cargar el plugin. Si faltan, el plugin no puede
# iniciar. En QGIS normalmente numpy ya viene instalado.
CORE_PACKAGES = {
    "numpy": "numpy>=1.21.0",
}

# Dependencias usadas solo cuando se ejecutan ciertos algoritmos.
OPTIONAL_PACKAGES = {
    "rasterio": "rasterio>=1.3.0  (lectura/escritura GeoTIFF)",
    "ee": "earthengine-api>=0.1.370  (solo descarga/autenticacion GEE)",
}


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
    """Retorna un diagnostico simple de dependencias."""
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


def manual_install_instructions():
    """Instrucciones conservadoras para instalar fuera del arranque del plugin."""
    if sys.platform == "win32":
        return (
            "WINDOWS / QGIS OSGeo4W\n"
            "1) Cierra QGIS completamente.\n"
            "2) Abre 'OSGeo4W Shell' desde el menu Inicio de Windows.\n"
            "3) Ejecuta:\n\n"
            "   python -m pip install --upgrade pip\n"
            "   python -m pip install earthengine-api rasterio\n\n"
            "4) Abre QGIS nuevamente.\n\n"
            "Nota: evita instalar desde el dialogo de arranque del plugin."
        )
    if sys.platform == "darwin":
        return (
            "macOS / QGIS.app\n"
            "1) Cierra QGIS completamente.\n"
            "2) Abre Terminal.\n"
            "3) Ejecuta con el Python de QGIS, por ejemplo:\n\n"
            "   /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install earthengine-api rasterio\n\n"
            "4) Abre QGIS nuevamente."
        )
    return (
        "Linux / Ubuntu / Zorin\n"
        "1) Cierra QGIS completamente.\n"
        "2) Abre Terminal.\n"
        "3) Ejecuta:\n\n"
        "   python3 -m pip install --user earthengine-api rasterio\n\n"
        "   # Si el sistema usa PEP 668:\n"
        "   python3 -m pip install --user --break-system-packages earthengine-api rasterio\n\n"
        "4) Abre QGIS nuevamente."
    )


def check_and_install():
    """
    Verifica dependencias criticas sin instalar automaticamente.

    Retorna True si el plugin puede cargar. Si falta una dependencia realmente
    critica, muestra un mensaje y retorna False. Las dependencias opcionales se
    diagnostican desde el menu del plugin o al ejecutar el algoritmo correspondiente.
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
            "GEEGPRPheno — dependencia critica faltante",
            "Faltan dependencias requeridas para cargar el plugin:\n\n"
            f"{txt}\n\n"
            "Instalalas manualmente fuera del arranque de QGIS.\n\n"
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
    print(f"\n=== GEEGPRPheno — Verificacion ({plat} | Python {sys.version.split()[0]}) ===")
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
