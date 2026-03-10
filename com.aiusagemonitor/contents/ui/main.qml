import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

import "ConfigBackend.js" as ConfigBackend

PlasmoidItem {
    id: root

    property var popupData: ({
        "selectedProviderId": "",
        "providerOrder": [],
        "hasOverview": false,
        "tabs": [],
        "providers": [],
        "overviewCards": []
    })

    property bool isLoading: true
    property string lastError: ""
    property string lastUpdated: ""
    property bool identityRefreshPending: false
    property var lastRenderedIdentityByProvider: ({})
    property var identityMismatchByProvider: ({})
    property string activeRunnerCommand: ""
    property string activeConfigSaveCommand: ""
    property string lastAppliedSharedConfigPayload: ""
    property string sharedConfigPayload: Plasmoid.configuration.sharedConfigPayload || "{}"
    property string runtimeSelectedProviderId: ""

    readonly property var popupTabs: popupData && popupData.tabs ? popupData.tabs : []
    readonly property var popupProviders: popupData && popupData.providers ? popupData.providers : []
    readonly property string popupSelectedProviderId: popupData && popupData.selectedProviderId
        ? popupData.selectedProviderId
        : ""

    readonly property int refreshInterval: (Plasmoid.configuration.refreshSecs || 60) * 1000

    function popupProviderById(providerId) {
        if (!popupProviders || popupProviders.length === 0)
            return null
        for (var i = 0; i < popupProviders.length; i++) {
            if (popupProviders[i].id === providerId)
                return popupProviders[i]
        }
        return null
    }

    function parseClockFromIso(isoString) {
        if (!isoString)
            return ""
        var parsed = new Date(isoString)
        if (isNaN(parsed.getTime()))
            return ""
        return parsed.getHours().toString().padStart(2, "0") + ":"
            + parsed.getMinutes().toString().padStart(2, "0") + ":"
            + parsed.getSeconds().toString().padStart(2, "0")
    }

    function providerIdentityFingerprint(providerObj) {
        if (!providerObj)
            return ""
        if (providerObj.identityFingerprint)
            return providerObj.identityFingerprint
        if (providerObj.identity && providerObj.identity.fingerprint)
            return providerObj.identity.fingerprint
        return ""
    }

    function buildIdentityMismatchMap(providersList) {
        var mismatches = ({})
        var snapshot = providersList || []
        for (var i = 0; i < snapshot.length; i++) {
            var providerObj = snapshot[i]
            if (!providerObj || !providerObj.id)
                continue
            var providerId = providerObj.id
            var nextFp = providerIdentityFingerprint(providerObj)
            var prevFp = lastRenderedIdentityByProvider[providerId] || ""
            var changed = prevFp !== "" && nextFp !== "" && prevFp !== nextFp
            mismatches[providerId] = changed
            if (nextFp !== "")
                lastRenderedIdentityByProvider[providerId] = nextFp
        }
        return mismatches
    }

    function pruneIdentityCaches(providersList) {
        var keep = ({})
        var snapshot = providersList || []
        for (var i = 0; i < snapshot.length; i++) {
            var providerObj = snapshot[i]
            if (providerObj && providerObj.id)
                keep[providerObj.id] = true
        }

        for (var providerId in lastRenderedIdentityByProvider) {
            if (!keep[providerId])
                delete lastRenderedIdentityByProvider[providerId]
        }
        for (providerId in identityMismatchByProvider) {
            if (!keep[providerId])
                delete identityMismatchByProvider[providerId]
        }
    }

    readonly property string scriptPath: {
        var url = Qt.resolvedUrl("../scripts/fetch_all_usage.py").toString()
        return url.replace(/^file:\/\//, "")
    }

    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation
    compactRepresentation: CompactRepresentation { }
    fullRepresentation: FullRepresentation {
        onProviderSelected: function(providerId) {
            if (!providerId || providerId === "overview")
                return
            if (root.runtimeSelectedProviderId === providerId)
                return
            root.runtimeSelectedProviderId = providerId
            root.refresh(true)
        }
    }

    Layout.fillWidth: false
    Layout.minimumWidth: 66
    Layout.preferredWidth: 66
    Layout.maximumWidth: 66

    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            if (sourceName === root.activeRunnerCommand)
                root.activeRunnerCommand = ""
            root.isLoading = false
            var stdout = (data["stdout"] || "").trim()
            var stderr = (data["stderr"] || "").trim()
            if (stdout === "") {
                root.popupData = ({})
                root.identityMismatchByProvider = ({})
                root.lastRenderedIdentityByProvider = ({})
                root.identityRefreshPending = false
                identityRefreshTimer.stop()
                root.lastError = stderr || "No output from script"
                return
            }
            try {
                var result = JSON.parse(stdout)

                if (result.popup) {
                    var providersSnapshot = result.popup.providers || []
                    if (root.runtimeSelectedProviderId) {
                        var hasRuntimeProvider = false
                        for (var idx = 0; idx < providersSnapshot.length; idx++) {
                            if (providersSnapshot[idx] && providersSnapshot[idx].id === root.runtimeSelectedProviderId) {
                                hasRuntimeProvider = true
                                break
                            }
                        }
                        if (!hasRuntimeProvider)
                            root.runtimeSelectedProviderId = ""
                    }
                    root.pruneIdentityCaches(providersSnapshot)
                    root.identityMismatchByProvider = root.buildIdentityMismatchMap(providersSnapshot)
                    root.popupData = result.popup
                    root.identityRefreshPending = result.popup.identityRefreshPending === true
                    root.lastError = ""
                    root.lastUpdated = root.parseClockFromIso(result.generatedAt)
                    var mismatchDetected = false
                    for (var providerId in root.identityMismatchByProvider) {
                        if (root.identityMismatchByProvider[providerId] === true) {
                            mismatchDetected = true
                            break
                        }
                    }
                    if ((root.identityRefreshPending || mismatchDetected) && !identityRefreshTimer.running)
                        identityRefreshTimer.start()
                    return
                }

                root.identityRefreshPending = false
                identityRefreshTimer.stop()
                root.popupData = ({})
                root.identityMismatchByProvider = ({})
                root.lastRenderedIdentityByProvider = ({})
                root.lastError = "Unsupported payload: popup-vm expected"
            } catch (e) {
                root.identityRefreshPending = false
                identityRefreshTimer.stop()
                root.popupData = ({})
                root.identityMismatchByProvider = ({})
                root.lastRenderedIdentityByProvider = ({})
                root.lastError = "Parse error: " + e.message
            }
        }
    }

    function disconnectRunnerSources() {
        var sources = runner.connectedSources || []
        for (var i = 0; i < sources.length; i++)
            runner.disconnectSource(sources[i])
        activeRunnerCommand = ""
    }

    function refresh(forceRefresh) {
        if (scriptPath === "")
            return
        root.isLoading = true
        disconnectRunnerSources()
        var preferredProviderId = root.runtimeSelectedProviderId || (Plasmoid.configuration.panelTool || "")
        if (preferredProviderId === "auto" || preferredProviderId === "overview")
            preferredProviderId = ""
        var command = "python3 " + ConfigBackend.shellQuote(scriptPath) + " popup-vm"
        if (preferredProviderId !== "")
            command += " " + ConfigBackend.shellQuote(preferredProviderId)
        if (forceRefresh === true)
            command += " --force"
        runner.connectSource(command)
        activeRunnerCommand = command
    }

    function applySharedConfigPayload(payload) {
        var raw = String(payload || "").trim()
        if (raw === "" || raw === lastAppliedSharedConfigPayload)
            return

        try {
            JSON.parse(raw)
        } catch (e) {
            root.lastError = "Invalid shared config payload: " + e.message
            return
        }

        var command = "python3 " + ConfigBackend.shellQuote(scriptPath)
            + " config-save-json " + ConfigBackend.shellQuote(raw)
        configSaveRunner.connectSource(command)
        activeConfigSaveCommand = command
    }

    Timer {
        id: refreshTimer
        interval: root.refreshInterval
        running: true
        repeat: true
        onTriggered: root.refresh(false)
    }

    Timer {
        id: identityRefreshTimer
        interval: 300
        running: false
        repeat: false
        onTriggered: root.refresh(true)
    }

    P5Support.DataSource {
        id: configSaveRunner
        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            if (sourceName === root.activeConfigSaveCommand)
                root.activeConfigSaveCommand = ""

            var stdout = (data["stdout"] || "").trim()
            var stderr = (data["stderr"] || "").trim()
            if (stdout === "") {
                root.lastError = stderr || "Shared config save failed"
                return
            }

            try {
                var payload = JSON.parse(stdout)
                if (payload && payload.ok === true) {
                    root.lastAppliedSharedConfigPayload = root.sharedConfigPayload
                    root.refresh(true)
                    return
                }
                root.lastError = stderr || "Shared config save returned invalid payload"
            } catch (e) {
                root.lastError = "Shared config save parse error: " + e.message
            }
        }
    }

    onSharedConfigPayloadChanged: applySharedConfigPayload(sharedConfigPayload)

    onRefreshIntervalChanged: {
        refreshTimer.interval = root.refreshInterval
        refreshTimer.restart()
    }

    Component.onCompleted: root.refresh(true)
    Component.onDestruction: {
        refreshTimer.stop()
        identityRefreshTimer.stop()
        root.disconnectRunnerSources()
        var configSources = configSaveRunner.connectedSources || []
        for (var i = 0; i < configSources.length; i++)
            configSaveRunner.disconnectSource(configSources[i])
        activeConfigSaveCommand = ""
        root.popupData = ({})
        root.lastRenderedIdentityByProvider = ({})
        root.identityMismatchByProvider = ({})
        root.identityRefreshPending = false
    }

    onExpandedChanged: {
        if (expanded)
            root.refresh(true)
        else
            identityRefreshTimer.stop()
    }
}
