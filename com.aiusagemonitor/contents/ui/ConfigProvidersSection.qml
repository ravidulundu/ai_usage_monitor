import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

QQC2.GroupBox {
    id: root

    property var configRoot

    title: "Providers"
    Layout.fillWidth: true

    function providerStateForDescriptor(descriptor) {
        for (var i = 0; i < configRoot.sharedProviders.length; i++) {
            if (configRoot.sharedProviders[i].id === descriptor.id)
                return configRoot.sharedProviders[i]
        }
        return {
            id: descriptor.id,
            enabled: descriptor.defaultEnabled,
            source: configRoot._defaultPreferredSource(descriptor)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: configRoot.sectionInnerSpacing

        QQC2.Label {
            Layout.fillWidth: true
            text: "Manage provider enable state and source strategy. Enabled providers always appear as top popup tabs."
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.Wrap
            font.pixelSize: 10
        }

        QQC2.Label {
            visible: configRoot.sharedConfigError !== ""
            text: configRoot.sharedConfigError
            color: Kirigami.Theme.negativeTextColor
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }

        Repeater {
            model: configRoot.descriptors

            delegate: SettingsProviderRow {
                required property var modelData
                readonly property var descriptor: modelData
                readonly property var providerState: root.providerStateForDescriptor(descriptor)
                readonly property var liveState: configRoot.providerLiveState(descriptor.id)
                readonly property var branding: descriptor.branding || ({})

                providerDescriptor: descriptor
                providerConfig: providerState
                providerLiveState: liveState
                subtitleText: configRoot.providerRowSubtitle(descriptor, providerState, liveState)
                preferredSourceLabel: configRoot.providerPreferredSourceLabel(providerState, liveState)
                sourceModeLabel: configRoot.providerSourceModeLabel(descriptor, providerState, liveState)
                activeSourceLabel: configRoot.providerActiveSourceLabel(providerState, liveState)
                sourceStatusLabel: configRoot.providerSourceStatusLabel(descriptor, providerState, liveState)
                fallbackLabel: configRoot.providerFallbackLabel(providerState, liveState)
                statusTags: configRoot.providerStatusTags(descriptor, providerState, liveState)
                sourceReasonText: configRoot.providerSourceReason(providerState, liveState)
                capabilitiesText: configRoot.providerCapabilitiesText(descriptor, liveState)
                strategyText: configRoot.providerStrategyText(providerState, liveState)
                availabilityText: configRoot.providerAvailabilityText(descriptor, providerState, liveState)
                iconSource: configRoot.providerIcon(descriptor)
                fallbackBadgeColor: branding.color || Kirigami.Theme.highlightColor
                fallbackBadgeText: branding.badgeText || "AI"
                expanded: configRoot.expandedProviderId === descriptor.id

                onToggleExpandedRequested: {
                    configRoot.expandedProviderId = expanded ? "" : descriptor.id
                }

                onEnabledChanged: function(enabled) {
                    configRoot.setProviderField(descriptor.id, "enabled", enabled)
                    if (enabled) {
                        configRoot.expandedProviderId = descriptor.id
                        return
                    }
                    if (configRoot.expandedProviderId === descriptor.id)
                        configRoot.expandedProviderId = ""
                }

                expandedContent: ConfigProviderExpandedContent {
                    configRoot: root.configRoot
                    descriptor: descriptor
                    providerState: providerState
                    liveState: liveState
                }
            }
        }
    }
}
