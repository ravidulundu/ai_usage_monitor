import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as P5Support

import "ConfigBackend.js" as ConfigBackend
import "ConfigPresentation.js" as ConfigPresentation

QQC2.ScrollView {
    id: configRoot
    clip: true

    property int cfg_refreshSecs: 60
    property string cfg_panelTool: "auto"
    property int cfg_panelDisplayMode: 0
    property int cfg_refreshSecsDefault: 60
    property string cfg_panelToolDefault: "auto"
    property int cfg_panelDisplayModeDefault: 0
    property string cfg_sharedConfigPayload: "{}"
    property var cfg_expanding
    property var cfg_length
    property string title: ""

    property var descriptors: []
    property var sharedProviders: []
    property var stateProviders: []
    property var stagedConfig: ({ "version": 1, "refreshInterval": 60, "overviewProviderIds": [], "providers": [] })
    property string sharedConfigError: ""
    property string expandedProviderId: ""
    property bool stateFetchInFlight: false
    readonly property int formLabelWidth: 134
    readonly property int sectionInnerSpacing: 6

    readonly property string scriptPath: Qt.resolvedUrl("../scripts/fetch_all_usage.py").toString().replace(/^file:\/\//, "")

    function loadSharedConfig() { stateProviders = []; loadSharedConfigMeta() }
    function disconnectPendingCommands() {
        var sources = configRunner.connectedSources || []
        for (var i = 0; i < sources.length; i++) {
            if (String(sources[i] || "").indexOf("config-ui-state") !== -1)
                stateFetchInFlight = false
            configRunner.disconnectSource(sources[i])
        }
    }
    function runBackendCommand(command) {
        if (stateFetchInFlight && String(command || "").indexOf("config-ui-state") === -1)
            stateFetchInFlight = false
        disconnectPendingCommands(); configRunner.connectSource(command)
    }
    function loadSharedConfigMeta() { runBackendCommand("python3 " + ConfigBackend.shellQuote(scriptPath) + " config-ui") }
    function loadSharedState() {
        if (stateFetchInFlight)
            return
        stateFetchInFlight = true
        runBackendCommand("python3 " + ConfigBackend.shellQuote(scriptPath) + " config-ui-state")
    }
    function syncStagedPayload() { cfg_sharedConfigPayload = JSON.stringify(stagedConfig) }
    function setProviderField(providerId, field, value) {
        stagedConfig = ConfigBackend.setProviderField(stagedConfig, providerId, field, value)
        sharedProviders = stagedConfig.providers || []
        syncStagedPayload(); saveConfig()
    }
    function selectedOverviewIds() { return ConfigBackend.selectedOverviewIds(stagedConfig) }
    function isOverviewSelected(providerId) { return ConfigBackend.isOverviewSelected(stagedConfig, providerId) }
    function toggleOverviewProvider(providerId, enabled) {
        stagedConfig = ConfigBackend.toggleOverviewProvider(stagedConfig, providerId, enabled, 3)
        syncStagedPayload(); saveConfig()
    }
    function saveConfig() {
        runBackendCommand("python3 " + ConfigBackend.shellQuote(scriptPath) + " config-save-json " + ConfigBackend.shellQuote(cfg_sharedConfigPayload))
    }

    function providerForPanelModel() { return ConfigBackend.providerForPanelModel(descriptors) }
    function providerLiveState(providerId) { return ConfigBackend.providerLiveState(stateProviders, providerId) }
    function providerIcon(descriptor) { return ConfigBackend.providerIcon(descriptor) }
    function sharedProviderState(providerId) {
        return ConfigBackend.sharedProviderState(sharedProviders, descriptors, providerId, _defaultPreferredSource)
    }

    function _sourceOptionItems(descriptor) { return ConfigPresentation.sourceOptionItems(descriptor) }
    function _defaultPreferredSource(descriptor) { return ConfigPresentation.defaultPreferredSource(descriptor) }
    function providerRowSubtitle(descriptor, providerState, liveState) { return ConfigPresentation.providerRowSubtitle(descriptor, providerState, liveState) }
    function providerCapabilitiesText(descriptor, liveState) { return ConfigPresentation.providerCapabilitiesText(descriptor, liveState) }
    function providerStrategyText(providerState, liveState) { return ConfigPresentation.providerStrategyText(providerState, liveState) }
    function providerAvailabilityText(descriptor, providerState, liveState) { return ConfigPresentation.providerAvailabilityText(descriptor, providerState, liveState) }
    function providerSourceModeLabel(descriptor, providerState, liveState) { return ConfigPresentation.providerSourceModeLabel(descriptor, providerState, liveState) }
    function providerActiveSourceLabel(providerState, liveState) { return ConfigPresentation.providerActiveSourceLabel(providerState, liveState) }
    function providerPreferredSourceLabel(providerState, liveState) { return ConfigPresentation.providerPreferredSourceLabel(providerState, liveState) }
    function providerSourceStatusLabel(descriptor, providerState, liveState) { return ConfigPresentation.providerSourceStatusLabel(descriptor, providerState, liveState) }
    function providerFallbackLabel(providerState, liveState) { return ConfigPresentation.providerFallbackLabel(providerState, liveState) }
    function providerStatusTags(descriptor, providerState, liveState) { return ConfigPresentation.providerStatusTags(descriptor, providerState, liveState) }
    function providerSourceReason(providerState, liveState) { return ConfigPresentation.providerSourceReason(providerState, liveState) }

    P5Support.DataSource {
        id: configRunner
        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            if (sourceName.indexOf("config-ui-state") !== -1)
                configRoot.stateFetchInFlight = false
            var stdout = (data["stdout"] || "").trim()
            var stderr = (data["stderr"] || "").trim()
            if (stdout === "") {
                configRoot.sharedConfigError = stderr || "No output from backend"
                return
            }
            try {
                var payload = JSON.parse(stdout)
                if (payload.descriptors)
                    configRoot.descriptors = payload.descriptors
                var synced = ConfigBackend.syncConfigFromPayload(payload, configRoot.stagedConfig)
                configRoot.stagedConfig = synced.stagedConfig
                configRoot.sharedProviders = synced.sharedProviders
                configRoot.syncStagedPayload()
                if (payload.state && payload.state.providers)
                    configRoot.stateProviders = payload.state.providers
                if (payload.descriptors || payload.config)
                    configRoot.loadSharedState()
                configRoot.sharedConfigError = ""
            } catch (e) {
                configRoot.sharedConfigError = "Parse error: " + e.message
            }
        }
    }

    Component.onCompleted: loadSharedConfig()
    Component.onDestruction: { stateFetchInFlight = false; disconnectPendingCommands() }

    Item {
        width: Math.max(configRoot.availableWidth, configRoot.width)
        implicitHeight: pageColumn.implicitHeight + 14

        ColumnLayout {
            id: pageColumn
            width: Math.min(parent.width - 20, 720)
            anchors.top: parent.top
            anchors.topMargin: 8
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8

            Kirigami.Heading {
                level: 2
                text: "AI Usage Monitor Settings"
                Layout.fillWidth: true
            }

            QQC2.Label {
                Layout.fillWidth: true
                text: "General behavior and panel display are configured above. Provider-specific shared settings are listed below."
                color: Kirigami.Theme.disabledTextColor
                wrapMode: Text.Wrap
                font.pixelSize: 11
            }

            ConfigGeneralSection { configRoot: configRoot }
            ConfigOverviewSection { configRoot: configRoot }
            ConfigProvidersSection { configRoot: configRoot }
            ConfigFooterActions { configRoot: configRoot }
        }
    }
}
