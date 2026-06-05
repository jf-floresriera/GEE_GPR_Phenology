# -*- coding: utf-8 -*-
"""
__init__.py — Punto de entrada del plugin GEEGPRPheno
Verifica e instala dependencias automáticamente antes de cargar el plugin.
"""


def classFactory(iface):
    # 1. Verificar e instalar dependencias antes de cargar nada
    from .installer import check_and_install, verify_structure
    deps_ok = check_and_install()

    if not deps_ok:
        # Si faltan dependencias y no se pudieron instalar, retornar plugin vacío
        class _EmptyPlugin:
            def __init__(self, iface): pass
            def initGui(self): pass
            def unload(self): pass
        return _EmptyPlugin(iface)

    # 2. Verificar estructura de archivos (en consola de QGIS)
    verify_structure()

    # 3. Cargar el plugin principal
    from .plugin import GEEGPRPhenoPlugin
    return GEEGPRPhenoPlugin(iface)
