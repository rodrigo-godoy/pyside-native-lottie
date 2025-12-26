import QtQuick
import QtQuick.Window
import NativeLottie 1.0 

Window {
    width: 400
    height: 300
    visible: true
    flags: Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"

    Rectangle {
        anchors.fill: parent
        radius: 20
        color: "teal" 
        layer.enabled: true
        
        Column {
            anchors.centerIn: parent
            spacing: 20

            // Tu componente Lottie
            Lottie {
                id: myLottie
                width: 150
                height: 150
                anchors.horizontalCenter: parent.horizontalCenter
                
                source: "animation.json"
                loop: false // Se detiene al final
                
                // Cuando termina, activamos el "Latido"
                onFinished: {
                    console.log("Animación terminada. Iniciando latido...");
                    heartbeat.start();
                }
            }

            // --- EFECTO DE LATIDO (Breathing) ---
            SequentialAnimation {
                id: heartbeat
                loops: Animation.Infinite // Repetir por siempre
                running: false // Empieza apagado

                // Inhalar (Crece y brilla un poco)
                ParallelAnimation {
                    NumberAnimation { target: myLottie; property: "scale"; to: 1.05; duration: 1500; easing.type: Easing.InOutQuad }
                    NumberAnimation { target: myLottie; property: "opacity"; to: 0.9; duration: 1500 }
                }

                // Exhalar (Vuelve a tamaño normal)
                ParallelAnimation {
                    NumberAnimation { target: myLottie; property: "scale"; to: 1.0; duration: 1500; easing.type: Easing.InOutQuad }
                    NumberAnimation { target: myLottie; property: "opacity"; to: 1.0; duration: 1500 }
                }
            }

            Text {
                text: "Cargas REMASEP"
                font.pixelSize: 24
                font.bold: true
                color: "white"
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }
}