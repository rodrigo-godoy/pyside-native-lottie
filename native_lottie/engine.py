import ctypes
import os
import platform
import struct
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtCore import QTimer, Property, QUrl, Signal

# --- CARGA DEL MOTOR INTELIGENTE MULTIPLATAFORMA ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM = platform.system()
MACHINE = platform.machine().lower()

# Detectamos si el Python que corre es 32 o 64 bits
IS_64BIT = (struct.calcsize("P") * 8) == 64

lib_name = ""

if SYSTEM == "Darwin":  # macOS
    lib_name = "librlottie.dylib"

elif SYSTEM == "Windows":
    # Lógica de selección para Windows
    if "arm" in MACHINE or "aarch64" in MACHINE:
        lib_name = "rlottie.arm64.dll"
    elif IS_64BIT:
        lib_name = "rlottie.x64.dll"  # PC Estándar 64 bits
    else:
        lib_name = "rlottie.x86.dll"  # Python de 32 bits o Windows antiguo

else:
    raise OSError(f"Sistema no soportado: {SYSTEM}")

LIB_PATH = os.path.join(CURRENT_DIR, lib_name)

if not os.path.exists(LIB_PATH):
    # Fallback de emergencia: Si no encuentra el específico, busca uno genérico
    if SYSTEM == "Windows" and os.path.exists(os.path.join(CURRENT_DIR, "rlottie.dll")):
        LIB_PATH = os.path.join(CURRENT_DIR, "rlottie.dll")
    else:
        raise FileNotFoundError(f"CRÍTICO: Falta el motor {lib_name} en {CURRENT_DIR}")

# Carga de la librería
if SYSTEM == "Windows":
    rlottie_lib = ctypes.CDLL(LIB_PATH, winmode=0)
else:
    rlottie_lib = ctypes.CDLL(LIB_PATH)

# Definimos los tipos opacos (Punteros C)
LottieAnimation = ctypes.c_void_p

# Mapeo de funciones C necesarias
rlottie_lib.lottie_animation_from_file.argtypes = [ctypes.c_char_p]
rlottie_lib.lottie_animation_from_file.restype = LottieAnimation

rlottie_lib.lottie_animation_destroy.argtypes = [LottieAnimation]
rlottie_lib.lottie_animation_destroy.restype = None

rlottie_lib.lottie_animation_get_size.argtypes = [LottieAnimation, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
rlottie_lib.lottie_animation_get_size.restype = None

rlottie_lib.lottie_animation_get_totalframe.argtypes = [LottieAnimation]
rlottie_lib.lottie_animation_get_totalframe.restype = ctypes.c_size_t

rlottie_lib.lottie_animation_get_framerate.argtypes = [LottieAnimation]
rlottie_lib.lottie_animation_get_framerate.restype = ctypes.c_double

rlottie_lib.lottie_animation_render.argtypes = [
    LottieAnimation, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t
]
rlottie_lib.lottie_animation_render.restype = None


# --- CLASE COMPONENTE PYSIDE ---
class LottieItem(QQuickPaintedItem):
    # Señal para avisar a QML cuando termina
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = ""
        self._anim_handle = None
        self._total_frames = 0
        self._frame_rate = 60
        self._current_frame = 0
        self._loop = False  # Por defecto NO hace loop
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

    # --- PROPIEDAD SOURCE ---
    @Property(str)
    def source(self):
        return self._source

    @source.setter
    def source(self, path):
        if self._source == path:
            return
        self._source = path
        clean_path = QUrl(path).toLocalFile() if "file://" in path else path
        
        if os.path.exists(clean_path):
            self.load_animation(clean_path)
        else:
            print(f"[Engine] No encontrado: {clean_path}")

    # --- PROPIEDAD LOOP ---
    @Property(bool)
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value

    def load_animation(self, path):
        if self._anim_handle:
            rlottie_lib.lottie_animation_destroy(self._anim_handle)
        
        self._anim_handle = rlottie_lib.lottie_animation_from_file(path.encode('utf-8'))
        
        if self._anim_handle:
            self._total_frames = rlottie_lib.lottie_animation_get_totalframe(self._anim_handle)
            self._frame_rate = rlottie_lib.lottie_animation_get_framerate(self._anim_handle)
            self._current_frame = 0
            
            # Reiniciamos el timer
            if self._frame_rate > 0:
                self.timer.start(int(1000 / self._frame_rate))
                
            self.update()

    def next_frame(self):
        if not self._anim_handle:
            return
        
        self._current_frame += 1
        
        # LÓGICA DE FIN DE ANIMACIÓN
        if self._current_frame >= self._total_frames:
            if self._loop:
                self._current_frame = 0  # Reiniciar
            else:
                self._current_frame = self._total_frames - 1  # Quedarse en el último frame
                self.timer.stop()  # Detener consumo de CPU
                self.finished.emit()  # Avisar que terminó
                return
            
        self.update()

    def paint(self, painter):
        if not self._anim_handle:
            return

        render_w = int(self.width())
        render_h = int(self.height())
        if render_w <= 0 or render_h <= 0:
            return

        bytes_per_line = render_w * 4
        buffer_size = render_w * render_h * 4
        raw_buffer = ctypes.create_string_buffer(buffer_size)
        
        rlottie_lib.lottie_animation_render(
            self._anim_handle,
            self._current_frame,
            ctypes.cast(raw_buffer, ctypes.c_void_p),
            render_w,
            render_h,
            bytes_per_line
        )
        
        img = QImage(raw_buffer, render_w, render_h, bytes_per_line, QImage.Format_ARGB32_Premultiplied)
        painter.drawImage(0, 0, img)

    def __del__(self):
        if self._anim_handle:
            rlottie_lib.lottie_animation_destroy(self._anim_handle)