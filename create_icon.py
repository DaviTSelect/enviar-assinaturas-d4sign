"""Gera logo.ico simples para o projeto. Execute uma vez: python create_icon.py"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

sizes = [256, 128, 64, 32, 16]
pixmaps = []

for size in sizes:
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    # Fundo arredondado
    p.setBrush(QColor("#203447"))
    p.setPen(Qt.NoPen)
    radius = size // 6
    p.drawRoundedRect(0, 0, size, size, radius, radius)

    # Letra "D4"
    font = QFont("Segoe UI", size // 3, QFont.Bold)
    p.setFont(font)
    p.setPen(QColor("#e94c1f"))
    p.drawText(px.rect(), Qt.AlignCenter, "D4")

    p.end()
    pixmaps.append(px)

# Salva como ICO usando o maior tamanho
pixmaps[0].save("logo.ico", "ICO")
print("logo.ico gerado com sucesso.")
