# -*- coding: utf-8 -*-
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QMessageBox,
    QScrollArea, QFrame, QInputDialog, QLineEdit, QSizePolicy
)
from qgis.PyQt.QtGui import QIcon, QFont, QDesktopServices
from qgis.PyQt.QtCore import Qt, QUrl, QPoint, QSize
import os

from .processing_provider import GEEGPRPhenoProvider


class GEEPanelDialog(QDialog):
    """Ventana flotante independiente del plugin — usa decoraciones del SO."""

    def __init__(self, parent, iface):
        super().__init__(
            parent,
            Qt.Window |
            Qt.WindowTitleHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.iface = iface
        self.setWindowTitle("GEE GPR Phenology")
        self.setMinimumSize(420, 540)
        self.resize(460, 680)

        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._check_gee_status(silent=True)

    def closeEvent(self, event):
        """Ocultar en lugar de destruir, para poder reabrirlo."""
        event.ignore()
        self.hide()

    # =========================================================================
    # CONSTRUCCION DE LA UI
    # =========================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header verde ──────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: qlineargradient("
            "x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #01696f, stop:1 #0c4e54); border: none; }"
        )
        header.setFixedHeight(60)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 10, 16, 10)
        h_lay.setSpacing(8)

        title = QLabel("GEE GPR Phenology")
        tf = QFont()
        tf.setPointSize(12)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: white; background: transparent;")

        subtitle = QLabel("Sentinel-2  ·  GPR  ·  Fenologia")
        subtitle.setStyleSheet(
            "color: rgba(255,255,255,0.75); background: transparent; font-size: 10px;"
        )

        txt_box = QVBoxLayout()
        txt_box.setSpacing(1)
        txt_box.addWidget(title)
        txt_box.addWidget(subtitle)
        h_lay.addLayout(txt_box)
        h_lay.addStretch()

        self.gee_btn = QPushButton("GEE")
        self.gee_btn.setFixedSize(58, 28)
        self.gee_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.15); color: white; "
            "border: 1px solid rgba(255,255,255,0.45); border-radius: 5px; "
            "font-size: 10px; font-weight: bold; }"
            "QPushButton:hover { background: rgba(255,255,255,0.30); }"
        )
        self.gee_btn.setToolTip("Estado GEE - clic para autenticar")
        self.gee_btn.clicked.connect(self._authenticate_gee)
        h_lay.addWidget(self.gee_btn)

        root.addWidget(header)

        # ── Tabs ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #f7f6f2; }
            QTabBar::tab {
                background: #e6e4df; color: #28251d;
                padding: 7px 9px; font-size: 10px;
                border: none; border-bottom: 2px solid transparent;
                min-width: 64px;
            }
            QTabBar::tab:selected {
                background: #f7f6f2; color: #01696f;
                border-bottom: 2px solid #01696f; font-weight: bold;
            }
            QTabBar::tab:hover:!selected { background: #dcd9d5; }
        """)

        self.tabs.addTab(self._make_algo_tab(
            '1. Prediccion Espectral GPR',
            'gpr_spectral_prediction', '🌿',
            'Aplica modelo GPR pre-entrenado sobre las\n'
            '10 bandas Sentinel-2 BOA para estimar\n'
            'pixel a pixel variables biofisicas:\n'
            'LAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw',
            '#437a22'
        ), '🌿 Espectral')

        self.tabs.addTab(self._make_algo_tab(
            '2. Relleno Temporal GPR (Gapfilling)',
            'gpr_gapfilling', '🔁',
            'Usa GPR con kernel RBF temporal para\n'
            'rellenar lagunas en la serie temporal\n'
            'causadas por cobertura nubosa.\n'
            'Hiperparametros calibrados por cultivo.',
            '#006494'
        ), '🔁 Gapfilling')

        self.tabs.addTab(self._make_algo_tab(
            '3. Metricas LSP (Fenologia)',
            'lsp_generation', '📈',
            'Ajusta doble logistica por pixel sobre\n'
            'la serie temporal gapfilled y extrae:\n'
            'SOS, EOS, POS, LOS, vmin, vmax\n'
            'y parametros n1, m1, n2, m2.',
            '#7a39bb'
        ), '📈 LSP')

        self.tabs.addTab(self._make_algo_tab(
            '4. Pipeline GEE Automatico',
            'gee_auto_pipeline', '🛰',
            'Pipeline completo automatico:\n'
            '1  Descarga S2 L2A desde Google Earth Engine\n'
            '2  Filtra por area, fechas y nubosidad\n'
            '3  Prediccion espectral GPR\n'
            '4  Gapfilling temporal GPR\n'
            '5  Metricas LSP fenologicas (opcional)',
            '#01696f'
        ), '🛰 GEE Auto')

        self.tabs.addTab(self._make_info_tab(), 'ℹ Info')

        root.addWidget(self.tabs, 1)

        # ── Footer ────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(38)
        footer.setStyleSheet(
            "QFrame { background: #f3f0ec; border-top: 1px solid #dcd9d5; }"
        )
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(12, 0, 12, 0)
        f_lay.setSpacing(8)

        ver = QLabel("GEEGPRPheno v1.2.1  —  UNAL Laboratorio 227")
        ver.setStyleSheet("color: #7a7974; font-size: 9px; background: transparent;")
        f_lay.addWidget(ver)
        f_lay.addStretch()

        ck = QPushButton("Verificar GEE")
        ck.setFixedHeight(26)
        ck.setStyleSheet(
            "QPushButton { background: #01696f; color: white; border: none; "
            "border-radius: 4px; font-size: 10px; padding: 0 12px; }"
            "QPushButton:hover { background: #0c4e54; }"
        )
        ck.clicked.connect(lambda: self._check_gee_status(silent=False))
        f_lay.addWidget(ck)

        root.addWidget(footer)

    # =========================================================================
    # PESTANA ALGORITMO
    # =========================================================================

    def _make_algo_tab(self, name, algo_id, icon_char, description, color):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f7f6f2; }")

        ctn = QWidget()
        ctn.setStyleSheet("background: #f7f6f2;")
        lay = QVBoxLayout(ctn)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        ico = QLabel(icon_char)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"font-size: 40px; background: transparent;")
        lay.addWidget(ico)

        nm = QLabel(name)
        nf = QFont()
        nf.setPointSize(11)
        nf.setBold(True)
        nm.setFont(nf)
        nm.setAlignment(Qt.AlignCenter)
        nm.setWordWrap(True)
        nm.setStyleSheet(f"color: {color}; background: transparent;")
        lay.addWidget(nm)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(2)
        sep.setStyleSheet(f"background: {color}; border: none;")
        lay.addWidget(sep)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        desc.setStyleSheet(
            "color: #28251d; background: #f9f8f5; padding: 12px; "
            "border-radius: 6px; font-size: 11px; line-height: 1.5;"
        )
        lay.addWidget(desc)

        lay.addStretch()

        run_btn = QPushButton("  Abrir y ejecutar")
        run_btn.setMinimumHeight(44)
        dark = self._darken(color)
        run_btn.setStyleSheet(
            f"QPushButton {{ background: {color}; color: white; border: none; "
            f"border-radius: 7px; font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {dark}; }}"
            f"QPushButton:pressed {{ background: {self._darken(color, 25)}; }}"
        )
        run_btn.clicked.connect(lambda checked, aid=algo_id: self._run_algorithm(aid))
        lay.addWidget(run_btn)

        scroll.setWidget(ctn)
        return scroll

    # =========================================================================
    # PESTANA INFO
    # =========================================================================

    def _make_info_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f7f6f2; }")

        ctn = QWidget()
        ctn.setStyleSheet("background: #f7f6f2;")
        lay = QVBoxLayout(ctn)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        tit = QLabel("GEE GPR Phenology Plugin")
        tf = QFont()
        tf.setPointSize(13)
        tf.setBold(True)
        tit.setFont(tf)
        tit.setAlignment(Qt.AlignCenter)
        tit.setStyleSheet("color: #01696f; background: transparent;")
        lay.addWidget(tit)

        ver = QLabel("Version 1.2.1  |  QGIS 3.x  |  Python 3.x")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #7a7974; font-size: 10px; background: transparent;")
        lay.addWidget(ver)

        lay.addWidget(self._sep())

        lay.addWidget(self._section_title("Descripcion"))
        desc = QLabel(
            "Plugin de QGIS para la estimacion de variables biofisicas y "
            "fenologia de cultivos a partir de imagenes Sentinel-2 BOA, usando "
            "modelos de Regresion por Procesos Gaussianos (GPR) pre-entrenados. "
            "Incluye pipeline automatico con descarga directa desde Google Earth "
            "Engine (GEE).\n\n"
            "Basado en la metodologia de:\n"
            "M. Salinero-Delgado et al. — GEEGPRPhenoDemos"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "color: #28251d; background: #f9f8f5; padding: 12px; "
            "border-radius: 6px; font-size: 11px;"
        )
        lay.addWidget(desc)

        lay.addWidget(self._sep())

        lay.addWidget(self._section_title("Desarrollador"))

        dev_frame = QFrame()
        dev_frame.setStyleSheet(
            "QFrame { background: #f9f8f5; border: 1px solid #dcd9d5; "
            "border-radius: 8px; }"
        )
        dv = QVBoxLayout(dev_frame)
        dv.setContentsMargins(14, 14, 14, 14)
        dv.setSpacing(10)

        def row(ico_char, text, link_url=''):
            r = QHBoxLayout()
            r.setSpacing(10)
            i = QLabel(ico_char)
            i.setFixedWidth(22)
            i.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            i.setStyleSheet("background: transparent; font-size: 16px;")
            r.addWidget(i)
            if link_url:
                lbl = QLabel(f'<a href="{link_url}" style="color:#01696f;">{text}</a>')
                lbl.setOpenExternalLinks(True)
            else:
                lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("background: transparent; font-size: 11px; color: #28251d;")
            r.addWidget(lbl, 1)
            return r

        dv.addLayout(row('👤', '<b>Jesus Enrique Flores Riera</b>'))
        dv.addLayout(row('🏛', 'Laboratorio 227 — Universidad Nacional de Colombia'))
        dv.addLayout(row('✉', 'jfloresr@unal.edu.co', 'mailto:jfloresr@unal.edu.co'))
        dv.addLayout(row('🔗', 'linkedin.com/in/flores-riera',
                         'https://www.linkedin.com/in/flores-riera/'))
        lay.addWidget(dev_frame)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_li = QPushButton("  Abrir LinkedIn")
        btn_li.setMinimumHeight(36)
        btn_li.setStyleSheet(
            "QPushButton { background: #0077b5; color: white; border: none; "
            "border-radius: 6px; font-size: 11px; font-weight: bold; }"
            "QPushButton:hover { background: #005f8e; }"
        )
        btn_li.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://www.linkedin.com/in/flores-riera/'))
        )
        btn_row.addWidget(btn_li)

        btn_em = QPushButton("  Enviar correo")
        btn_em.setMinimumHeight(36)
        btn_em.setStyleSheet(
            "QPushButton { background: #437a22; color: white; border: none; "
            "border-radius: 6px; font-size: 11px; font-weight: bold; }"
            "QPushButton:hover { background: #2e5c10; }"
        )
        btn_em.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('mailto:jfloresr@unal.edu.co'))
        )
        btn_row.addWidget(btn_em)
        lay.addLayout(btn_row)

        lay.addWidget(self._sep())

        lay.addWidget(self._section_title("Algoritmos incluidos"))

        for ico_char, name, desc_txt, color in [
            ('🌿', '1. Prediccion Espectral GPR',
             'Estima LAI, Cab, Cw, Cm, FVC pixel a pixel', '#437a22'),
            ('🔁', '2. Relleno Temporal GPR',
             'Rellena series temporales con cobertura nubosa', '#006494'),
            ('📈', '3. Metricas LSP (Fenologia)',
             'SOS, EOS, POS, LOS via doble logistica', '#7a39bb'),
            ('🛰', '4. Pipeline GEE Automatico',
             'Descarga S2 + GPR + LSP en un solo paso', '#01696f'),
        ]:
            af = QFrame()
            af.setStyleSheet(
                f"QFrame {{ background: #f9f8f5; border-left: 3px solid {color}; "
                f"border-top: none; border-right: none; border-bottom: none; "
                f"border-radius: 0px; }}"
            )
            al = QHBoxLayout(af)
            al.setContentsMargins(10, 8, 10, 8)
            al.setSpacing(10)

            ai = QLabel(ico_char)
            ai.setFixedWidth(24)
            ai.setStyleSheet("background: transparent; font-size: 18px;")
            al.addWidget(ai)

            at = QVBoxLayout()
            at.setSpacing(2)
            an = QLabel(name)
            anf = QFont()
            anf.setBold(True)
            anf.setPointSize(9)
            an.setFont(anf)
            an.setStyleSheet(f"background: transparent; color: {color};")
            ad = QLabel(desc_txt)
            ad.setStyleSheet("background: transparent; color: #7a7974; font-size: 10px;")
            at.addWidget(an)
            at.addWidget(ad)
            al.addLayout(at, 1)
            lay.addWidget(af)

        lay.addWidget(self._sep())

        lay.addWidget(self._section_title("Dependencias"))
        deps = QLabel(
            "numpy >= 1.21    scipy >= 1.7    rasterio >= 1.3\n"
            "earthengine-api >= 0.1.370  (solo Algoritmo 4)"
        )
        deps.setStyleSheet(
            "color: #28251d; background: #f9f8f5; padding: 10px; "
            "border-radius: 6px; font-size: 10px; font-family: monospace;"
        )
        lay.addWidget(deps)
        lay.addStretch()

        scroll.setWidget(ctn)
        return scroll

    # =========================================================================
    # HELPERS UI
    # =========================================================================

    def _sep(self):
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setFixedHeight(1)
        s.setStyleSheet("background: #dcd9d5; border: none;")
        return s

    def _section_title(self, text):
        lbl = QLabel(text)
        f = QFont()
        f.setBold(True)
        f.setPointSize(10)
        lbl.setFont(f)
        lbl.setStyleSheet("color: #28251d; background: transparent;")
        return lbl

    def _darken(self, hex_color, amount=18):
        h = hex_color.lstrip('#')
        r = max(0, int(h[0:2], 16) - amount)
        g = max(0, int(h[2:4], 16) - amount)
        b = max(0, int(h[4:6], 16) - amount)
        return f'#{r:02x}{g:02x}{b:02x}'

    # =========================================================================
    # EJECUCION DE ALGORITMOS
    # =========================================================================

    def _run_algorithm(self, algo_id):
        try:
            from processing.gui.AlgorithmDialog import AlgorithmDialog
            alg = QgsApplication.processingRegistry().algorithmById(
                f'geegprpheno:{algo_id}'
            )
            if alg is None:
                QMessageBox.warning(
                    self, "GEEGPRPheno",
                    f"Algoritmo '{algo_id}' no encontrado.\n"
                    "Recarga el plugin desde Complementos > Administrar complementos."
                )
                return

            # Mantener vivo el panel: en algunos entornos el dialogo modal de
            # Processing puede dejar oculto o sin foco el panel del plugin.
            was_visible = self.isVisible()
            dlg = AlgorithmDialog(alg, False, self)
            dlg.show()
            dlg.exec_()
            if was_visible:
                self.show()
                self.raise_()
                self.activateWindow()
        except Exception as ex:
            QMessageBox.critical(self, "GEEGPRPheno", f"Error al abrir algoritmo:\n{ex}")

    # =========================================================================
    # GEE — VERIFICACION
    # =========================================================================

    def _check_gee_status(self, silent=False):
        try:
            import ee
            project = self._load_gee_project()
            if project:
                ee.Initialize(project=project)
            else:
                ee.Initialize()
            self.gee_btn.setText("GEE OK")
            self.gee_btn.setToolTip("GEE conectado correctamente")
            self.gee_btn.setStyleSheet(
                "QPushButton { background: rgba(67,122,34,0.75); color: white; "
                "border: 1px solid rgba(255,255,255,0.4); border-radius: 5px; "
                "font-size: 9px; font-weight: bold; }"
                "QPushButton:hover { background: rgba(67,122,34,0.95); }"
            )
            if not silent:
                QMessageBox.information(
                    self, "GEE activo",
                    "Google Earth Engine conectado correctamente.\n"
                    "El Pipeline Automatico esta listo."
                )
        except Exception as ex:
            self.gee_btn.setText("Sin GEE")
            self.gee_btn.setToolTip("Sin conexion GEE - clic para autenticar")
            self.gee_btn.setStyleSheet(
                "QPushButton { background: rgba(192,57,43,0.75); color: white; "
                "border: 1px solid rgba(255,255,255,0.4); border-radius: 5px; "
                "font-size: 9px; font-weight: bold; }"
                "QPushButton:hover { background: rgba(192,57,43,0.95); }"
            )
            if not silent:
                reply = QMessageBox.question(
                    self, "Sin conexion GEE",
                    "No hay conexion activa con Google Earth Engine.\n\n"
                    "Deseas autenticarte ahora?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self._authenticate_gee()

    # =========================================================================
    # GEE — GUARDAR / CARGAR PROJECT ID
    # =========================================================================

    def _gee_config_path(self):
        config_dir = os.path.expanduser('~/.config/earthengine')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'qgis_plugin_config.json')

    def _save_gee_project(self, project_id):
        import json
        with open(self._gee_config_path(), 'w') as f:
            json.dump({'project': project_id}, f)

    def _load_gee_project(self):
        import json
        path = self._gee_config_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f).get('project', '')
            except Exception:
                pass
        return ''

    # =========================================================================
    # GEE — AUTENTICACION (flujo moderno ee.Authenticate)
    # =========================================================================

    def _prompt_gee_project(self, current_project=''):
        project, ok = QInputDialog.getText(
            self,
            "ID de proyecto Google Cloud / GEE",
            "Ingresa o cambia el Project ID de Google Cloud / Earth Engine:\n\n"
            "Ejemplo: ee-miusuario o my-gee-project-123\n\n"
            "Este valor se usara en ee.Initialize(project=...).",
            QLineEdit.Normal,
            current_project or ""
        )
        if not ok or not project.strip():
            return ''
        return project.strip()

    def _reset_ee_session(self, ee):
        """Reinicia la sesion local de ee si la version de la API lo permite."""
        try:
            ee.Reset()
        except Exception:
            pass

    def _authenticate_gee(self, force=False, change_project=False):
        try:
            import ee
        except ImportError:
            QMessageBox.critical(
                self, "GEEGPRPheno",
                "earthengine-api no instalado.\n\n"
                "Para evitar bucles de reinicio, instala esta dependencia fuera del arranque de QGIS.\n\n"
                "En Windows:\n"
                "1) Cierra QGIS.\n"
                "2) Abre OSGeo4W Shell.\n"
                "3) Ejecuta:\n\n"
                "   python -m pip install earthengine-api\n\n"
                "Luego abre QGIS y vuelve a autenticar."
            )
            return

        project = self._load_gee_project()

        if project and not change_project:
            reply = QMessageBox.question(
                self,
                "Proyecto GEE guardado",
                f"Proyecto actual guardado:\n\n  {project}\n\n"
                "¿Deseas usar este proyecto?\n\n"
                "Selecciona No para cambiar de proyecto antes de autenticar.",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.No:
                change_project = True

        if change_project or not project:
            new_project = self._prompt_gee_project(project)
            if not new_project:
                QMessageBox.warning(
                    self, "GEEGPRPheno",
                    "Se necesita un Project ID para inicializar Earth Engine."
                )
                return
            project = new_project
            self._save_gee_project(project)
            self._reset_ee_session(ee)

        # Primero intentar inicializar. Si force=True se fuerza reautenticacion.
        if not force:
            try:
                self._reset_ee_session(ee)
                ee.Initialize(project=project)
                self._check_gee_status(silent=True)
                QMessageBox.information(
                    self, "GEE activo",
                    f"Google Earth Engine esta conectado.\n\nProyecto: {project}\n\n"
                    "Para cambiar de cuenta o renovar credenciales usa:\n"
                    "Plugins > GEE GPR Phenology > Cambiar proyecto / reautenticar."
                )
                return
            except Exception:
                pass

        reply = QMessageBox.question(
            self, "Autenticacion Google Earth Engine",
            "Se abrira el navegador para autenticar Google Earth Engine.\n\n"
            f"Proyecto GEE: {project}\n\n"
            + ("Se forzara la renovacion de credenciales.\n\n" if force else "") +
            "Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Earth Engine reutiliza credenciales por defecto; force=True permite renovar credenciales.
        auth_errors = []
        for mode in ('localhost', 'notebook', None):
            try:
                kwargs = {'quiet': False}
                if mode:
                    kwargs['auth_mode'] = mode
                if force:
                    kwargs['force'] = True
                ee.Authenticate(**kwargs)
                self._reset_ee_session(ee)
                ee.Initialize(project=project)
                self._check_gee_status(silent=True)
                QMessageBox.information(
                    self, "Autenticacion exitosa",
                    f"Google Earth Engine autenticado correctamente.\n\nProyecto: {project}"
                )
                return
            except TypeError:
                # Compatibilidad con versiones antiguas de earthengine-api sin force=...
                try:
                    kwargs = {'quiet': False}
                    if mode:
                        kwargs['auth_mode'] = mode
                    ee.Authenticate(**kwargs)
                    self._reset_ee_session(ee)
                    ee.Initialize(project=project)
                    self._check_gee_status(silent=True)
                    QMessageBox.information(
                        self, "Autenticacion exitosa",
                        f"Google Earth Engine autenticado correctamente.\n\nProyecto: {project}"
                    )
                    return
                except Exception as ex:
                    auth_errors.append(str(ex))
            except Exception as ex:
                auth_errors.append(str(ex))

        last_error = auth_errors[-1] if auth_errors else 'Error no especificado'
        QMessageBox.critical(
            self, "Error de autenticacion",
            f"No se pudo autenticar.\n\nError: {last_error}\n\n"
            "Solucion manual sugerida en la Consola Python de QGIS:\n\n"
            "  import ee\n"
            "  ee.Authenticate(force=True)\n"
            f"  ee.Initialize(project='{project}')\n\n"
            "O en terminal:\n\n"
            "  earthengine authenticate --force\n"
            f"  earthengine set_project {project}"
        )

# =============================================================================
# CLASE PRINCIPAL DEL PLUGIN
# =============================================================================

class GEEGPRPhenoPlugin:

    def __init__(self, iface):
        self.iface    = iface
        self.provider = None
        self.actions  = []
        self.menu_name = "GEE GPR Phenology"
        self.toolbar   = None
        self.panel     = None

    def initProcessing(self):
        self.provider = GEEGPRPhenoProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.toolbar = self.iface.addToolBar("GEE GPR Phenology")
        self.toolbar.setObjectName("GEEGPRPhenoToolbar")

        act_open = QAction(icon, "Abrir GEE GPR Phenology Tools",
                           self.iface.mainWindow())
        act_open.setToolTip("Abrir panel GEE GPR Phenology")
        act_open.triggered.connect(self._toggle_panel)
        self.toolbar.addAction(act_open)
        self.actions.append(act_open)
        self.iface.addPluginToMenu(self.menu_name, act_open)

        act_auth = QAction("Autenticar Google Earth Engine",
                           self.iface.mainWindow())
        act_auth.triggered.connect(self._auth_from_menu)
        self.iface.addPluginToMenu(self.menu_name, act_auth)
        self.actions.append(act_auth)

        act_change = QAction("Cambiar proyecto GEE / reautenticar",
                             self.iface.mainWindow())
        act_change.triggered.connect(self._change_project_from_menu)
        self.iface.addPluginToMenu(self.menu_name, act_change)
        self.actions.append(act_change)

        act_check = QAction("Verificar conexion GEE", self.iface.mainWindow())
        act_check.triggered.connect(self._check_from_menu)
        self.iface.addPluginToMenu(self.menu_name, act_check)
        self.actions.append(act_check)

        act_deps = QAction("Diagnosticar dependencias Python", self.iface.mainWindow())
        act_deps.triggered.connect(self._dependency_help)
        self.iface.addPluginToMenu(self.menu_name, act_deps)
        self.actions.append(act_deps)

        act_help = QAction("Ayuda y documentacion", self.iface.mainWindow())
        act_help.triggered.connect(self._open_help)
        self.iface.addPluginToMenu(self.menu_name, act_help)
        self.actions.append(act_help)

        # Abrir panel al arrancar
        self._toggle_panel()

    def _get_panel(self):
        if self.panel is None:
            self.panel = GEEPanelDialog(self.iface.mainWindow(), self.iface)
        return self.panel

    def _toggle_panel(self):
        p = self._get_panel()
        if p.isVisible():
            p.hide()
        else:
            p.show()
            p.raise_()
            p.activateWindow()

    def _auth_from_menu(self):
        self._get_panel()._authenticate_gee()

    def _change_project_from_menu(self):
        self._get_panel()._authenticate_gee(force=True, change_project=True)

    def _check_from_menu(self):
        self._get_panel()._check_gee_status(silent=False)

    def _dependency_help(self):
        try:
            from .installer import dependency_report, manual_install_instructions
            rows = dependency_report()
            lines = []
            for kind, module_name, pip_spec, ok, ver in rows:
                status = "OK" if ok else "FALTA"
                lines.append(f"{status:5s}  {module_name:10s}  {ver}  [{kind}] {pip_spec}")
            QMessageBox.information(
                self.iface.mainWindow(),
                "GEEGPRPheno — dependencias Python",
                "Estado de dependencias:\n\n"
                + "\n".join(lines)
                + "\n\nInstalacion manual recomendada:\n\n"
                + manual_install_instructions()
            )
        except Exception as ex:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "GEEGPRPheno — dependencias Python",
                f"No se pudo generar el diagnostico:\n{ex}"
            )

    def _open_help(self):
        QDesktopServices.openUrl(
            QUrl('https://github.com/jf-floresriera/GEE_GPR_Phenology')
        )

    def unload(self):
        if self.panel:
            self.panel.close()
            self.panel.deleteLater()
            self.panel = None
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
        for action in self.actions:
            self.iface.removePluginMenu(self.menu_name, action)
            self.iface.removeToolBarIcon(action)
        if self.toolbar:
            del self.toolbar
            self.toolbar = None
            