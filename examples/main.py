import sys
import os

# Ajuste de rutas para poder importar la librería "hermana"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

# Importamos TU librería
import native_lottie

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    
    # 1. Registramos tu componente personalizado
    native_lottie.register()

    engine = QQmlApplicationEngine()
    
    # 2. Cargamos el QML
    qml_file = os.path.join(os.path.dirname(__file__), "app.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())