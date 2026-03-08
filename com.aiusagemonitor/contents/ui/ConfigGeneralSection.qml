import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

QQC2.GroupBox {
    id: root

    property var configRoot

    title: "General"
    Layout.fillWidth: true

    ColumnLayout {
        anchors.fill: parent
        spacing: configRoot.sectionInnerSpacing

        QQC2.Label {
            Layout.fillWidth: true
            text: "Panel behavior, refresh cycle and indicator style."
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.Wrap
            font.pixelSize: 10
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 10
            rowSpacing: 6

            QQC2.Label {
                text: "Refresh every"
                color: Kirigami.Theme.disabledTextColor
                Layout.preferredWidth: configRoot.formLabelWidth
            }

            QQC2.ComboBox {
                Layout.fillWidth: true
                model: [
                    { text: "20 seconds",  value: 20  },
                    { text: "1 minute",    value: 60  },
                    { text: "2 minutes",   value: 120 },
                    { text: "5 minutes",   value: 300 },
                    { text: "10 minutes",  value: 600 },
                    { text: "30 minutes",  value: 1800 },
                ]
                textRole: "text"
                currentIndex: {
                    var v = configRoot.cfg_refreshSecs
                    for (var i = 0; i < model.length; i++) {
                        if (model[i].value === v)
                            return i
                    }
                    return 1
                }
                onActivated: configRoot.cfg_refreshSecs = model[currentIndex].value
            }

            QQC2.Label {
                text: "Panel tool"
                color: Kirigami.Theme.disabledTextColor
                Layout.preferredWidth: configRoot.formLabelWidth
            }

            QQC2.ComboBox {
                Layout.fillWidth: true
                textRole: "shortName"
                model: configRoot.providerForPanelModel()
                currentIndex: {
                    for (var i = 0; i < model.length; i++) {
                        if (model[i].id === configRoot.cfg_panelTool)
                            return i
                    }
                    return 0
                }
                onActivated: {
                    if (model[currentIndex] && model[currentIndex].id)
                        configRoot.cfg_panelTool = model[currentIndex].id
                }
            }

            QQC2.Label {
                text: "Display style"
                color: Kirigami.Theme.disabledTextColor
                Layout.preferredWidth: configRoot.formLabelWidth
                Layout.alignment: Qt.AlignTop
            }

            Item {
                Layout.fillWidth: true
                implicitHeight: displayStyleFlow.implicitHeight

                Flow {
                    id: displayStyleFlow
                    width: parent.width
                    spacing: 8

                    QQC2.RadioButton {
                        text: "Ring and percentage"
                        checked: configRoot.cfg_panelDisplayMode === 0
                        onToggled: if (checked) configRoot.cfg_panelDisplayMode = 0
                    }

                    QQC2.RadioButton {
                        text: "Ring only"
                        checked: configRoot.cfg_panelDisplayMode === 1
                        onToggled: if (checked) configRoot.cfg_panelDisplayMode = 1
                    }

                    QQC2.RadioButton {
                        text: "Percentage only"
                        checked: configRoot.cfg_panelDisplayMode === 2
                        onToggled: if (checked) configRoot.cfg_panelDisplayMode = 2
                    }
                }
            }
        }
    }
}
