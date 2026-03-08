import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PC3

Item {
    id: root

    PopupTokens {
        id: tokens
    }

    property var tabsModel: []
    property string selectedTabId: ""
    signal tabSelected(string tabId)

    implicitHeight: Math.max(
        tokens.rowHeight + tokens.tabOutlineAllowance,
        tabsRow.implicitHeight + tokens.tabOutlineAllowance
    )

    function withAlpha(color, alpha) {
        return Qt.rgba(color.r, color.g, color.b, alpha)
    }

    function tabIcon(tab) {
        if (!tab || !tab.iconKey)
            return ""
        return Qt.resolvedUrl("../images/" + tab.iconKey + ".svg")
    }

    function tabAccent(_tab) {
        return tokens.accent
    }

    Flickable {
        id: tabsFlick
        anchors.fill: parent
        contentWidth: tabsRow.implicitWidth
        contentHeight: tabsRow.implicitHeight
        clip: true
        interactive: contentWidth > width
        boundsBehavior: Flickable.StopAtBounds

        RowLayout {
            id: tabsRow
            spacing: tokens.spacing.inlineGap

            Repeater {
                model: root.tabsModel || []

                delegate: QQC2.AbstractButton {
                    required property var modelData
                    readonly property var tab: modelData
                    readonly property bool selected: root.selectedTabId === tab.id
                    readonly property bool tabEnabled: tab && tab.enabled !== false
                    readonly property var miniMetric: tab && tab.miniMetric ? tab.miniMetric : ({})
                    readonly property string mode: miniMetric.mode || "none"
                    readonly property real pct: (miniMetric.percent === null || miniMetric.percent === undefined)
                        ? 0
                        : Math.max(0, Math.min(100, Number(miniMetric.percent)))

                    enabled: tabEnabled
                    onClicked: {
                        if (tabEnabled)
                            root.tabSelected(tab.id)
                    }
                    implicitHeight: Math.max(
                        tokens.rowHeight,
                        tabContent.implicitHeight + topPadding + bottomPadding
                    )
                    leftPadding: tokens.spacing.tabHorizontalPadding
                    rightPadding: tokens.spacing.tabHorizontalPadding
                    topPadding: tokens.spacing.tabVerticalPadding
                    bottomPadding: tokens.spacing.tabVerticalPadding

                    contentItem: ColumnLayout {
                        id: tabContent
                        spacing: tokens.spacing.tabStackGap

                        RowLayout {
                            spacing: tokens.spacing.tabInnerGap
                            Layout.alignment: Qt.AlignHCenter

                            Image {
                                id: tabIconImage
                                width: tokens.tabIconSize
                                height: tokens.tabIconSize
                                source: root.tabIcon(tab)
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                visible: source !== ""
                            }

                            Rectangle {
                                width: tokens.tabIconSize
                                height: tokens.tabIconSize
                                radius: width / 2
                                color: root.withAlpha(root.tabAccent(tab), tokens.opacity.tabBadgeSurface)
                                visible: tabIconImage.source === "" && !!tab.badgeText

                                Text {
                                    anchors.centerIn: parent
                                    text: tab.badgeText
                                    font.pixelSize: tokens.tabBadgeTextSize
                                    font.bold: true
                                    color: tokens.accentText
                                }
                            }

                            PC3.Label {
                                text: tab.shortTitle
                                font.pixelSize: tokens.tabTextSize
                                font.bold: selected && tabEnabled
                                color: selected && tabEnabled
                                    ? tokens.text
                                    : tokens.mutedText
                                opacity: tabEnabled ? (selected ? 1.0 : 0.92) : 0.68
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: tokens.tabMiniLineThickness
                            radius: height / 2
                            color: tokens.separator

                            Rectangle {
                                width: {
                                    if (!tabEnabled)
                                        return 0
                                    if (mode === "percent")
                                        return Math.max(tokens.tabMiniLineMinFillWidth, parent.width * (pct / 100))
                                    if (mode === "tick")
                                        return tokens.tabMiniLineMinFillWidth
                                    return selected ? parent.width : 0
                                }
                                height: parent.height
                                radius: parent.radius
                                color: selected && tabEnabled
                                    ? tokens.accent
                                    : (tabEnabled ? root.tabAccent(tab) : tokens.mutedText)
                            }
                        }
                    }

                    background: Rectangle {
                        radius: tokens.radius.tabPill
                        color: selected && tabEnabled
                            ? tokens.selectedTabSurface
                            : "transparent"
                        border.width: selected && tabEnabled ? 1 : 0
                        border.color: selected && tabEnabled ? tokens.selectedTabBorder : "transparent"
                    }
                }
            }
        }
    }
}
