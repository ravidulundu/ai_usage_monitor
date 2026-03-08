import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

QQC2.GroupBox {
    id: root

    property var configRoot

    title: "Overview"
    Layout.fillWidth: true

    ColumnLayout {
        anchors.fill: parent
        spacing: configRoot.sectionInnerSpacing

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: "Overview tab providers"
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            QQC2.Label {
                text: "Max 3 · Selected " + configRoot.selectedOverviewIds().length + "/3"
                color: Kirigami.Theme.disabledTextColor
                font.pixelSize: 10
            }
        }

        QQC2.Label {
            visible: configRoot.descriptors.length === 0
            text: "Loading providers..."
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
        }

        Rectangle {
            Layout.fillWidth: true
            radius: 6
            color: Qt.rgba(
                Kirigami.Theme.alternateBackgroundColor.r,
                Kirigami.Theme.alternateBackgroundColor.g,
                Kirigami.Theme.alternateBackgroundColor.b,
                0.14
            )
            border.width: 1
            border.color: Qt.rgba(
                Kirigami.Theme.textColor.r,
                Kirigami.Theme.textColor.g,
                Kirigami.Theme.textColor.b,
                0.08
            )
            implicitHeight: overviewGrid.implicitHeight + 12

            GridLayout {
                id: overviewGrid
                anchors.fill: parent
                anchors.margins: 6
                columns: width > 620 ? 3 : 2
                columnSpacing: 8
                rowSpacing: 4

                Repeater {
                    model: configRoot.descriptors

                    delegate: Item {
                        required property var modelData
                        readonly property string providerId: modelData.id
                        readonly property var liveState: configRoot.providerLiveState(providerId)
                        readonly property var savedState: configRoot.sharedProviderState(providerId)
                        readonly property bool detected: liveState ? liveState.installed !== false : false
                        readonly property bool providerEnabled: savedState.enabled !== false
                        readonly property string statusText: !providerEnabled
                            ? "disabled"
                            : (!detected ? "not detected" : "")
                        readonly property string labelText: modelData.shortName || modelData.displayName || providerId

                        Layout.fillWidth: true
                        Layout.preferredWidth: Math.max(150, (overviewGrid.width - (overviewGrid.columnSpacing * (overviewGrid.columns - 1))) / overviewGrid.columns)
                        implicitHeight: rowLayout.implicitHeight

                        RowLayout {
                            id: rowLayout
                            anchors.fill: parent
                            spacing: 4

                            QQC2.CheckBox {
                                id: overviewCheck
                                text: ""
                                checked: configRoot.isOverviewSelected(providerId)
                                enabled: checked || configRoot.selectedOverviewIds().length < 3
                                onToggled: configRoot.toggleOverviewProvider(providerId, checked)
                            }

                            QQC2.Label {
                                text: labelText
                                color: overviewCheck.enabled ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            QQC2.Label {
                                visible: statusText !== ""
                                text: statusText
                                color: Kirigami.Theme.disabledTextColor
                                font.pixelSize: 9
                            }
                        }
                    }
                }
            }
        }

        QQC2.Label {
            Layout.fillWidth: true
            text: "Overview selection only affects overview cards in the overview tab. It is separate from normal enabled provider tabs."
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            visible: configRoot.descriptors.length > 0
        }
    }
}
