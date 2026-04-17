import sys
import psutil
import json
import os
import webbrowser
import winreg
from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QHBoxLayout, 
                             QVBoxLayout, QMenu, QFrame, QSystemTrayIcon)
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QFont, QAction, QPixmap, QIcon, QPainter, QColor

def aladin_kaynak_yolu(goreceli_yol):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, goreceli_yol)

class AladinNetMon(QWidget):
    def __init__(self):
        super().__init__()
        
        # Dosya ve Link Ayarları
        self.aladin_settings_file = "aladin_ayarlar.json"
        self.aladin_github_url = "https://github.com/tezalaaddin"
        self.exe_path = os.path.realpath(sys.argv[0])
        self.aladin_logo_path = aladin_kaynak_yolu("aladin_icon_logo.png")

        # Pencere Özellikleri
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Arayüz ve Tray Kurulumu
        self.setup_ui()
        self.setup_tray()
        self.aladin_konum_yukle()

        # İlk Değerler
        self.last_up = psutil.net_io_counters().bytes_sent
        self.last_down = psutil.net_io_counters().bytes_recv

        # Timer (Her saniye güncelle)
        self.aladin_timer = QTimer()
        self.aladin_timer.timeout.connect(self.aladin_guncelle)
        self.aladin_timer.start(1000)

    def setup_ui(self):
        self.aladin_main_layout = QHBoxLayout()
        self.aladin_logo_label = QLabel()
        if os.path.exists(self.aladin_logo_path):
            pix = QPixmap(self.aladin_logo_path)
            self.aladin_logo_label.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.aladin_speed_layout = QVBoxLayout()
        self.aladin_speed_layout.setSpacing(0)
        self.aladin_up_label = QLabel("↑ 0 KB/s")
        self.aladin_down_label = QLabel("↓ 0 KB/s")
        
        for lbl in [self.aladin_up_label, self.aladin_down_label]:
            lbl.setFont(QFont("Consolas", 10, QFont.Bold))
            self.aladin_speed_layout.addWidget(lbl)

        self.aladin_up_label.setStyleSheet("color: #00FF00; background: transparent;")
        self.aladin_down_label.setStyleSheet("color: #00E5FF; background: transparent;")

        self.aladin_main_layout.addWidget(self.aladin_logo_label)
        self.aladin_main_layout.addLayout(self.aladin_speed_layout)

        self.aladin_frame = QFrame()
        self.aladin_frame.setStyleSheet("""
            background-color: rgba(15, 15, 15, 220); 
            border-radius: 12px; 
            border: 1px solid #d4af37;
        """)
        self.aladin_frame.setLayout(self.aladin_main_layout)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.aladin_frame)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(self.aladin_logo_path):
            self.tray_icon.setIcon(QIcon(self.aladin_logo_path))
        
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("background-color: #222; color: white;")
        
        show_action = QAction("🧞 Göster", self)
        show_action.triggered.connect(self.show)
        
        exit_action = QAction("Tamamen Kapat", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_menu.addAction(show_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def aladin_ikon_olustur(self, metin):
        """Sistem tepsisi için dinamik rakamlı ikon çizer"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Arka plan yuvarlağı
        painter.setBrush(QColor(15, 15, 15, 230))
        painter.setPen(QColor("#d4af37")) # Altın kenarlık
        painter.drawRoundedRect(0, 0, 31, 31, 8, 8)
        
        # Rakam çizimi
        painter.setPen(QColor("#00E5FF"))
        font = QFont("Consolas", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, metin[:2])
        painter.end()
        
        return QIcon(pixmap)

    def is_autostart_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "aladinNetMon")
            winreg.CloseKey(key)
            return True
        except: return False

    def toggle_autostart(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if self.is_autostart_enabled():
            winreg.DeleteValue(key, "aladinNetMon")
        else:
            winreg.SetValueEx(key, "aladinNetMon", 0, winreg.REG_SZ, f'"{self.exe_path}"')
        winreg.CloseKey(key)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #222; color: white; border: 1px solid #444;")
        
        auto_act = QAction("🚀 Başlangıçta Çalıştır", self)
        auto_act.setCheckable(True)
        auto_act.setChecked(self.is_autostart_enabled())
        auto_act.triggered.connect(self.toggle_autostart)
        menu.addAction(auto_act)

        menu.addSeparator()
        
        tray_act = QAction("📥 Sistem Tepsisine Gizle", self)
        tray_act.triggered.connect(self.hide)
        menu.addAction(tray_act)

        about_act = QAction("🧞 About tezalaaddin", self)
        about_act.triggered.connect(lambda: webbrowser.open(self.aladin_github_url))
        menu.addAction(about_act)
        
        menu.addSeparator()
        exit_act = QAction("Kapat", self)
        exit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_act)
        menu.exec(event.globalPos())

    def format_hiz(self, b):
        if b < 1024**2: return f"{b/1024:.0f} KB/s"
        return f"{b/1024**2:.1f} MB/s"

    def aladin_guncelle(self):
        try:
            cnt = psutil.net_io_counters()
            up = cnt.bytes_sent - self.last_up
            down = cnt.bytes_recv - self.last_down
            self.last_up, self.last_down = cnt.bytes_sent, cnt.bytes_recv
            
            u_str, d_str = self.format_hiz(up), self.format_hiz(down)
            self.aladin_up_label.setText(f"↑ {u_str}")
            self.aladin_down_label.setText(f"↓ {d_str}")
            
            # Tray İkon Güncelleme
            if self.isHidden():
                # Download hızı MB ise MB değerini, KB ise KB değerini 2 hane göster
                val = int(down/1024/1024) if down > 1024**2 else int(down/1024)
                txt = str(val) if val < 100 else "99"
                self.tray_icon.setIcon(self.aladin_ikon_olustur(txt))
            else:
                if os.path.exists(self.aladin_logo_path):
                    self.tray_icon.setIcon(QIcon(self.aladin_logo_path))

            self.tray_icon.setToolTip(f"aladinNetMon\n↑ {u_str}\n↓ {d_str}")
        except: pass

    def aladin_konum_kaydet(self):
        with open(self.aladin_settings_file, "w") as f:
            json.dump({"x": self.x(), "y": self.y()}, f)

    def aladin_konum_yukle(self):
        if os.path.exists(self.aladin_settings_file):
            with open(self.aladin_settings_file, "r") as f:
                d = json.load(f)
                self.move(d["x"], d["y"])
        else:
            ekran = QApplication.primaryScreen().size()
            self.move(ekran.width() - 300, ekran.height() - 150)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            self.aladin_konum_kaydet()
    def mouseReleaseEvent(self, event): self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    widget = AladinNetMon()
    widget.show()
    sys.exit(app.exec())
