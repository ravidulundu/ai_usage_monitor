import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

QQC2.GroupBox {
    id: root

    property var configRoot

    title: "Footer actions"
    Layout.fillWidth: true

    RowLayout {
        anchors.fill: parent
        spacing: 6

        QQC2.Label {
            Layout.fillWidth: true
            text: "Maintenance actions for settings and provider descriptors."
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            wrapMode: Text.Wrap
        }

        QQC2.Button {
            text: "Reload"
            onClicked: configRoot.loadSharedConfig()
        }

        QQC2.Button {
            text: "Collapse all"
            enabled: configRoot.expandedProviderId !== ""
            onClicked: configRoot.expandedProviderId = ""
        }
    }
}
