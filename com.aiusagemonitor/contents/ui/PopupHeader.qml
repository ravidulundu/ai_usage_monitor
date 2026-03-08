import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    PopupTokens { id: tokens }

    property var provider: null
    readonly property var sourcePresentation: (root.provider && root.provider.sourcePresentation)
        ? root.provider.sourcePresentation
        : ({})
    readonly property var statusPresentation: (root.provider && root.provider.statusPresentation)
        ? root.provider.statusPresentation
        : ({})
    readonly property string sourceModeLabel: sourcePresentation.modeLabel || ""
    readonly property string activeSourceLabel: sourcePresentation.activeSourceLabel || ""
    readonly property var sourceStatusTags: sourcePresentation.statusTags || []
    readonly property string sourceReasonText: sourcePresentation.reasonText || ""
    readonly property bool providerStatusVisible: statusPresentation.visible === true
    readonly property string providerStatusBadge: statusPresentation.badgeLabel || ""
    readonly property string providerStatusDetails: statusPresentation.details || ""
    readonly property string providerStatusTone: statusPresentation.tone || "warn"

    Layout.fillWidth: true
    spacing: tokens.spacing.rowGap

    PopupHeaderTitleRow {
        provider: root.provider
        tokens: tokens
    }

    PopupHeaderSourceRow {
        tokens: tokens
        sourceModeLabel: root.sourceModeLabel
        activeSourceLabel: root.activeSourceLabel
        sourceStatusTags: root.sourceStatusTags
    }

    PC3.Label {
        text: (root.provider && root.provider.subtitle) ? root.provider.subtitle : ""
        visible: text !== ""
        color: tokens.mutedText
        font.pixelSize: tokens.metaTextSize
        elide: Text.ElideRight
        Layout.fillWidth: true
    }

    PC3.Label {
        text: root.sourceReasonText !== ""
            ? root.sourceReasonText
            : ((root.provider && root.provider.sourceDetails) ? root.provider.sourceDetails : "")
        visible: text !== ""
        color: tokens.mutedText
        font.pixelSize: tokens.metaTextSize - 1
        elide: Text.ElideRight
        Layout.fillWidth: true
    }

    PopupHeaderStatusRow {
        tokens: tokens
        providerStatusVisible: root.providerStatusVisible
        providerStatusBadge: root.providerStatusBadge
        providerStatusDetails: root.providerStatusDetails
        providerStatusTone: root.providerStatusTone
    }

    PC3.Label {
        Layout.fillWidth: true
        text: (root.provider && root.provider.errorState && root.provider.errorState.hasError && root.provider.errorState.message)
            ? root.provider.errorState.message
            : ""
        visible: text !== ""
        wrapMode: Text.Wrap
        color: tokens.error
        font.pixelSize: tokens.metaTextSize - 1
    }
}
