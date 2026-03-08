import QtQuick

Item {
    id: root

    property var tokens: null
    property bool hasPanelProvider: false
    property string iconSource: ""
    property string badgeText: ""
    property color ringColor: "transparent"

    width: 18
    height: 18
    visible: hasPanelProvider

    Image {
        width: 18
        height: 18
        source: root.iconSource
        fillMode: Image.PreserveAspectFit
        smooth: true
        visible: root.iconSource !== ""
    }

    Rectangle {
        width: 18
        height: 18
        radius: 9
        color: root.ringColor
        visible: root.iconSource === ""

        Text {
            anchors.centerIn: parent
            text: root.badgeText
            font.pixelSize: 8
            font.bold: true
            color: root.tokens ? root.tokens.accentText : "#ffffff"
        }
    }
}
