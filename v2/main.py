import sys
import ctypes
import psutil
import os
import webbrowser
from ctypes import wintypes
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon
from PySide6.QtCore import QTimer, Qt

# =========================================================
# YAPILANDIRMA (Varsayılan Ayarlar)
# =========================================================
conf = {
    "font_name": "Bahnschrift",
    "font_size": 14,
    "font_stretch": QFont.SemiCondensed,
    "color_up": "#00FF00",
    "color_down": "#FF0000",
    "unit": "MB",
    "adapter": "Hepsi",
    "paused": False
}

COLORS = {
    "Yeşil": "#00FF00", "Turkuaz": "#00FFFF", "Sarı": "#FFFF00", 
    "Beyaz": "#FFFFFF", "Kırmızı": "#FF0000", "Turuncu": "#FFA500"
}
SIZES = [8, 9, 10, 11, 12, 14, 15, 16, 17]

# =========================================================
# WIN32 API & STARTUP AYARLARI
# =========================================================
user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32
advapi32 = ctypes.windll.advapi32

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_int64
WNDPROC_TYPE = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

WM_TRAY = 0x0401
WM_RBUTTONUP = 0x0205
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
TPM_RETURNCMD, TPM_RIGHTBUTTON = 0x0100, 0x0002
MF_STRING, MF_POPUP, MF_SEPARATOR, MF_CHECKED = 0x0000, 0x0010, 0x0800, 0x0008

ID_PAUSE, ID_EXIT, ID_STARTUP, ID_ABOUT = 1001, 1002, 1003, 1004
ID_UNIT_BASE, ID_ADAP_BASE, ID_SIZE_BASE, ID_UPCOL_BASE, ID_DNCOL_BASE = 2000, 2100, 2200, 2300, 2400

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AladinNetworkMonitor"

def set_startup(enable=True):
    hkey = wintypes.HKEY()
    advapi32.RegOpenKeyExW(0x80000001, REG_PATH, 0, 0x00020000 | 0x0002, ctypes.byref(hkey))
    if enable:
        path = sys.executable if getattr(sys, 'frozen', False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        advapi32.RegSetValueExW(hkey, APP_NAME, 0, 1, path, (len(path) + 1) * 2)
    else:
        advapi32.RegDeleteValueW(hkey, APP_NAME)
    advapi32.RegCloseKey(hkey)

def is_startup_enabled():
    hkey = wintypes.HKEY()
    res = advapi32.RegOpenKeyExW(0x80000001, REG_PATH, 0, 0x00020000 | 0x0001, ctypes.byref(hkey))
    if res != 0: return False
    res = advapi32.RegQueryValueExW(hkey, APP_NAME, None, None, None, None)
    advapi32.RegCloseKey(hkey)
    return res == 0

# =========================================================
# İKON OLUŞTURMA VE HIZ HESABI
# =========================================================
_net_init = psutil.net_io_counters()
last_up, last_down = _net_init.bytes_sent, _net_init.bytes_recv

def format_speed(bytes_val):
    val = bytes_val * 8 if conf["unit"] in ["b", "Kb", "Mb"] else bytes_val
    if "M" in conf["unit"]: val /= (1024 * 1024)
    elif "K" in conf["unit"]: val /= 1024
    return f"{val:.1f}" if val < 10 else f"{int(val)}"

def create_hicon(val_text, color_hex):
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    font = QFont(conf["font_name"], conf["font_size"])
    font.setStretch(conf["font_stretch"]); font.setBold(True)
    p.setFont(font); p.setPen(QColor(color_hex))
    p.drawText(pix.rect(), Qt.AlignCenter, val_text)
    p.end()
    icon = pix.toImage().toHICON()
    return icon

# =========================================================
# HAKKINDA EKRANI VE MENÜ
# =========================================================
def show_about():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Hakkında - Aladin Network Monitor")
    msg.setText("<b>Aladin Network Monitor v1.0</b><br><br>"
                "Geliştirici: <b>Alaaddin</b><br><br>"
                "GitHub: <a href='https://github.com/tezalaaddin'>github.com/tezalaaddin</a><br>"
                "Proje: <a href='https://github.com/tezalaaddin/aladinNetWorkMonitor'>Aladin Network Monitor</a>")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()

def show_menu(hwnd):
    hmenu = user32.CreatePopupMenu()
    
    # Üst Kısım
    user32.AppendMenuW(hmenu, MF_STRING, ID_ABOUT, "Hakkında")
    startup_flag = MF_STRING | (MF_CHECKED if is_startup_enabled() else 0)
    user32.AppendMenuW(hmenu, startup_flag, ID_STARTUP, "Başlangıçta Çalıştır")
    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

    # Birim Seçimi
    h_units = user32.CreatePopupMenu()
    for i, u in enumerate(["B", "b", "KB", "Kb", "MB", "Mb"]):
        user32.AppendMenuW(h_units, MF_STRING | (MF_CHECKED if conf["unit"] == u else 0), ID_UNIT_BASE + i, f"{u}/s")
    user32.AppendMenuW(hmenu, MF_POPUP, h_units, "Birim Seç")

    # Font Boyutu
    h_sizes = user32.CreatePopupMenu()
    for i, s in enumerate(SIZES):
        user32.AppendMenuW(h_sizes, MF_STRING | (MF_CHECKED if conf["font_size"] == s else 0), ID_SIZE_BASE + i, str(s))
    user32.AppendMenuW(hmenu, MF_POPUP, h_sizes, "Font Boyutu")

    # Renk Özelleştirme
    h_up_cols = user32.CreatePopupMenu()
    for i, (name, hex_val) in enumerate(COLORS.items()):
        user32.AppendMenuW(h_up_cols, MF_STRING | (MF_CHECKED if conf["color_up"] == hex_val else 0), ID_UPCOL_BASE + i, name)
    user32.AppendMenuW(hmenu, MF_POPUP, h_up_cols, "Upload Rengi")

    h_dn_cols = user32.CreatePopupMenu()
    for i, (name, hex_val) in enumerate(COLORS.items()):
        user32.AppendMenuW(h_dn_cols, MF_STRING | (MF_CHECKED if conf["color_down"] == hex_val else 0), ID_DNCOL_BASE + i, name)
    user32.AppendMenuW(hmenu, MF_POPUP, h_dn_cols, "Download Rengi")

    # Adaptör Seçimi
    h_adapters = user32.CreatePopupMenu()
    adapters = list(psutil.net_io_counters(pernic=True).keys())
    user32.AppendMenuW(h_adapters, MF_STRING | (MF_CHECKED if conf["adapter"] == "Hepsi" else 0), ID_ADAP_BASE, "Tüm Adaptörler")
    for i, name in enumerate(adapters[:20]):
        user32.AppendMenuW(h_adapters, MF_STRING | (MF_CHECKED if conf["adapter"] == name else 0), ID_ADAP_BASE + 1 + i, name)
    user32.AppendMenuW(hmenu, MF_POPUP, h_adapters, "Adaptör Seç")

    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(hmenu, MF_STRING, ID_PAUSE, "Devam Et" if conf["paused"] else "Duraklat")
    user32.AppendMenuW(hmenu, MF_STRING, ID_EXIT, "Çıkış")

    pt = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(pt))
    user32.SetForegroundWindow(hwnd)
    cmd = user32.TrackPopupMenu(hmenu, TPM_RIGHTBUTTON | TPM_RETURNCMD, pt.x, pt.y, 0, hwnd, None)
    user32.DestroyMenu(hmenu)

    # İşlemler
    if cmd == ID_ABOUT: show_about()
    elif cmd == ID_STARTUP: set_startup(not is_startup_enabled())
    elif cmd == ID_PAUSE: conf["paused"] = not conf["paused"]
    elif ID_UNIT_BASE <= cmd < ID_UNIT_BASE + 6: conf["unit"] = ["B", "b", "KB", "Kb", "MB", "Mb"][cmd - ID_UNIT_BASE]
    elif ID_SIZE_BASE <= cmd < ID_SIZE_BASE + len(SIZES): conf["font_size"] = SIZES[cmd - ID_SIZE_BASE]
    elif ID_UPCOL_BASE <= cmd < ID_UPCOL_BASE + len(COLORS): conf["color_up"] = list(COLORS.values())[cmd - ID_UPCOL_BASE]
    elif ID_DNCOL_BASE <= cmd < ID_DNCOL_BASE + len(COLORS): conf["color_down"] = list(COLORS.values())[cmd - ID_DNCOL_BASE]
    elif cmd == ID_ADAP_BASE: conf["adapter"] = "Hepsi"
    elif ID_ADAP_BASE < cmd <= ID_ADAP_BASE + len(adapters): conf["adapter"] = adapters[cmd - ID_ADAP_BASE - 1]
    elif cmd == ID_EXIT: QApplication.quit()

# =========================================================
# ANA ÇALIŞTIRMA VE TEMİZLİK
# =========================================================
def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_TRAY and lparam == WM_RBUTTONUP:
        show_menu(hwnd)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False) # Diyalog penceresi kapandığında uygulama kapanmasın

hinst = kernel32.GetModuleHandleW(None)
wptr = WNDPROC_TYPE(wnd_proc)

class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC_TYPE), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON), ("hCursor", wintypes.HCURSOR), ("hbrBackground", wintypes.HBRUSH), ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

wc = WNDCLASS(lpfnWndProc=wptr, hInstance=hinst, lpszClassName="NetMonFinal_V12")
user32.RegisterClassW(ctypes.byref(wc))
hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "NetTray", 0, 0, 0, 0, 0, None, None, hinst, None)

class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT), ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON), ("szTip", wintypes.WCHAR * 128)]

nid_up = NOTIFYICONDATA(cbSize=ctypes.sizeof(NOTIFYICONDATA), hWnd=hwnd, uID=1, uFlags=7, uCallbackMessage=WM_TRAY, szTip="Upload")
nid_down = NOTIFYICONDATA(cbSize=ctypes.sizeof(NOTIFYICONDATA), hWnd=hwnd, uID=2, uFlags=7, uCallbackMessage=WM_TRAY, szTip="Download")
shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid_up))
shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid_down))

def cleanup():
    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid_up))
    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid_down))
    if nid_up.hIcon: user32.DestroyIcon(nid_up.hIcon)
    if nid_down.hIcon: user32.DestroyIcon(nid_down.hIcon)

app.aboutToQuit.connect(cleanup)

def update():
    global last_up, last_down
    if conf["paused"]: return
    try: 
        net = psutil.net_io_counters() if conf["adapter"] == "Hepsi" else psutil.net_io_counters(pernic=True).get(conf["adapter"], psutil.net_io_counters())
    except: return
    
    up_s, down_s = net.bytes_sent - last_up, net.bytes_recv - last_down
    last_up, last_down = net.bytes_sent, net.bytes_recv
    
    # Eski ikonları bellekten temizle
    if nid_up.hIcon: user32.DestroyIcon(nid_up.hIcon)
    if nid_down.hIcon: user32.DestroyIcon(nid_down.hIcon)
    
    nid_up.hIcon = create_hicon(format_speed(up_s), conf["color_up"])
    nid_down.hIcon = create_hicon(format_speed(down_s), conf["color_down"])
    
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid_up))
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid_down))

timer = QTimer(); timer.timeout.connect(update); timer.start(1000)
app.exec()
