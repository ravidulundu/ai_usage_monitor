import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3

Item {
    id: compactRoot

    PopupTokens {
        id: tokens
    }

    property string panelTool: Plasmoid.configuration.panelTool || "auto"
    property int displayMode: Plasmoid.configuration.panelDisplayMode || 0

    readonly property var panelIndicator: (root.popupData && root.popupData.panel)
        ? root.popupData.panel
        : ({})
    readonly property bool hasPanelProvider: !!panelIndicator.providerId

    property real activePct: {
        var percent = Number(panelIndicator.percent)
        if (isNaN(percent))
            return 0
        return Math.max(0, Math.min(100, percent))
    }

    property string activeText: {
        if (root.isLoading)
            return "..."
        return panelIndicator.displayText || "-"
    }

    property string iconSource: {
        if (!panelIndicator.iconKey)
            return ""
        return Qt.resolvedUrl("../images/" + panelIndicator.iconKey + ".svg")
    }

    function ringColor() {
        var tone = String(panelIndicator.tone || "ok")
        if (tone === "error")
            return tokens.error
        if (tone === "warn")
            return tokens.warn
        if (tone === "accent")
            return tokens.accent
        return tokens.success
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.expanded = !root.expanded
    }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: tokens.spacing.inlineGap - 1

        CompactProviderMark {
            tokens: tokens
            hasPanelProvider: compactRoot.hasPanelProvider
            iconSource: compactRoot.iconSource
            badgeText: panelIndicator.badgeText || ""
            ringColor: Qt.color(compactRoot.ringColor())
        }

        CompactProgressIndicator {
            visible: compactRoot.hasPanelProvider && displayMode < 2
            tokens: tokens
            pct: compactRoot.activePct
            toneColor: Qt.color(compactRoot.ringColor())
            displayText: compactRoot.activeText
            showText: displayMode === 0
        }

        PC3.Label {
            visible: compactRoot.hasPanelProvider && displayMode === 2
            text: compactRoot.activeText
            font.pixelSize: 12
            font.bold: true
            color: Qt.color(compactRoot.ringColor())
        }

        PC3.Label {
            visible: root.isLoading && !compactRoot.hasPanelProvider
            text: "..."
            font.pixelSize: 11
            color: tokens.mutedText
        }
    }
}
