import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami

Item {
    id: fullRoot
    implicitWidth: 344
    implicitHeight: contentCol.implicitHeight + 16
    width: implicitWidth
    height: implicitHeight

    property string selectedProviderId: "overview"

    function branding(provider) {
        return (provider && provider.metadata && provider.metadata.branding) ? provider.metadata.branding : {}
    }

    property var visibleProviderList: {
        var items = root.providerStates || []
        var filtered = []
        for (var i = 0; i < items.length; i++) {
            if (items[i].enabled !== false && items[i].installed === true)
                filtered.push(items[i])
        }
        filtered.sort(function(a, b) {
            function rank(provider) {
                if ((provider.primaryMetric || provider.secondaryMetric) && !provider.error) return 0
                if (!provider.error) return 1
                return 2
            }
            return rank(a) - rank(b)
        })
        return filtered
    }

    property var overviewProviderList: visibleProviderList.slice(0, 3)

    onVisibleProviderListChanged: {
        if (selectedProviderId === "overview")
            return
        var stillVisible = false
        for (var i = 0; i < visibleProviderList.length; i++) {
            if (visibleProviderList[i].id === selectedProviderId) {
                stillVisible = true
                break
            }
        }
        if (!stillVisible)
            selectedProviderId = "overview"
    }

    function usageColor(pct) {
        if (pct >= 90) return "#ef4444"
        if (pct >= 70) return "#f59e0b"
        if (pct >= 40) return "#eab308"
        return "#22c55e"
    }

    function formatReset(isoStr) {
        if (!isoStr) return ""
        var now = new Date()
        var reset = new Date(isoStr)
        var diff = reset - now
        if (diff <= 0) return "soon"
        var hrs = Math.floor(diff / 3600000)
        var mins = Math.floor((diff % 3600000) / 60000)
        if (hrs >= 24) {
            var days = Math.floor(hrs / 24)
            return "in " + days + "d " + (hrs % 24) + "h"
        }
        if (hrs > 0) return "in " + hrs + "h " + mins + "m"
        return "in " + mins + "m"
    }

    function providerIcon(provider) {
        var data = branding(provider)
        if (!data)
            return ""
        var assetName = data.assetName || ""
        if (!assetName && data.iconKey)
            assetName = data.iconKey + ".svg"
        return assetName ? Qt.resolvedUrl("../images/" + assetName) : ""
    }

    function providerBadgeText(provider) {
        var badge = branding(provider).badgeText
        if (badge)
            return badge
        if (!provider || !provider.displayName)
            return "AI"
        var words = provider.displayName.split(/\s+/).filter(function(word) { return word.length > 0 })
        if (words.length >= 2)
            return (words[0][0] + words[1][0]).toUpperCase()
        return provider.displayName.slice(0, 2).toUpperCase()
    }

    function providerSubtitle(provider) {
        var extras = provider && provider.extras ? provider.extras : {}
        var parts = []
        if (provider && provider.source)
            parts.push(String(provider.source).toUpperCase())
        if (extras.model && extras.model !== "local-cli")
            parts.push(extras.model)
        if (extras.plan && !(provider && provider.source === "cli" && (extras.plan === "api" || extras.plan === "oauth")))
            parts.push(extras.plan)
        return parts.join(" · ")
    }

    function formatLocalUsage(localUsage) {
        if (!localUsage)
            return ""
        var parts = []
        if (localUsage.sessionTokens !== null && localUsage.sessionTokens !== undefined)
            parts.push("session " + localUsage.sessionTokens + " tok")
        if (localUsage.last30DaysTokens !== null && localUsage.last30DaysTokens !== undefined)
            parts.push("30d " + localUsage.last30DaysTokens + " tok")
        return parts.join(" · ")
    }

    function selectedProvider() {
        for (var i = 0; i < visibleProviderList.length; i++) {
            if (visibleProviderList[i].id === selectedProviderId)
                return visibleProviderList[i]
        }
        return null
    }

    Rectangle {
        anchors.fill: parent
        radius: 16
        color: Qt.rgba(0.07, 0.08, 0.11, 0.97)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.08)
    }

    Rectangle {
        anchors.fill: parent
        radius: 16
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0.24, 0.34, 0.94, 0.08) }
            GradientStop { position: 0.45; color: Qt.rgba(0.03, 0.03, 0.04, 0.0) }
            GradientStop { position: 1.0; color: Qt.rgba(0.98, 0.72, 0.16, 0.05) }
        }
    }

    ColumnLayout {
        id: contentCol
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: 10
        }
        spacing: 8

        RowLayout {
            Layout.fillWidth: true

            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true

                PC3.Label {
                    text: "AI Usage Monitor"
                    font.bold: true
                    font.pixelSize: 14
                }

                PC3.Label {
                    text: root.lastUpdated ? ("Updated " + root.lastUpdated) : "Shared backend state"
                    color: Kirigami.Theme.disabledTextColor
                    font.pixelSize: 10
                }
            }

            PC3.ToolButton {
                icon.name: "view-refresh"
                enabled: !root.isLoading
                onClicked: root.refresh()
                PC3.ToolTip.text: "Refresh"
                PC3.ToolTip.visible: hovered
                PC3.ToolTip.delay: 250
            }
        }

        Loader {
            Layout.fillWidth: true
            active: visibleProviderList.length > 0
            sourceComponent: Flickable {
                Layout.fillWidth: true
                contentWidth: switcherRow.implicitWidth
                contentHeight: switcherRow.implicitHeight
                clip: true
                interactive: contentWidth > width
                boundsBehavior: Flickable.StopAtBounds

                RowLayout {
                    id: switcherRow
                    spacing: 6

                    Repeater {
                        model: ["overview"].concat(fullRoot.visibleProviderList.map(function(provider) { return provider.id }))

                        delegate: QQC2.Button {
                            required property var modelData
                            readonly property string providerId: modelData
                            readonly property var provider: providerId === "overview" ? null : fullRoot.visibleProviderList.find(function(item) { return item.id === providerId })
                            text: providerId === "overview" ? "Overview" : (provider ? provider.displayName : providerId)
                            highlighted: fullRoot.selectedProviderId === providerId
                            onClicked: fullRoot.selectedProviderId = providerId
                            flat: !highlighted
                        }
                    }
                }
            }
        }

        Loader {
            Layout.fillWidth: true
            active: visibleProviderList.length > 0 && selectedProviderId === "overview"
            sourceComponent: ColumnLayout {
                spacing: 6

                Repeater {
                    model: fullRoot.overviewProviderList

                    delegate: ProviderRow {
                        provider: modelData
                        compact: true
                    }
                }
            }
        }

        Loader {
            Layout.fillWidth: true
            active: visibleProviderList.length > 0 && selectedProviderId !== "overview" && !!selectedProvider()
            sourceComponent: ProviderRow {
                provider: fullRoot.selectedProvider()
                compact: false
            }
        }

        Loader {
            Layout.fillWidth: true
            active: visibleProviderList.length === 0
            sourceComponent: Rectangle {
                radius: 12
                color: Qt.rgba(1, 1, 1, 0.03)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.06)
                implicitHeight: 78

                PC3.Label {
                    anchors.centerIn: parent
                    text: {
                        if (root.isLoading) return "Loading…"
                        if (root.lastError) return root.lastError
                        return (root.providerStates && root.providerStates.length > 0)
                            ? "All tools hidden in shared config"
                            : "No AI tools detected"
                    }
                    color: Kirigami.Theme.disabledTextColor
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    width: 250
                }
            }
        }
    }

    component ProviderHeader: RowLayout {
        property var provider: null
        Layout.fillWidth: true
        spacing: 8

        Image {
            width: 18
            height: 18
            source: fullRoot.providerIcon(provider)
            fillMode: Image.PreserveAspectFit
            smooth: true
            visible: source !== ""
        }

        Rectangle {
            width: 18
            height: 18
            radius: 9
            color: fullRoot.branding(provider).color || "#64748b"
            visible: fullRoot.providerIcon(provider) === ""

            Text {
                anchors.centerIn: parent
                text: fullRoot.providerBadgeText(provider)
                font.pixelSize: 8
                font.bold: true
                color: "#ffffff"
            }
        }

        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true

            PC3.Label {
                text: provider ? provider.displayName : ""
                font.bold: true
                font.pixelSize: 12
            }

            PC3.Label {
                visible: fullRoot.providerSubtitle(provider) !== ""
                text: fullRoot.providerSubtitle(provider)
                color: Kirigami.Theme.disabledTextColor
                font.pixelSize: 10
            }
        }
    }

    component ProviderRow: Rectangle {
        id: providerRow
        property var provider: null
        property bool compact: false
        readonly property var extras: provider && provider.extras ? provider.extras : ({})
        radius: 14
        color: Qt.rgba(1, 1, 1, 0.04)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.07)
        Layout.fillWidth: true
        implicitHeight: rowContent.implicitHeight + 14

        ColumnLayout {
            id: rowContent
            anchors.fill: parent
            anchors.margins: 8
            spacing: 6

            ProviderHeader { provider: providerRow.provider }

            PC3.Label {
                visible: !!(provider && provider.error)
                text: provider ? provider.error : ""
                color: "#ff7b7b"
                font.pixelSize: 10
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            Loader {
                Layout.fillWidth: true
                active: !!(provider && provider.primaryMetric) && !(provider && provider.error)
                sourceComponent: UsageRow {
                    metric: providerRow.provider.primaryMetric
                    compact: providerRow.compact
                }
            }

            Loader {
                Layout.fillWidth: true
                active: !!(provider && provider.secondaryMetric) && !(provider && provider.error)
                sourceComponent: UsageRow {
                    metric: providerRow.provider.secondaryMetric
                    compact: providerRow.compact
                }
            }

            Repeater {
                model: (!(provider && provider.error) && !compact && extras.buckets) ? extras.buckets : []

                delegate: UsageRow {
                    metric: {
                        "label": modelData.model || "Model",
                        "usedPct": modelData.used_pct || 0,
                        "resetAt": modelData.reset_time || ""
                    }
                    compact: true
                }
            }

            PC3.Label {
                visible: !!(provider && provider.localUsage)
                    && fullRoot.formatLocalUsage(provider.localUsage) !== ""
                    && (!compact || !(provider && (provider.primaryMetric || provider.secondaryMetric)))
                text: fullRoot.formatLocalUsage(provider.localUsage)
                color: Kirigami.Theme.disabledTextColor
                font.pixelSize: 10
                Layout.fillWidth: true
            }
        }
    }

    component UsageRow: ColumnLayout {
        property var metric: null
        property bool compact: false
        spacing: 3
        Layout.fillWidth: true

        RowLayout {
            Layout.fillWidth: true

            PC3.Label {
                text: metric ? metric.label : ""
                font.pixelSize: 10
                color: Kirigami.Theme.disabledTextColor
            }

            Item { Layout.fillWidth: true }

            PC3.Label {
                text: metric ? (Math.round(metric.usedPct || 0) + "%") : ""
                font.pixelSize: compact ? 10 : 11
                font.bold: true
                color: fullRoot.usageColor(metric ? metric.usedPct || 0 : 0)
            }

            PC3.Label {
                text: metric ? fullRoot.formatReset(metric.resetAt) : ""
                font.pixelSize: 10
                color: Kirigami.Theme.disabledTextColor
                visible: text !== ""
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: compact ? 5 : 7
            radius: height / 2
            color: Qt.rgba(1, 1, 1, 0.08)

            Rectangle {
                width: parent.width * (Math.min(metric ? metric.usedPct || 0 : 0, 100) / 100)
                height: parent.height
                radius: parent.radius
                color: fullRoot.usageColor(metric ? metric.usedPct || 0 : 0)

                Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
            }
        }
    }
}
