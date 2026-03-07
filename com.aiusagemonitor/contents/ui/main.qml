import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

PlasmoidItem {
    id: root

    // Parsed data from shared Python backend
    property var providerStates: []
    property bool isLoading: true
    property string lastError: ""
    property string lastUpdated: ""

    readonly property int refreshInterval: (Plasmoid.configuration.refreshSecs || 60) * 1000

    function providerById(providerId) {
        if (!providerStates || providerStates.length === 0)
            return null
        for (var i = 0; i < providerStates.length; i++) {
            if (providerStates[i].id === providerId)
                return providerStates[i]
        }
        return null
    }

    // Path to the Python script (resolved relative to this QML file)
    readonly property string scriptPath: {
        var url = Qt.resolvedUrl("../scripts/fetch_all_usage.py").toString()
        return url.replace(/^file:\/\//, "")
    }

    // In windowed/planar mode, show the full view by default.
    // In panel mode, keep compact view.
    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation
    compactRepresentation: CompactRepresentation { }
    fullRepresentation: FullRepresentation { }

    // Tell the panel exactly how much space this widget needs
    Layout.fillWidth: false
    Layout.minimumWidth: 66
    Layout.preferredWidth: 66
    Layout.maximumWidth: 66

    // Executable data source — runs the Python script
    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            root.isLoading = false
            var stdout = (data["stdout"] || "").trim()
            var stderr = (data["stderr"] || "").trim()
            if (stdout === "") {
                root.lastError = stderr || "No output from script"
                return
            }
            try {
                var result = JSON.parse(stdout)
                root.providerStates = result.providers || []
                root.lastError = ""
                var now = new Date()
                root.lastUpdated = now.getHours().toString().padStart(2, "0") + ":" +
                                   now.getMinutes().toString().padStart(2, "0") + ":" +
                                   now.getSeconds().toString().padStart(2, "0")
            } catch (e) {
                root.lastError = "Parse error: " + e.message
            }
        }
    }

    function refresh() {
        if (scriptPath === "") return
        root.isLoading = true
        // The executable data engine passes arguments directly; quoting the path makes
        // Python treat the quotes as literal filename characters.
        runner.connectSource("python3 " + scriptPath)
    }

    // Auto-refresh timer
    Timer {
        id: refreshTimer
        interval: root.refreshInterval
        running: true
        repeat: true
        onTriggered: root.refresh()
    }

    // Update timer when config changes
    onRefreshIntervalChanged: {
        refreshTimer.interval = root.refreshInterval
        refreshTimer.restart()
    }

    // Initial load
    Component.onCompleted: root.refresh()

    onExpandedChanged: {
        if (expanded)
            root.refresh()
    }
}
