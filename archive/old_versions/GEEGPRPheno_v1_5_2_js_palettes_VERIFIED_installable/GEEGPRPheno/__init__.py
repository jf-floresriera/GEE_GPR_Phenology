# -*- coding: utf-8 -*-
"""
__init__.py — Punto de entrada del plugin GEEGPRPheno.

Desde v1.5.0 el plugin NO intenta instalar paquetes automaticamente al
arrancar QGIS. Esto evita bucles de reinicio/carga cuando falta earthengine-api.
"""


def classFactory(iface):
    from .installer import check_and_install, verify_structure
    deps_ok = check_and_install()

    if not deps_ok:
        class _EmptyPlugin:
            def __init__(self, iface): pass
            def initGui(self): pass
            def unload(self): pass
        return _EmptyPlugin(iface)

    verify_structure()
    from .plugin import GEEGPRPhenoPlugin
    return GEEGPRPhenoPlugin(iface)
