import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami

Item {
    id: compactRoot

    property string panelTool: Plasmoid.configuration.panelTool || "claude"
    property int displayMode: Plasmoid.configuration.panelDisplayMode || 0

    function branding(provider) {
        return (provider && provider.metadata && provider.metadata.branding) ? provider.metadata.branding : {}
    }

    function iconAsset(provider) {
        var data = branding(provider)
        if (!data)
            return ""
        var assetName = data.assetName || ""
        if (assetName)
            return assetName
        if (data.iconKey)
            return data.iconKey + ".svg"
        return ""
    }

    function visibleProviders() {
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

    property var activeData: {
        var preferred = root.providerById(panelTool)
        if (preferred && preferred.enabled !== false && preferred.installed === true)
            return preferred
        var filtered = visibleProviders()
        return filtered.length > 0 ? filtered[0] : null
    }

    property real activePct: {
        if (!activeData || !activeData.primaryMetric)
            return 0
        return Math.min((activeData.primaryMetric.usedPct || 0), 100)
    }

    property string activeText: {
        if (root.isLoading) return "…"
        if (!activeData || !activeData.primaryMetric)
            return "—"
        return activeData.primaryMetric.usedPct + "%"
    }

    property string iconSource: {
        var assetName = iconAsset(activeData)
        if (!activeData || assetName === "")
            return ""
        return Qt.resolvedUrl("../images/" + assetName)
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

    function ringColor() {
        if (activeData && activeData.error)
            return "#ef4444"
        if (activeData && activeData.incident && activeData.incident.indicator && activeData.incident.indicator !== "none") {
            if (activeData.incident.indicator === "critical")
                return "#ef4444"
            if (activeData.incident.indicator === "major")
                return "#f97316"
            if (activeData.incident.indicator === "minor")
                return "#eab308"
            if (activeData.incident.indicator === "maintenance")
                return "#38bdf8"
        }
        var p = activePct
        if (p >= 90) return "#ef4444"
        if (p >= 70) return "#f97316"
        if (p >= 40) return "#eab308"
        return "#22c55e"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.expanded = !root.expanded
    }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 5

        Image {
            width: 18
            height: 18
            source: compactRoot.iconSource
            fillMode: Image.PreserveAspectFit
            smooth: true
            visible: !!activeData && activeData.installed === true && compactRoot.iconSource !== ""
        }

        Rectangle {
            width: 18
            height: 18
            radius: 9
            color: Qt.color(branding(activeData).color || compactRoot.ringColor())
            visible: !!activeData && activeData.installed === true && compactRoot.iconSource === ""

            Text {
                anchors.centerIn: parent
                text: compactRoot.providerBadgeText(activeData)
                font.pixelSize: 8
                font.bold: true
                color: "#ffffff"
            }
        }

        // ── Ring (modes 0 and 1) ─────────────────────────────────────────
        Item {
            visible: !!activeData && activeData.installed === true && displayMode < 2
            width: 34; height: 34

            Canvas {
                id: progressRing
                anchors.fill: parent

                property real pct: compactRoot.activePct
                property color color: Qt.color(compactRoot.ringColor())

                onPctChanged:   requestPaint()
                onColorChanged: requestPaint()

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    var cx = width  / 2
                    var cy = height / 2
                    var r  = cx - 3
                    var lw = 3

                    ctx.beginPath()
                    ctx.arc(cx, cy, r, 0, 2 * Math.PI)
                    ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.18)
                    ctx.lineWidth = lw
                    ctx.stroke()

                    if (pct > 0) {
                        ctx.beginPath()
                        ctx.arc(cx, cy, r,
                                -Math.PI / 2,
                                -Math.PI / 2 + 2 * Math.PI * (pct / 100))
                        ctx.strokeStyle = color
                        ctx.lineWidth = lw
                        ctx.stroke()
                    }
                }
            }

            // Text inside ring — mode 0 only
            Text {
                visible: displayMode === 0
                anchors.centerIn: parent
                text: compactRoot.activeText
                font.pixelSize: 9
                font.bold: true
                color: Qt.color(compactRoot.ringColor())
                horizontalAlignment: Text.AlignHCenter
            }
        }

        // ── Text only — mode 2 ───────────────────────────────────────────
        PC3.Label {
            visible: !!activeData && activeData.installed === true && displayMode === 2
            text: compactRoot.activeText
            font.pixelSize: 12
            font.bold: true
            color: Qt.color(compactRoot.ringColor())
        }

        // Loading fallback
        PC3.Label {
            visible: root.isLoading && (!activeData || activeData.installed !== true)
            text: "…"
            font.pixelSize: 11
            color: Kirigami.Theme.disabledTextColor
        }
    }
}
