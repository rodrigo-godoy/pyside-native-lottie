from .engine import LottieItem
from PySide6.QtQml import qmlRegisterType

def register():
    qmlRegisterType(LottieItem, "NativeLottie", 1, 0, "Lottie")