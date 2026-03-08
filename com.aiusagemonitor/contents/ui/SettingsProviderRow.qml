import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: rowRoot

    property var providerDescriptor: ({})
    property var providerConfig: ({})
    property var providerLiveState: null
    property string subtitleText: ""
    property string preferredSourceLabel: ""
    property string sourceModeLabel: ""
    property string activeSourceLabel: ""
    property string sourceStatusLabel: ""
    property string fallbackLabel: ""
    property var statusTags: []
    property string sourceReasonText: ""
    property string capabilitiesText: ""
    property string strategyText: ""
    property string availabilityText: ""
    property string iconSource: ""
    property color fallbackBadgeColor: Kirigami.Theme.highlightColor
    property string fallbackBadgeText: "AI"
    property bool expanded: false
    property Component expandedContent: null

    signal toggleExpandedRequested()
    signal enabledChanged(bool enabled)

    readonly property string statusSummaryText: {
        if (rowRoot.sourceStatusLabel !== "") {
            if (rowRoot.fallbackLabel !== "")
                return rowRoot.sourceStatusLabel + " · " + rowRoot.fallbackLabel
            return rowRoot.sourceStatusLabel
        }

        var tags = rowRoot.statusTags || []
        if (tags && tags.length > 0)
            return tags.join(" · ")
        return rowRoot.fallbackLabel || ""
    }

    radius: 8
    color: Qt.rgba(
        Kirigami.Theme.alternateBackgroundColor.r,
        Kirigami.Theme.alternateBackgroundColor.g,
        Kirigami.Theme.alternateBackgroundColor.b,
        rowHover.hovered || expanded ? 0.24 : 0.16
    )
    border.width: 1
    border.color: expanded
        ? Qt.rgba(
            Kirigami.Theme.highlightColor.r,
            Kirigami.Theme.highlightColor.g,
            Kirigami.Theme.highlightColor.b,
            0.30
        )
        : Qt.rgba(
            Kirigami.Theme.textColor.r,
            Kirigami.Theme.textColor.g,
            Kirigami.Theme.textColor.b,
            0.10
        )
    Layout.fillWidth: true
    implicitHeight: contentCol.implicitHeight + 10

    HoverHandler {
        id: rowHover
    }

    ColumnLayout {
        id: contentCol
        anchors.fill: parent
        anchors.margins: 6
        spacing: 6

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 10
            rowSpacing: 4

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Item {
                    Layout.preferredWidth: 20
                    Layout.minimumWidth: 20
                    Layout.maximumWidth: 20
                    Layout.preferredHeight: 20
                    Layout.alignment: Qt.AlignVCenter

                    Image {
                        anchors.centerIn: parent
                        width: 16
                        height: 16
                        source: rowRoot.iconSource
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        visible: source !== ""
                    }

                    Rectangle {
                        anchors.centerIn: parent
                        width: 16
                        height: 16
                        radius: 8
                        color: rowRoot.fallbackBadgeColor
                        visible: !rowRoot.iconSource

                        Text {
                            anchors.centerIn: parent
                            text: rowRoot.fallbackBadgeText
                            font.pixelSize: 6
                            font.bold: true
                            color: Kirigami.Theme.highlightedTextColor
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 2

                    RowLayout {
                        Layout.fillWidth: true

                        QQC2.Label {
                            text: rowRoot.providerDescriptor.displayName || rowRoot.providerDescriptor.shortName || ""
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            visible: rowRoot.sourceModeLabel !== ""
                            radius: 7
                            implicitHeight: 18
                            implicitWidth: sourceModeText.implicitWidth + 12
                            color: Qt.rgba(
                                Kirigami.Theme.highlightColor.r,
                                Kirigami.Theme.highlightColor.g,
                                Kirigami.Theme.highlightColor.b,
                                0.18
                            )
                            border.width: 1
                            border.color: Qt.rgba(
                                Kirigami.Theme.highlightColor.r,
                                Kirigami.Theme.highlightColor.g,
                                Kirigami.Theme.highlightColor.b,
                                0.35
                            )

                            QQC2.Label {
                                id: sourceModeText
                                anchors.centerIn: parent
                                text: rowRoot.sourceModeLabel
                                color: Kirigami.Theme.textColor
                                font.pixelSize: 9
                                font.bold: true
                            }
                        }
                    }

                    QQC2.Label {
                        text: rowRoot.subtitleText
                        color: Kirigami.Theme.disabledTextColor
                        font.pixelSize: 10
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 4

                        Rectangle {
                            visible: rowRoot.preferredSourceLabel !== ""
                            radius: 6
                            implicitHeight: 16
                            implicitWidth: preferredSourceText.implicitWidth + 10
                            color: Qt.rgba(
                                Kirigami.Theme.alternateBackgroundColor.r,
                                Kirigami.Theme.alternateBackgroundColor.g,
                                Kirigami.Theme.alternateBackgroundColor.b,
                                0.30
                            )
                            border.width: 1
                            border.color: Qt.rgba(
                                Kirigami.Theme.textColor.r,
                                Kirigami.Theme.textColor.g,
                                Kirigami.Theme.textColor.b,
                                0.16
                            )

                            QQC2.Label {
                                id: preferredSourceText
                                anchors.centerIn: parent
                                text: rowRoot.preferredSourceLabel
                                color: Kirigami.Theme.disabledTextColor
                                font.pixelSize: 9
                            }
                        }

                        Rectangle {
                            visible: rowRoot.activeSourceLabel !== ""
                            radius: 6
                            implicitHeight: 16
                            implicitWidth: activeSourceText.implicitWidth + 10
                            color: Qt.rgba(
                                Kirigami.Theme.alternateBackgroundColor.r,
                                Kirigami.Theme.alternateBackgroundColor.g,
                                Kirigami.Theme.alternateBackgroundColor.b,
                                0.30
                            )
                            border.width: 1
                            border.color: Qt.rgba(
                                Kirigami.Theme.textColor.r,
                                Kirigami.Theme.textColor.g,
                                Kirigami.Theme.textColor.b,
                                0.16
                            )

                            QQC2.Label {
                                id: activeSourceText
                                anchors.centerIn: parent
                                text: rowRoot.activeSourceLabel
                                color: Kirigami.Theme.disabledTextColor
                                font.pixelSize: 9
                            }
                        }

                    }

                    QQC2.Label {
                        Layout.fillWidth: true
                        visible: rowRoot.statusSummaryText !== ""
                        text: rowRoot.statusSummaryText
                        color: Kirigami.Theme.disabledTextColor
                        font.pixelSize: 9
                        elide: Text.ElideRight
                    }

                    QQC2.Label {
                        Layout.fillWidth: true
                        visible: rowRoot.sourceReasonText !== ""
                        text: rowRoot.sourceReasonText
                        color: Kirigami.Theme.disabledTextColor
                        font.pixelSize: 9
                        elide: Text.ElideRight
                    }
                }
            }

            QQC2.Button {
                text: rowRoot.expanded ? "Hide" : "Configure"
                Layout.preferredWidth: 96
                Layout.minimumWidth: 96
                Layout.maximumWidth: 96
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                onClicked: rowRoot.toggleExpandedRequested()
            }

            RowLayout {
                spacing: 6
                Layout.preferredWidth: 86
                Layout.minimumWidth: 86
                Layout.maximumWidth: 86
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight

                QQC2.Switch {
                    checked: rowRoot.providerConfig.enabled !== false
                    onToggled: rowRoot.enabledChanged(checked)
                }

                QQC2.Label {
                    text: rowRoot.providerConfig.enabled !== false ? "On" : "Off"
                    color: Kirigami.Theme.disabledTextColor
                    font.pixelSize: 10
                }
            }
        }

        Loader {
            Layout.fillWidth: true
            active: rowRoot.expanded && rowRoot.expandedContent !== null
            sourceComponent: rowRoot.expandedContent
        }
    }
}
