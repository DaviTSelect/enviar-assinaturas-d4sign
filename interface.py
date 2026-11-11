"""Interface gráfica PySide6 para envio de documentos para assinatura via D4Sign."""
from __future__ import annotations

import logging
import re
import sys
import threading
import unicodedata
from pathlib import Path

from openpyxl import load_workbook
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGraphicsDropShadowEffect, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from navegador import Navegador
from version import VERSION

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
ERROR_LOG = LOG_DIR / "automation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(threadName)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(ERROR_LOG, encoding="utf-8")],
)
logger = logging.getLogger(__name__)

# ── Paleta ────────────────────────────────────────────────────────────────────
BG     = '#203447'
TEXT   = '#efede5'
ACTION = '#e94c1f'
COR_DIVISOR_ESCURO = '#415364'
COR_ICONE          = '#7a8791'
COR_SELECIONADO    = '#317458'

ESTILO_FUNDO_ICONE    = 'background:#e9eef0; border-radius:12px;'
ESTILO_FUNDO_ICONE_OK = 'background:#e5f4ed; border-radius:12px;'
ESTILO_BOTAO_LINHA = '''
    QPushButton {background:#ffffff; border:1px solid #d9dddc; border-radius:9px;
        color:#344a5b; font-family:"Segoe UI"; font-size:11px; font-weight:600; padding:0 12px;}
    QPushButton:hover {background:#f1f3f1; border-color:#b5bec3;}'''
ESTILO_INICIAR_ATIVO = f'''
    QPushButton {{background:{ACTION}; color:white; border:none; border-radius:9px;
        font:600 11px "Segoe UI"; padding:0 19px;}}
    QPushButton:hover {{background:#d74118;}}'''
ESTILO_INICIAR_INATIVO = '''
    QPushButton {background:#d8dad9; color:#92999b; border:none; border-radius:9px;
        font:600 11px "Segoe UI"; padding:0 19px;}
    QPushButton:disabled {background:#d8dad9; color:#92999b;}'''
ESTILO_INICIAR_RODANDO = '''
    QPushButton {background:#2a4255; color:#a5b4c0; border:none; border-radius:9px;
        font:600 11px "Segoe UI"; padding:0 19px;}
    QPushButton:disabled {background:#2a4255; color:#a5b4c0;}'''

_ESTILO_DIALOGO = """
    QMessageBox { background-color: #203447; }
    QLabel { color: #efede5; font-family: "Segoe UI"; font-size: 13px; }
    QPushButton { background: #e94c1f; color: white; border: none; border-radius: 6px;
                  font: 600 11px "Segoe UI"; padding: 6px 20px; min-width: 70px; }
    QPushButton:hover { background: #d74118; }
"""

ST_CONFIRMADO = 'Confirmado'
ST_ENVIANDO   = 'Enviando...'
ST_ENVIADO    = 'Enviado'
ST_ERRO       = 'Erro'

_COR_ST = {
    ST_CONFIRMADO: ('#d6f0e3', '#2a6648'),
    ST_ENVIANDO:   ('#e8f0fb', '#2563a8'),
    ST_ENVIADO:    ('#bde8d0', '#1d5e3a'),
    ST_ERRO:       ('#fde8e4', '#c0351a'),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dialogo(parent, titulo: str, msg: str, icone=QMessageBox.Information,
             botoes=QMessageBox.Ok) -> int:
    dlg = QMessageBox(parent)
    dlg.setWindowTitle(titulo)
    dlg.setText(msg)
    dlg.setIcon(icone)
    dlg.setStandardButtons(botoes)
    dlg.setStyleSheet(_ESTILO_DIALOGO)
    return dlg.exec()


def _rotulo(text, size, color, weight=QFont.Normal, wrap=False):
    w = QLabel(text)
    f = QFont('Segoe UI', size)
    f.setWeight(weight)
    w.setFont(f)
    w.setStyleSheet(f'color:{color}; background:transparent;')
    w.setWordWrap(wrap)
    return w


def _divisor(color):
    d = QFrame()
    d.setFixedHeight(1)
    d.setStyleSheet(f'background:{color}; border:none;')
    return d


# ── Ícone desenhado ───────────────────────────────────────────────────────────

class Icon(QWidget):
    def __init__(self, kind, color=COR_ICONE, size=24, parent=None):
        super().__init__(parent)
        self.kind, self.color = kind, color
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(self.width() / 24, self.height() / 24)
        pen = QPen(QColor(self.color), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if self.kind in ('folder', 'save'):
            self._pasta(p, seta=self.kind == 'save')
        elif self.kind == 'file':
            self._arquivo(p)
        elif self.kind == 'check':
            pen.setWidthF(2)
            p.setPen(pen)
            self._check(p)
        p.end()

    @staticmethod
    def _ln(p, x1, y1, x2, y2):
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _pasta(self, p, seta):
        path = QPainterPath()
        path.moveTo(3.75, 16.25); path.lineTo(3.75, 6.75)
        path.cubicTo(3.75, 5.65, 4.65, 4.75, 5.75, 4.75)
        path.lineTo(9.11, 4.75); path.lineTo(11.91, 7.75); path.lineTo(18.25, 7.75)
        path.cubicTo(19.35, 7.75, 20.25, 8.65, 20.25, 9.75); path.lineTo(20.25, 16.25)
        path.cubicTo(20.25, 18, 19, 19.25, 17.25, 19.25); path.lineTo(6.75, 19.25)
        path.cubicTo(5, 19.25, 3.75, 18, 3.75, 16.25)
        p.drawPath(path)
        if seta:
            self._ln(p, 12, 10.5, 12, 15.5)
            self._ln(p, 10, 13.5, 12, 15.5)
            self._ln(p, 14, 13.5, 12, 15.5)

    def _arquivo(self, p):
        path = QPainterPath()
        path.moveTo(7, 3.75); path.lineTo(13.17, 3.75); path.lineTo(18, 8.58)
        path.lineTo(18, 20.25); path.lineTo(7, 20.25)
        path.cubicTo(5.7, 20.25, 5, 19.4, 5, 18.25)
        path.lineTo(5, 5.75); path.cubicTo(5, 4.6, 5.8, 3.75, 7, 3.75)
        p.drawPath(path)
        self._ln(p, 13.5, 4, 13.5, 8.5); self._ln(p, 13.5, 8.5, 18, 8.5)
        self._ln(p, 8.5, 13, 15.25, 13); self._ln(p, 8.5, 16.5, 13.25, 16.5)

    @staticmethod
    def _check(p):
        path = QPainterPath()
        path.moveTo(6.75, 12.25); path.lineTo(10, 15.5); path.lineTo(17.25, 8.25)
        p.drawPath(path)


# ── SelectionRow ──────────────────────────────────────────────────────────────

class SelectionRow(QFrame):
    def __init__(self, number, title, desc, btn_text, icon_kind, callback):
        super().__init__()
        self.btn_text = btn_text
        self.icon_kind = icon_kind
        self.setObjectName('selRow')
        self.setStyleSheet('#selRow {background:transparent; border:none;}')
        self.setMinimumHeight(110)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 18, 16, 18)
        outer.setSpacing(12)

        self.icon_box = QFrame()
        self.icon_box.setFixedSize(43, 43)
        self.icon_box.setStyleSheet(ESTILO_FUNDO_ICONE)
        self.icon_lay = QHBoxLayout(self.icon_box)
        self.icon_lay.setContentsMargins(0, 0, 0, 0)
        self.icon_lay.addWidget(Icon(icon_kind))
        outer.addWidget(self.icon_box, 0, Qt.AlignTop)
        outer.addLayout(self._textos(number, title, desc), 1)

        self.btn = QPushButton(btn_text)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setMinimumWidth(126)
        self.btn.setFixedHeight(39)
        self.btn.setStyleSheet(ESTILO_BOTAO_LINHA)
        self.btn.clicked.connect(callback)
        outer.addWidget(self.btn, 0, Qt.AlignVCenter)

    def _textos(self, number, title, desc):
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setContentsMargins(0, 1, 0, 0)

        head = QHBoxLayout()
        head.setSpacing(9)
        head.setContentsMargins(0, 0, 0, 0)
        head.addWidget(_rotulo('ETAPA ' + number, 9, '#7b8791', QFont.Bold))
        self.badge = _rotulo('SELECIONADO', 8, COR_SELECIONADO, QFont.Bold)
        self.badge.setStyleSheet(
            f'color:{COR_SELECIONADO}; background:#e5f4ed; border-radius:9px; padding:3px 8px;'
        )
        self.badge.hide()
        head.addWidget(self.badge)
        head.addStretch()
        col.addLayout(head)
        col.addSpacing(6)
        col.addWidget(_rotulo(title, 12, BG, QFont.DemiBold))
        col.addSpacing(5)
        col.addWidget(_rotulo(desc, 10, '#6d7780', wrap=True))
        self.valor = _rotulo('', 10, '#344b5e', QFont.Medium)
        self.valor.hide()
        col.addSpacing(4)
        col.addWidget(self.valor)
        col.addStretch()
        return col

    def definir_valor(self, value):
        ok = bool(value)
        self.badge.setVisible(ok)
        self.valor.setText(value)
        self.valor.setToolTip(value)
        self.valor.setVisible(ok)
        self.btn.setText('Alterar' if ok else self.btn_text)
        old = self.icon_lay.takeAt(0)
        if old and old.widget():
            old.widget().deleteLater()
        self.icon_lay.addWidget(
            Icon('check' if ok else self.icon_kind, COR_SELECIONADO if ok else COR_ICONE)
        )
        self.icon_box.setStyleSheet(ESTILO_FUNDO_ICONE_OK if ok else ESTILO_FUNDO_ICONE)


# ── Tabela de documentos ──────────────────────────────────────────────────────

class TabelaDocumentos(QFrame):
    COLS = ['Documento', 'Arquivo', 'Signatários', 'Status']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background:transparent; border:none;')
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 4, 16, 8)
        lay.setSpacing(6)
        lay.addWidget(_rotulo('Documentos confirmados', 10, BG, QFont.DemiBold))

        self.tbl = QTableWidget(0, len(self.COLS))
        self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setHighlightSections(False)
        self.tbl.setShowGrid(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setMinimumHeight(140)
        self.tbl.setMaximumHeight(320)
        self.tbl.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.setStyleSheet('''
            QTableWidget {background:#f8f7f3; border:1px solid #dde1df;
                border-radius:8px; font-family:"Segoe UI"; font-size:10px;}
            QTableWidget::item {padding:5px 10px; color:#344a5b; border:none;}
            QTableWidget::item:selected {background:#e3ede9; color:#203447;}
            QTableWidget::item:alternate {background:#f1f1ed;}
            QHeaderView::section {background:#edecea; color:#68747d; font-weight:600;
                font-size:9px; font-family:"Segoe UI"; padding:5px 10px;
                border:none; border-bottom:1px solid #dde1df;}
            QScrollBar:vertical {background:#ebebe7; width:6px; border-radius:3px; margin:0;}
            QScrollBar::handle:vertical {background:#c5c8c6; border-radius:3px; min-height:24px;}
            QScrollBar::handle:vertical:hover {background:#a8aaa8;}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0;}
        ''')
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        lay.addWidget(self.tbl)

    def carregar(self, documentos: list[dict]) -> None:
        self.tbl.setRowCount(0)
        for doc in documentos:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setRowHeight(r, 34)
            self.tbl.setItem(r, 0, QTableWidgetItem(doc['nome']))
            self.tbl.setItem(r, 1, QTableWidgetItem(Path(doc['nome_arquivo']).name))
            n = len(doc['emails'])
            self.tbl.setItem(r, 2, QTableWidgetItem(f'{n} e-mail{"s" if n != 1 else ""}'))
            self._set_status(r, ST_CONFIRMADO)

    def atualizar_status(self, row: int, status: str) -> None:
        self._set_status(row, status)

    def _set_status(self, row: int, status: str) -> None:
        item = QTableWidgetItem(status)
        item.setTextAlignment(Qt.AlignCenter)
        bg, fg = _COR_ST.get(status, ('#f1f1ed', '#8c929a'))
        item.setBackground(QColor(bg))
        item.setForeground(QColor(fg))
        f = QFont('Segoe UI', 9)
        f.setWeight(QFont.Medium)
        item.setFont(f)
        self.tbl.setItem(row, 3, item)


# ── Janela principal ──────────────────────────────────────────────────────────

_base_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


class Interface(QWidget):
    sinal_cofres_carregados = Signal(list)
    sinal_doc_enviando      = Signal(int)
    sinal_doc_enviado       = Signal(int)
    sinal_doc_falhou        = Signal(int, str)
    sinal_automacao_ok      = Signal(int, int, int)   # total, sucesso, erros
    sinal_automacao_falhou  = Signal(str)
    _sinal_update           = Signal(str, str)        # texto, cor
    _sinal_update_concluido = Signal()

    def __init__(self):
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._app.setStyle('Fusion')
        super().__init__()

        self.planilha_path        = ''
        self.pasta_documentos     = ''
        self.documentos: list[dict] = []
        self.lista_cofres: list[dict] = []
        self.navegador: Navegador | None = None
        self.automacao_em_andamento = False
        self._linhas_duplicadas: list = []
        self._cabecalhos_planilha: list = []
        self._info_update: dict = {}

        self.setWindowTitle('Enviar Assinaturas D4Sign')
        _logo = _base_dir / 'logo.ico'
        if _logo.is_file():
            self.setWindowIcon(QIcon(str(_logo)))
        self.resize(1180, 770)
        self.setMinimumSize(880, 600)
        self.setStyleSheet(f'background:{BG};')

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 24, 48, 26)
        root.setSpacing(0)
        self._montar_cabecalho(root)
        center = QHBoxLayout()
        center.setSpacing(65)
        center.addLayout(self._montar_painel_esquerdo(), 5)
        center.addWidget(self._montar_cartao(), 9)
        root.addLayout(center, 1)
        self._montar_rodape(root)

        self.sinal_cofres_carregados.connect(self._cofres_carregados)
        self.sinal_doc_enviando.connect(lambda r: self.tabela_widget.atualizar_status(r, ST_ENVIANDO))
        self.sinal_doc_enviado.connect(lambda r: self.tabela_widget.atualizar_status(r, ST_ENVIADO))
        self.sinal_doc_falhou.connect(lambda r, _msg: self.tabela_widget.atualizar_status(r, ST_ERRO))
        self.sinal_automacao_ok.connect(self._ao_concluir_automacao)
        self.sinal_automacao_falhou.connect(self._ao_falhar_automacao)
        self._sinal_update.connect(self._ao_status_update)
        self._sinal_update_concluido.connect(self._ao_update_concluido)

        self._atualizar_estado()
        self.show()
        threading.Thread(target=self._verificar_atualizacoes_bg, daemon=True).start()
        sys.exit(self._app.exec())

    # ── Montagem ──────────────────────────────────────────────────────────────

    def _montar_cabecalho(self, root):
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(5)
        left.addWidget(_rotulo('E N V I O   D E   A S S I N A T U R A S', 9, '#85929c', QFont.Bold))
        left.addWidget(_rotulo('Automação D4Sign', 14, TEXT, QFont.DemiBold))
        hdr.addLayout(left)
        hdr.addStretch()
        root.addLayout(hdr)
        root.addSpacing(20)
        root.addWidget(_divisor(COR_DIVISOR_ESCURO))

    def _montar_painel_esquerdo(self):
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)
        left.addStretch()
        left.addWidget(_rotulo('A U T O M A Ç Ã O   D 4 S I G N', 9, ACTION, QFont.Bold))
        left.addSpacing(20)
        left.addWidget(_rotulo('Envie documentos\npara assinatura\ndigital.', 29, TEXT, QFont.DemiBold, True))
        left.addSpacing(22)
        intro = _rotulo(
            'Carrega os documentos PDF de uma pasta, lê os signatários de uma '
            'planilha Excel e envia cada arquivo para assinatura no portal D4Sign '
            'automaticamente.',
            12, '#a5afb6', wrap=True,
        )
        intro.setMinimumWidth(270)
        intro.setMaximumWidth(365)
        left.addWidget(intro)
        left.addSpacing(37)
        left.addWidget(_divisor(COR_DIVISOR_ESCURO))
        left.addSpacing(24)
        sec = QHBoxLayout()
        sec.setSpacing(14)
        circle = QFrame()
        circle.setFixedSize(34, 34)
        circle.setStyleSheet('background:#304658; border-radius:17px;')
        cl = QHBoxLayout(circle)
        cl.setContentsMargins(5, 5, 5, 5)
        cl.addWidget(Icon('file', '#a6b4bd', 20))
        sec.addWidget(circle, 0, Qt.AlignTop)
        sec.addWidget(
            _rotulo(
                'Os documentos são enviados diretamente ao D4Sign a partir da sua máquina. '
                'Nada é armazenado externamente.',
                10, '#8998a3', wrap=True,
            ), 1,
        )
        left.addLayout(sec)
        left.addStretch()
        return left

    def _montar_cartao(self):
        card = QFrame()
        card.setObjectName('card')
        card.setStyleSheet('#card {background:#f8f7f3; border-radius:18px;}')
        sombra = QGraphicsDropShadowEffect(card)
        sombra.setBlurRadius(52)
        sombra.setOffset(0, 22)
        sombra.setColor(QColor(6, 18, 28, 80))
        card.setGraphicsEffect(sombra)
        lay = QVBoxLayout(card)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        self._montar_titulo_cartao(lay)
        lay.addWidget(_divisor('#dde1df'))
        self._montar_corpo_cartao(lay)
        self._montar_rodape_cartao(lay)
        return card

    def _montar_titulo_cartao(self, lay):
        top = QHBoxLayout()
        top.setContentsMargins(30, 20, 30, 16)
        titles = QVBoxLayout()
        titles.setSpacing(5)
        titles.addWidget(_rotulo('Enviar documentos para assinatura via D4Sign', 14, BG, QFont.DemiBold))
        self.subtitle = _rotulo('Selecione a pasta de documentos e a planilha para começar.', 10, '#7a838a')
        titles.addWidget(self.subtitle)
        top.addLayout(titles)
        top.addStretch()
        self.badge_total = _rotulo('0 documentos', 9, '#68747d', QFont.Bold)
        self.badge_total.setStyleSheet(
            'color:#68747d; background:transparent; border:1px solid #d9dddc; border-radius:12px; padding:7px 12px;'
        )
        top.addWidget(self.badge_total)
        lay.addLayout(top)

    def _montar_corpo_cartao(self, lay):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('''
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #ebebe7; width: 6px; border-radius: 3px; margin: 0; }
            QScrollBar::handle:vertical { background: #c5c8c6; border-radius: 3px; min-height: 24px; }
            QScrollBar::handle:vertical:hover { background: #a8aaa8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        ''')
        conteudo = QWidget()
        conteudo.setStyleSheet('background: transparent;')
        cly = QVBoxLayout(conteudo)
        cly.setContentsMargins(0, 0, 0, 0)
        cly.setSpacing(0)

        # ── Bloco de seleção (some após confirmar) ────────────────────────────
        self.row_pasta = SelectionRow(
            '01', 'Pasta de documentos',
            'Pasta contendo os arquivos PDF a serem enviados para assinatura.',
            'Selecionar pasta', 'folder', self.selecionar_documentos,
        )
        cly.addWidget(self.row_pasta)
        self.div_pasta = _divisor('#e3e5e2')
        cly.addWidget(self.div_pasta)

        self.row_planilha = SelectionRow(
            '02', 'Planilha de signatários',
            'Planilha .xlsx com colunas: nome, email (ou email1, email2...).',
            'Selecionar planilha', 'file', self.selecionar_planilha,
        )
        cly.addWidget(self.row_planilha)

        # ── Mensagem (acima da tabela, some quando não confirmado) ───────────
        self.div_msg = _divisor('#e3e5e2')
        self.div_msg.hide()
        cly.addWidget(self.div_msg)
        self.msg_frame = QFrame()
        self.msg_frame.hide()
        self.msg_frame.setStyleSheet('background:transparent; border:none;')
        mlay = QVBoxLayout(self.msg_frame)
        mlay.setContentsMargins(16, 12, 16, 8)
        mlay.setSpacing(6)
        mlay.addWidget(_rotulo('Texto da mensagem para assinatura', 10, BG, QFont.DemiBold))
        self.mensagem_texto = QTextEdit()
        self.mensagem_texto.setPlaceholderText('Digite a mensagem que será enviada aos signatários...')
        self.mensagem_texto.setFixedHeight(80)
        self.mensagem_texto.setStyleSheet('''
            QTextEdit {background:#ffffff; border:1px solid #dde1df; border-radius:8px;
                font-family:"Segoe UI"; font-size:11px; color:#344a5b; padding:8px;}
            QTextEdit:focus {border-color:#a0b0bc;}
        ''')
        mlay.addWidget(self.mensagem_texto)
        cly.addWidget(self.msg_frame)

        # ── Tabela de documentos confirmados ──────────────────────────────────
        self.div_tabela = _divisor('#e3e5e2')
        self.div_tabela.hide()
        cly.addWidget(self.div_tabela)
        self.tabela_widget = TabelaDocumentos()
        self.tabela_widget.hide()
        cly.addWidget(self.tabela_widget)

        # ── Seleção de cofre ──────────────────────────────────────────────────
        self.div_cofres = _divisor('#e3e5e2')
        self.div_cofres.hide()
        cly.addWidget(self.div_cofres)
        self.cofres_frame = QFrame()
        self.cofres_frame.hide()
        self.cofres_frame.setStyleSheet('background:transparent; border:none;')
        clay = QVBoxLayout(self.cofres_frame)
        clay.setContentsMargins(16, 12, 16, 16)
        clay.setSpacing(8)
        clay.addWidget(_rotulo('Cofre para envio', 10, BG, QFont.DemiBold))
        self.cofre_combo = QComboBox()
        self.cofre_combo.setStyleSheet('''
            QComboBox {background:#ffffff; border:1px solid #dde1df; border-radius:8px;
                font-family:"Segoe UI"; font-size:11px; color:#344a5b;
                padding:6px 12px; min-height:34px;}
            QComboBox::drop-down {border:none; padding-right:8px;}
            QComboBox QAbstractItemView {background:#ffffff; border:1px solid #dde1df;
                font-family:"Segoe UI"; font-size:11px; color:#344a5b;}
        ''')
        clay.addWidget(self.cofre_combo)
        self.continuar_btn = QPushButton('Continuar automação  →')
        self.continuar_btn.setFixedHeight(42)
        self.continuar_btn.setCursor(Qt.PointingHandCursor)
        self.continuar_btn.setStyleSheet(ESTILO_INICIAR_ATIVO)
        self.continuar_btn.clicked.connect(self.continuar_automacao)
        clay.addWidget(self.continuar_btn)
        cly.addWidget(self.cofres_frame)

        cly.addStretch()
        scroll.setWidget(conteudo)
        lay.addWidget(scroll, 1)

    def _montar_rodape_cartao(self, lay):
        footer = QFrame()
        footer.setStyleSheet(
            'background:#f1f1ed; border-bottom-left-radius:18px; border-bottom-right-radius:18px;'
        )
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(30, 20, 30, 20)
        texts = QVBoxLayout()
        texts.setSpacing(5)
        self.ready_title = _rotulo('Aguardando seleção', 10, '#344a5b', QFont.DemiBold)
        self.ready_hint  = _rotulo(
            'Selecione a pasta de documentos e a planilha para continuar.', 9, '#838c91', wrap=True
        )
        texts.addWidget(self.ready_title)
        texts.addWidget(self.ready_hint)
        fl.addLayout(texts, 1)
        self.chk_oculto = QCheckBox('Modo oculto')
        self.chk_oculto.setToolTip('Executar Chrome em segundo plano (sem janela visível)')
        self.chk_oculto.setStyleSheet('''
            QCheckBox { color:#344a5b; font-family:"Segoe UI"; font-size:10px; spacing:6px; }
            QCheckBox::indicator { width:16px; height:16px; border-radius:4px;
                border:2px solid #c0c8cc; background:#fff; }
            QCheckBox::indicator:checked { background:#e94c1f; border-color:#e94c1f; }
            QCheckBox::indicator:checked::after { color:#fff; }
        ''')
        fl.addWidget(self.chk_oculto)
        fl.addSpacing(16)
        self.start_btn = QPushButton('Aguardando seleção')
        self.start_btn.setFixedHeight(46)
        self.start_btn.setMinimumWidth(190)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._acao_principal)
        fl.addWidget(self.start_btn)
        lay.addWidget(footer)

    def _montar_rodape(self, root):
        root.addWidget(_divisor(COR_DIVISOR_ESCURO))
        root.addSpacing(17)
        bot = QHBoxLayout()
        bot.addWidget(
            _rotulo('Automação D4Sign — Envio de Documentos para Assinatura Digital', 9, '#83919c')
        )
        bot.addStretch()
        self._btn_update = QPushButton('')
        self._btn_update.setFlat(True)
        self._btn_update.setStyleSheet(
            'QPushButton { color:#83919c; font-family:"Segoe UI"; font-size:9px;'
            ' border:none; padding:0; background:transparent; }'
        )
        self._btn_update.clicked.connect(self._iniciar_atualizacao)
        bot.addWidget(self._btn_update)
        root.addLayout(bot)

    # ── Estado da UI ──────────────────────────────────────────────────────────

    def _atualizar_estado(self):
        n = len(self.documentos)
        self.badge_total.setText(f'{n} documento{"s" if n != 1 else ""}')

        confirmado  = n > 0
        selecao_ok  = bool(self.planilha_path and self.pasta_documentos) and not confirmado
        rodando     = self.automacao_em_andamento

        if rodando:
            self.subtitle.setText('Automação em andamento...')
            self.ready_title.setText('Automação em andamento')
            self.ready_hint.setText('Aguarde o carregamento dos cofres disponíveis.')
            self.start_btn.setText('◌  Iniciando...')
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet(ESTILO_INICIAR_RODANDO)
        elif selecao_ok:
            self.subtitle.setText('Seleção pronta. Confirme para carregar os documentos.')
            self.ready_title.setText('Pronto para confirmar')
            self.ready_hint.setText('Clique em Confirmar seleção para validar a planilha.')
            self.start_btn.setText('Confirmar seleção  →')
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(ESTILO_INICIAR_ATIVO)
        elif confirmado:
            self.subtitle.setText(
                f'{n} documento{"s" if n != 1 else ""} carregado{"s" if n != 1 else ""}. Revise e inicie.'
            )
            self.ready_title.setText('Tudo pronto para iniciar')
            self.ready_hint.setText('Revise os documentos e clique em Iniciar automação.')
            self.start_btn.setText('Iniciar automação  →')
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(ESTILO_INICIAR_ATIVO)
        else:
            self.subtitle.setText('Selecione a pasta de documentos e a planilha para começar.')
            self.ready_title.setText('Aguardando seleção')
            self.ready_hint.setText('Selecione a pasta de documentos e a planilha para continuar.')
            self.start_btn.setText('Aguardando seleção')
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet(ESTILO_INICIAR_INATIVO)

    def _acao_principal(self):
        if self.automacao_em_andamento:
            return
        if self.documentos:
            self.iniciar_automacao()
        else:
            self.confirmar_selecao()

    # ── Seleção de arquivos ───────────────────────────────────────────────────

    def selecionar_planilha(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Selecionar planilha', '',
            'Planilhas Excel (*.xlsx);;Todos os arquivos (*.*)',
        )
        if not path:
            return
        self.planilha_path = path
        self.row_planilha.definir_valor(Path(path).name)
        self._resetar_confirmacao()

    def selecionar_documentos(self):
        path = QFileDialog.getExistingDirectory(self, 'Selecionar pasta de documentos')
        if not path:
            return
        self.pasta_documentos = path
        self.row_pasta.definir_valor(path)
        self._resetar_confirmacao()

    def _resetar_confirmacao(self):
        self.documentos = []
        self.row_pasta.show()
        self.div_pasta.show()
        self.row_planilha.show()
        self.div_tabela.hide()
        self.tabela_widget.hide()
        self.div_msg.hide()
        self.msg_frame.hide()
        self.div_cofres.hide()
        self.cofres_frame.hide()
        self._atualizar_estado()

    # ── Confirmação ───────────────────────────────────────────────────────────

    def confirmar_selecao(self):
        if not self.pasta_documentos or not self.planilha_path:
            _dialogo(self, 'Seleção incompleta',
                     'Selecione a pasta e a planilha para confirmar.', QMessageBox.Warning)
            return
        try:
            self.documentos = self.carregar_documentos(self.planilha_path, self.pasta_documentos)
        except Exception as erro:
            _dialogo(self, 'Planilha inválida', str(erro), QMessageBox.Critical)
            return
        if self._linhas_duplicadas:
            n = len(self._linhas_duplicadas)
            nomes_dup = ", ".join(sorted({l["nome"] for l in self._linhas_duplicadas}))
            _dialogo(
                self, 'Nomes duplicados ignorados',
                f'{n} linha(s) ignorada(s) por nome duplicado:\n{nomes_dup}\n\n'
                'Essas linhas serão mantidas na planilha com status "Nome duplicado".',
                QMessageBox.Warning,
            )
        self.row_pasta.hide()
        self.div_pasta.hide()
        self.row_planilha.hide()
        self.div_msg.show()
        self.msg_frame.show()
        self.div_tabela.show()
        self.tabela_widget.carregar(self.documentos)
        self.tabela_widget.show()
        self._atualizar_estado()

    # ── Normalização e carga da planilha ──────────────────────────────────────

    @staticmethod
    def _normalizar_cabecalho(valor):
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        return "".join(c for c in texto if not unicodedata.combining(c)).strip().lower().replace(" ", "_")

    @staticmethod
    def _normalizar_nome_arquivo(valor):
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c)).casefold()
        return " ".join(re.findall(r"[a-z0-9]+", texto))

    def carregar_documentos(self, caminho_planilha, pasta_documentos):
        workbook = load_workbook(caminho_planilha, read_only=True, data_only=True)
        planilha = workbook.active
        linhas_iter = planilha.iter_rows(values_only=True)
        cabecalhos = next(linhas_iter, None)
        if not cabecalhos:
            raise ValueError("A planilha está vazia.")
        self._cabecalhos_planilha = list(cabecalhos)
        indices = {
            self._normalizar_cabecalho(v): i
            for i, v in enumerate(cabecalhos) if v is not None
        }
        indices_email = [
            i for cab, i in indices.items()
            if cab in ("email", "e_mail")
            or cab.startswith("email_")
            or re.fullmatch(r"email\d+", cab)
        ]
        indice_nome = indices.get("nome")
        if not indices_email or indice_nome is None:
            raise ValueError(
                "A planilha deve ter uma coluna 'nome' "
                "e ao menos uma coluna 'email', 'email1', 'email2' etc."
            )
        arquivos = [
            arq for arq in Path(pasta_documentos).iterdir()
            if arq.is_file() and arq.suffix.casefold() == ".pdf"
        ]

        # Primeira passagem: coletar todas as linhas válidas
        todas_linhas = []
        for num_linha, valores in enumerate(list(linhas_iter), start=2):
            if not valores or not any(v is not None and str(v).strip() for v in valores):
                continue
            nome = str(valores[indice_nome] or "").strip() if indice_nome < len(valores) else ""
            emails = [
                str(valores[i] or "").strip()
                for i in indices_email
                if i < len(valores) and valores[i] is not None and str(valores[i]).strip()
            ]
            if not emails or not nome:
                raise ValueError(f"Linha {num_linha}: informe nome e ao menos um e-mail.")
            todas_linhas.append({
                "num": num_linha,
                "nome": nome,
                "emails": emails,
                "valores": tuple(valores),
            })
        workbook.close()

        # Detectar nomes duplicados
        contagem: dict[str, int] = {}
        for l in todas_linhas:
            chave_n = l["nome"].casefold()
            contagem[chave_n] = contagem.get(chave_n, 0) + 1
        nomes_dup = {n for n, c in contagem.items() if c > 1}

        self._linhas_duplicadas = [l for l in todas_linhas if l["nome"].casefold() in nomes_dup]
        linhas_validas = [l for l in todas_linhas if l["nome"].casefold() not in nomes_dup]

        # Montar documentos a partir das linhas válidas
        agrupados: dict[str, dict] = {}
        for l in linhas_validas:
            nome = l["nome"]
            alvo = self._normalizar_nome_arquivo(nome)
            candidatos = [arq for arq in arquivos if self._normalizar_nome_arquivo(arq.stem) == alvo]
            if not candidatos:
                tokens = alvo.split()
                candidatos = [
                    arq for arq in arquivos
                    if all(t in self._normalizar_nome_arquivo(arq.stem).split() for t in tokens)
                ]
            if not candidatos:
                raise ValueError(
                    f"Linha {l['num']}: não encontrei arquivo compatível com '{nome}' na pasta."
                )
            if len(candidatos) > 1:
                nomes_arq = ", ".join(arq.name for arq in candidatos)
                raise ValueError(
                    f"Linha {l['num']}: mais de um arquivo corresponde a '{nome}': {nomes_arq}."
                )
            arq   = candidatos[0]
            chave = str(arq.resolve())
            if chave not in agrupados:
                agrupados[chave] = {
                    "nome": nome or arq.stem,
                    "emails": [],
                    "nome_arquivo": chave,
                    "linhas_planilha": [],
                }
            agrupados[chave]["emails"].extend(l["emails"])
            agrupados[chave]["linhas_planilha"].append({"num": l["num"], "valores": l["valores"]})

        if not agrupados and not self._linhas_duplicadas:
            raise ValueError("A planilha não contém linhas de signatários para processar.")
        if not agrupados and self._linhas_duplicadas:
            raise ValueError(
                "Todos os nomes da planilha estão duplicados — corrija a planilha antes de prosseguir."
            )
        return list(agrupados.values())

    # ── Automação — fase 1: login e cofres ────────────────────────────────────

    def iniciar_automacao(self):
        if self.automacao_em_andamento:
            return
        self.automacao_em_andamento = True
        self._atualizar_estado()
        threading.Thread(target=self._executar_inicio, daemon=True).start()

    def _executar_inicio(self):
        try:
            self.navegador = Navegador(self.mostrar_cofres, headless=self.chk_oculto.isChecked())
            if not self.navegador.status_login:
                self.navegador.realizar_login()
            self.navegador.abrir_tela_envio()
            self.navegador.carregar_cofres()
        except Exception as erro:
            logger.exception("Falha durante a inicialização e leitura dos cofres")
            self.sinal_automacao_falhou.emit(str(erro))
        finally:
            self.automacao_em_andamento = False

    def mostrar_cofres(self, cofres):
        self.sinal_cofres_carregados.emit(cofres)

    def _cofres_carregados(self, cofres: list[dict]):
        self.lista_cofres = cofres
        self.cofre_combo.clear()
        for cofre in cofres:
            self.cofre_combo.addItem(cofre["texto"], cofre["valor"])
        self.cofres_frame.show()
        self.div_cofres.show()
        self.ready_title.setText(f'{len(cofres)} cofre(s) disponível(is)')
        self.ready_hint.setText('Selecione o cofre e clique em Continuar automação.')

    # ── Automação — fase 2: envio dos documentos ──────────────────────────────

    def continuar_automacao(self):
        if self.automacao_em_andamento or not self.lista_cofres:
            return
        idx = self.cofre_combo.currentIndex()
        if idx < 0:
            _dialogo(self, 'Cofre inválido', 'Selecione um cofre disponível.', QMessageBox.Warning)
            return
        texto = self.mensagem_texto.toPlainText().strip()
        if not texto:
            _dialogo(self, 'Mensagem obrigatória',
                     'Digite o texto da mensagem para assinatura.', QMessageBox.Warning)
            return
        cofre = self.lista_cofres[idx]
        self.automacao_em_andamento = True
        self.continuar_btn.setEnabled(False)
        self.continuar_btn.setStyleSheet(ESTILO_INICIAR_RODANDO)
        threading.Thread(
            target=self._enviar_arquivos,
            args=(cofre, list(self.documentos), texto),
            daemon=True,
        ).start()

    def _enviar_arquivos(self, cofre, documentos, texto):
        erros: dict[int, str] = {}
        for i, doc in enumerate(documentos):
            self.sinal_doc_enviando.emit(i)
            try:
                self.navegador.selecionar_cofre(cofre["valor"])
                self.navegador.upload_documento(str(Path(doc["nome_arquivo"])))
                self.navegador.adicionar_emails(doc["emails"])
                self.navegador.envio_para_assinatura(texto)
                if i + 1 < len(documentos):
                    self.navegador.voltar_para_envio()
                self.sinal_doc_enviado.emit(i)
            except Exception as erro:
                logger.exception(f"Falha no documento [{i}] {doc.get('nome', '')}")
                msg_erro = str(erro)
                erros[i] = msg_erro
                self.sinal_doc_falhou.emit(i, msg_erro)
                # Tenta recuperar para o próximo documento
                if i + 1 < len(documentos):
                    try:
                        self.navegador.voltar_para_envio()
                    except Exception:
                        pass

        try:
            self._atualizar_planilha_resultado(erros)
        except Exception:
            logger.exception("Falha ao atualizar planilha após automação")

        self.automacao_em_andamento = False
        sucesso = len(documentos) - len(erros)
        self.sinal_automacao_ok.emit(len(documentos), sucesso, len(erros))

    def _ao_concluir_automacao(self, total: int, sucesso: int, num_erros: int):
        self.continuar_btn.setEnabled(True)
        self.continuar_btn.setStyleSheet(ESTILO_INICIAR_ATIVO)
        partes = [
            f'{sucesso} de {total} documento(s) enviado(s) para assinatura'
            f' no cofre "{self.cofre_combo.currentText()}".'
        ]
        if num_erros:
            partes.append(
                f'{num_erros} documento(s) com erro foram mantidos na planilha original com a mensagem de erro.'
            )
        n_dup = len(self._linhas_duplicadas)
        if n_dup:
            partes.append(
                f'{n_dup} linha(s) ignorada(s) por nome duplicado foram mantidas na planilha.'
            )
        icon = QMessageBox.Warning if (num_erros or n_dup) else QMessageBox.Information
        _dialogo(self, 'Automação concluída', '\n\n'.join(partes), icon)

    def _ao_falhar_automacao(self, msg: str):
        self._atualizar_estado()
        self.continuar_btn.setEnabled(True)
        self.continuar_btn.setStyleSheet(ESTILO_INICIAR_ATIVO)
        _dialogo(
            self, 'Falha na automação',
            f'Ocorreu um erro:\n{msg}\n\nConsulte o log: {ERROR_LOG}',
            QMessageBox.Critical,
        )

    # ── Reescrita da planilha após automação ──────────────────────────────────

    def _atualizar_planilha_resultado(self, erros_por_indice: dict):
        from openpyxl import load_workbook as _lw
        wb = _lw(self.planilha_path)
        ws1 = wb.active

        # Encontra ou adiciona coluna "status"
        num_colunas = ws1.max_column or 0
        cab_norm = [
            self._normalizar_cabecalho(ws1.cell(1, c).value or "")
            for c in range(1, num_colunas + 1)
        ]
        if "status" in cab_norm:
            idx_status = cab_norm.index("status") + 1
        else:
            idx_status = num_colunas + 1
            ws1.cell(1, idx_status, "status")

        # Limpa dados da planilha 1 (mantém cabeçalho)
        if ws1.max_row > 1:
            ws1.delete_rows(2, ws1.max_row - 1)

        # Cria ou limpa aba "Enviados"
        if "Enviados" in wb.sheetnames:
            ws2 = wb["Enviados"]
            if ws2.max_row > 1:
                ws2.delete_rows(2, ws2.max_row - 1)
        else:
            ws2 = wb.create_sheet("Enviados")
            for c in range(1, idx_status):
                ws2.cell(1, c, ws1.cell(1, c).value)
            ws2.cell(1, idx_status, "status")

        def _escrever_linha(ws, row, valores, status_val):
            for col, val in enumerate(valores, 1):
                if col != idx_status:
                    ws.cell(row, col, val)
            ws.cell(row, idx_status, status_val)

        # Linhas duplicadas → aba 1
        prox1 = 2
        for l in self._linhas_duplicadas:
            _escrever_linha(ws1, prox1, l["valores"], "Nome duplicado")
            prox1 += 1

        # Documentos: erro → aba 1, sucesso → aba 2
        prox2 = 2
        for i, doc in enumerate(self.documentos):
            for linha in doc.get("linhas_planilha", []):
                if i in erros_por_indice:
                    _escrever_linha(ws1, prox1, linha["valores"], erros_por_indice[i][:250])
                    prox1 += 1
                else:
                    _escrever_linha(ws2, prox2, linha["valores"], "Enviado")
                    prox2 += 1

        wb.save(self.planilha_path)
        wb.close()

    # ── Atualizador automático ────────────────────────────────────────────────

    def _verificar_atualizacoes_bg(self):
        try:
            from updater import verificar_atualizacao
            resultado = verificar_atualizacao()
            if resultado.get("versao_mais_nova") or resultado.get("disponivel"):
                self._info_update = resultado
                v = resultado.get("versao_nova", "")
                self._sinal_update.emit(f'● Nova versão {v} — clique para atualizar', '#e9a833')
            else:
                self._sinal_update.emit(f'● v{VERSION} — atualizado', '#5aaa7a')
        except Exception:
            self._sinal_update.emit(f'v{VERSION}', '#83919c')

    def _ao_status_update(self, texto: str, cor: str):
        tem_update = bool(self._info_update)
        self._btn_update.setText(texto)
        underline = 'text-decoration:underline;' if tem_update else ''
        cursor = Qt.PointingHandCursor if tem_update else Qt.ArrowCursor
        self._btn_update.setCursor(cursor)
        self._btn_update.setStyleSheet(
            f'QPushButton {{ color:{cor}; font-family:"Segoe UI"; font-size:9px;'
            f' border:none; padding:0; background:transparent; {underline} }}'
        )

    def _iniciar_atualizacao(self):
        if not self._info_update:
            return
        url      = self._info_update.get("url_download", "")
        versao   = self._info_update.get("versao_nova", "")
        if not url:
            _dialogo(self, 'Atualização disponível',
                     f'Nova versão {versao} disponível!\n'
                     'Baixe manualmente em:\ngithub.com/DaviTSelect/enviar-assinaturas-d4sign/releases/latest',
                     QMessageBox.Information)
            return
        resp = _dialogo(self, 'Atualizar agora?',
                        f'Nova versão {versao} disponível!\n\n'
                        'O programa vai baixar a atualização, fechar e reabrir automaticamente.\n\nContinuar?',
                        QMessageBox.Question, QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._btn_update.setEnabled(False)
        self._sinal_update.emit('⬇ Baixando atualização...', '#2563a8')
        threading.Thread(target=self._baixar_e_aplicar, daemon=True).start()

    def _baixar_e_aplicar(self):
        try:
            from updater import aplicar_atualizacao
            def _progresso(baixados, total):
                if total > 0:
                    pct = int(baixados * 100 / total)
                    mb  = baixados / 1_048_576
                    self._sinal_update.emit(f'⬇ {pct}% ({mb:.1f} MB)...', '#2563a8')
            aplicar_atualizacao(
                self._info_update["url_download"],
                self._info_update["versao_nova"],
                _progresso,
            )
            self._sinal_update_concluido.emit()
        except Exception as e:
            logger.exception("Falha ao baixar/aplicar atualização")
            self._sinal_update.emit(f'● Erro ao atualizar: clique para tentar novamente', '#c0351a')
            self._btn_update.setEnabled(True)

    def _ao_update_concluido(self):
        _dialogo(self, 'Atualização pronta',
                 'Download concluído!\n\nO programa será fechado e a nova versão abrirá automaticamente.',
                 QMessageBox.Information)
        self.close()

    def closeEvent(self, event):
        if self.automacao_em_andamento:
            resp = _dialogo(
                self, 'Fechar',
                'Uma automação está em andamento. Fechar agora pode deixar documentos incompletos.\n\nFechar mesmo assim?',
                QMessageBox.Question, QMessageBox.Yes | QMessageBox.No,
            )
            if resp == QMessageBox.No:
                event.ignore()
                return
        event.accept()
