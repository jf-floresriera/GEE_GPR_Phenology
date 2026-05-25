# -*- coding: utf-8 -*-
"""
installer.py — Auto-instalador multiplataforma para el plugin GEEGPRPheno
Compatible con: Windows (OSGeo4W), macOS (QGIS.app), Linux/Zorin/Ubuntu/Debian
"""
import sys
import subprocess
import importlib
import os

REQUIRED_PACKAGES = {
    "numpy":            "numpy>=1.21.0",
    "scipy":            "scipy>=1.7.0",
    "rasterio":         "rasterio>=1.3.0",
    "ee":               "earthengine-api>=0.1.370",   # ← NUEVA LÍNEA
}

def _detect_qgis_python():
    """
    Detecta el ejecutable Python correcto según el SO y la instalación de QGIS.
    Retorna (python_exe, pip_extra_args)
    """
    platform = sys.platform

    # ── Windows (OSGeo4W) ─────────────────────────────────────────────────────
    if platform == "win32":
        # QGIS en Windows usa su propio Python dentro de OSGeo4W
        # sys.executable ya apunta al Python de QGIS
        return sys.executable, []

    # ── macOS (QGIS.app) ─────────────────────────────────────────────────────
    if platform == "darwin":
        # QGIS en macOS usa Python dentro del bundle .app
        # Posibles ubicaciones del Python de QGIS en Mac
        mac_candidates = [
            "/Applications/QGIS.app/Contents/MacOS/bin/python3",
            "/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3",
            "/Applications/QGIS.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
        ]
        for candidate in mac_candidates:
            if os.path.exists(candidate):
                return candidate, []
        # Si no encontramos el bundle, usar sys.executable con --user
        return sys.executable, ["--user"]

    # ── Linux / Zorin OS / Ubuntu / Debian ───────────────────────────────────
    # Necesita --user y --break-system-packages en sistemas modernos (PEP 668)
    user_site = os.path.expanduser(
        f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    os.makedirs(user_site, exist_ok=True)
    return sys.executable, ["--user", "--break-system-packages", "--no-warn-script-location"]


def _add_user_site_to_path():
    """Agrega rutas de usuario a sys.path para que QGIS encuentre los paquetes."""
    import site

    paths_to_add = []

    # Linux/macOS: ~/.local/lib/pythonX.Y/site-packages
    user_site = os.path.expanduser(
        f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    paths_to_add.append(user_site)

    # site.getusersitepackages() — portable entre SO
    try:
        paths_to_add.append(site.getusersitepackages())
    except AttributeError:
        pass

    for p in paths_to_add:
        if p and p not in sys.path:
            sys.path.insert(0, p)


def check_and_install():
    """
    Verifica e instala dependencias faltantes.
    Funciona en Windows, macOS y Linux/Zorin sin configuración adicional.
    """
    _add_user_site_to_path()

    # Detectar qué falta
    missing = []
    for module_name, pip_spec in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append((module_name, pip_spec))

    if not missing:
        return True  # Todo OK

    # Detectar SO para mostrar instrucciones correctas en el mensaje
    platform = sys.platform
    if platform == "win32":
        os_name = "Windows"
        manual_cmd = (
            "1. Abre el OSGeo4W Shell (menú inicio → QGIS → OSGeo4W Shell)\n"
            "2. Ejecuta:\n"
            "   python -m pip install numpy scipy rasterio"
        )
    elif platform == "darwin":
        os_name = "macOS"
        manual_cmd = (
            "Abre Terminal y ejecuta:\n"
            "sudo /Applications/QGIS.app/Contents/MacOS/bin/pip3 install \\\n"
            "  numpy scipy rasterio"
        )
    else:
        os_name = "Linux/Zorin OS"
        manual_cmd = (
            "Abre Terminal y ejecuta:\n"
            "pip3 install --user --break-system-packages numpy scipy rasterio\n\n"
            "O con apt:\n"
            "sudo apt install python3-numpy python3-scipy\n"
            "pip3 install --user --break-system-packages rasterio"
        )

    # Diálogo de confirmación
    try:
        from qgis.PyQt.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle(f"GEEGPRPheno — Dependencias faltantes ({os_name})")
        msg.setText(
            f"Sistema detectado: {os_name}\n\n"
            "El plugin necesita instalar las siguientes librerías Python:\n\n"
            + "\n".join(f"  • {p}" for _, p in missing)
            + "\n\n¿Deseas instalarlas automáticamente ahora?\n"
            "(Requiere conexión a internet)"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        reply = msg.exec_()
        if reply != QMessageBox.Yes:
            QMessageBox.warning(
                None, "GEEGPRPheno — Instalación manual requerida",
                f"Instala las dependencias manualmente:\n\n{manual_cmd}"
            )
            return False
    except Exception:
        pass

    # Instalar
    python_exe, extra_args = _detect_qgis_python()
    failed = []

    for module_name, pkg_spec in missing:
        cmd = [python_exe, "-m", "pip", "install", pkg_spec, "--quiet"] + extra_args
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # Fallback: sin --user (para Windows/Mac donde no aplica)
            cmd_fallback = [python_exe, "-m", "pip", "install", pkg_spec, "--quiet"]
            result2 = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if result2.returncode != 0:
                failed.append((pkg_spec, result2.stderr.strip()))

    if failed:
        try:
            from qgis.PyQt.QtWidgets import QMessageBox
            errores = "\n\n".join(f"• {p}\n  {e[:200]}" for p, e in failed)
            QMessageBox.critical(
                None, "GEEGPRPheno — Error de instalación",
                f"No se pudieron instalar algunos paquetes:\n\n{errores}\n\n"
                f"──────────────────────────────────\n"
                f"Instalación manual ({os_name}):\n\n{manual_cmd}"
            )
        except Exception:
            pass
        return False

    # Recargar paths y pedir reinicio
    _add_user_site_to_path()

    try:
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.information(
            None, "GEEGPRPheno — Instalación completada",
            "✅ Dependencias instaladas correctamente.\n\n"
            "⚠️ Por favor, reinicia QGIS para activar los cambios."
        )
    except Exception:
        pass
    return False  # Forzar reinicio


def verify_structure():
    """Imprime en la consola de QGIS el estado completo del plugin."""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "__init__.py", "plugin.py", "processing_provider.py",
        "s2boa_models.py", "algo_spectral_prediction.py",
        "algo_gapfilling.py", "algo_lsp.py", "phenology_functions.py",
        "metadata.txt", "requirements.txt", "installer.py",
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
    for mod, spec in REQUIRED_PACKAGES.items():
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "?")
            print(f"  ✓  {mod} v{ver}")
        except ImportError:
            print(f"  ✗  {mod}  ← NO instalado")
            all_ok = False

    print("=" * 55 + "\n")
    return all_ok
