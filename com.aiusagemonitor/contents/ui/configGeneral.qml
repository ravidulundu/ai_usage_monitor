import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as P5Support

QQC2.ScrollView {
    id: configRoot
    clip: true

    property int cfg_refreshSecs: 60
    property string cfg_panelTool: "claude"
    property int cfg_panelDisplayMode: 0
    property int cfg_refreshSecsDefault: 60
    property string cfg_panelToolDefault: "claude"
    property int cfg_panelDisplayModeDefault: 0
    property var cfg_expanding
    property var cfg_length
    property string title: ""

    property var descriptors: []
    property var sharedProviders: []
    property var stateProviders: []
    property string sharedConfigError: ""
    property string expandedProviderId: ""

    readonly property string scriptPath: {
        var url = Qt.resolvedUrl("../scripts/fetch_all_usage.py").toString()
        return url.replace(/^file:\/\//, "")
    }

    function shellQuote(value) {
        return "'" + String(value).replace(/'/g, "'\"'\"'") + "'"
    }

    function loadSharedConfig() {
        configRunner.connectSource("python3 " + shellQuote(scriptPath) + " config-ui")
    }

    function setProviderField(providerId, field, value) {
        var encoded = value
        if (value === "" || value === null || value === undefined)
            encoded = "__null__"
        configRunner.connectSource(
            "python3 " + shellQuote(scriptPath)
            + " config-set-provider "
            + shellQuote(providerId) + " "
            + shellQuote(field) + " "
            + shellQuote(encoded)
        )
    }

    function providerForPanelModel() {
        return descriptors.length > 0 ? descriptors : [
            { id: "claude", displayName: "Claude Code", shortName: "Claude" },
            { id: "codex", displayName: "OpenAI Codex", shortName: "Codex" },
            { id: "gemini", displayName: "Gemini CLI", shortName: "Gemini" },
        ]
    }

    function providerLiveState(providerId) {
        for (var i = 0; i < stateProviders.length; i++) {
            if (stateProviders[i].id === providerId)
                return stateProviders[i]
        }
        return null
    }

    function providerIcon(descriptor) {
        var branding = descriptor && descriptor.branding ? descriptor.branding : {}
        var assetName = branding.assetName || ""
        if (!assetName && branding.iconKey)
            assetName = branding.iconKey + ".svg"
        return assetName ? Qt.resolvedUrl("../images/" + assetName) : ""
    }

    P5Support.DataSource {
        id: configRunner
        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
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
                if (payload.config && payload.config.providers)
                    configRoot.sharedProviders = payload.config.providers
                if (payload.state && payload.state.providers)
                    configRoot.stateProviders = payload.state.providers
                if (payload.ok && payload.config && payload.config.providers)
                    configRoot.sharedProviders = payload.config.providers
                configRoot.sharedConfigError = ""
            } catch (e) {
                configRoot.sharedConfigError = "Parse error: " + e.message
            }
        }
    }

    Component.onCompleted: loadSharedConfig()

    Item {
        width: Math.max(configRoot.availableWidth, configRoot.width)
        implicitHeight: pageColumn.implicitHeight + 24

        ColumnLayout {
            id: pageColumn
            width: Math.min(parent.width - 24, 760)
            anchors.top: parent.top
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 14

            QQC2.GroupBox {
                title: "General"
                Layout.fillWidth: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true

                        QQC2.Label {
                            text: "Refresh every"
                            color: Kirigami.Theme.disabledTextColor
                        }

                        Item { Layout.fillWidth: true }

                        QQC2.ComboBox {
                            id: refreshCombo
                            model: [
                                { text: "20 seconds",  value: 20  },
                                { text: "1 minute",    value: 60  },
                                { text: "2 minutes",   value: 120 },
                                { text: "5 minutes",   value: 300 },
                                { text: "10 minutes",  value: 600 },
                                { text: "30 minutes",  value: 1800 },
                            ]
                            textRole: "text"
                            currentIndex: {
                                var v = cfg_refreshSecs
                                for (var i = 0; i < model.length; i++) {
                                    if (model[i].value === v) return i
                                }
                                return 1
                            }
                            onActivated: cfg_refreshSecs = model[currentIndex].value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        QQC2.Label {
                            text: "Panel tool"
                            color: Kirigami.Theme.disabledTextColor
                        }

                        Item { Layout.fillWidth: true }

                        QQC2.ComboBox {
                            textRole: "shortName"
                            model: providerForPanelModel()
                            currentIndex: {
                                for (var i = 0; i < model.length; i++) {
                                    if (model[i].id === cfg_panelTool)
                                        return i
                                }
                                return 0
                            }
                            onActivated: {
                                if (model[currentIndex] && model[currentIndex].id)
                                    cfg_panelTool = model[currentIndex].id
                            }
                        }
                    }

                    ColumnLayout {
                        spacing: 6

                        QQC2.Label {
                            text: "Display style"
                            color: Kirigami.Theme.disabledTextColor
                        }

                        QQC2.RadioButton {
                            text: "Ring and percentage"
                            checked: cfg_panelDisplayMode === 0
                            onToggled: if (checked) cfg_panelDisplayMode = 0
                        }
                        QQC2.RadioButton {
                            text: "Ring only"
                            checked: cfg_panelDisplayMode === 1
                            onToggled: if (checked) cfg_panelDisplayMode = 1
                        }
                        QQC2.RadioButton {
                            text: "Percentage only"
                            checked: cfg_panelDisplayMode === 2
                            onToggled: if (checked) cfg_panelDisplayMode = 2
                        }
                    }
                }
            }

            QQC2.GroupBox {
                title: "Shared Provider Config"
                Layout.fillWidth: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10

                    QQC2.Label {
                        visible: configRoot.sharedConfigError !== ""
                        text: configRoot.sharedConfigError
                        color: Kirigami.Theme.negativeTextColor
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }

                    QQC2.Button {
                        text: "Reload shared config"
                        onClicked: configRoot.loadSharedConfig()
                    }

                    Repeater {
                        model: configRoot.descriptors

                        delegate: Rectangle {
                            required property var modelData
                            readonly property var descriptor: modelData
                            readonly property var providerState: {
                                for (var i = 0; i < configRoot.sharedProviders.length; i++) {
                                    if (configRoot.sharedProviders[i].id === descriptor.id)
                                        return configRoot.sharedProviders[i]
                                }
                                return { id: descriptor.id, enabled: descriptor.defaultEnabled, source: descriptor.sourceModes[0] }
                            }
                            readonly property var liveState: configRoot.providerLiveState(descriptor.id)
                            readonly property var branding: descriptor.branding || ({})

                            radius: 14
                            color: Qt.rgba(1, 1, 1, 0.03)
                            border.width: 1
                            border.color: Qt.rgba(1, 1, 1, 0.08)
                            Layout.fillWidth: true
                            implicitHeight: providerColumn.implicitHeight + 18

                            ColumnLayout {
                                id: providerColumn
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Item {
                                        Layout.preferredWidth: 24
                                        Layout.minimumWidth: 24
                                        Layout.maximumWidth: 24
                                        Layout.preferredHeight: 24
                                        Layout.alignment: Qt.AlignTop

                                        Image {
                                            anchors.centerIn: parent
                                            width: 20
                                            height: 20
                                            source: configRoot.providerIcon(descriptor)
                                            fillMode: Image.PreserveAspectFit
                                            smooth: true
                                            visible: source !== ""
                                        }

                                        Rectangle {
                                            anchors.centerIn: parent
                                            width: 20
                                            height: 20
                                            radius: 10
                                            color: branding.color || "#64748b"
                                            visible: !configRoot.providerIcon(descriptor)

                                            Text {
                                                anchors.centerIn: parent
                                                text: branding.badgeText || "AI"
                                                font.pixelSize: 8
                                                font.bold: true
                                                color: "#ffffff"
                                            }
                                        }
                                    }

                                    ColumnLayout {
                                        spacing: 0
                                        Layout.fillWidth: true
                                        Layout.alignment: Qt.AlignVCenter

                                        QQC2.Label {
                                            text: descriptor.shortName || descriptor.displayName
                                            font.bold: true
                                        }

                                        QQC2.Label {
                                            text: {
                                                var baseName = descriptor.displayName || descriptor.id
                                                if (!liveState)
                                                    return baseName
                                                if (liveState.installed === false)
                                                    return baseName + " · not detected"
                                                if (liveState.error)
                                                    return baseName + " · error"
                                                if (liveState.primaryMetric)
                                                    return baseName + " · " + Math.round(liveState.primaryMetric.usedPct || 0) + "%"
                                                return baseName
                                            }
                                            color: Kirigami.Theme.disabledTextColor
                                            font.pixelSize: 10
                                            wrapMode: Text.Wrap
                                        }
                                    }

                                    QQC2.Button {
                                        text: configRoot.expandedProviderId === descriptor.id ? "Hide" : "Configure"
                                        Layout.alignment: Qt.AlignVCenter
                                        onClicked: {
                                            configRoot.expandedProviderId =
                                                configRoot.expandedProviderId === descriptor.id ? "" : descriptor.id
                                        }
                                    }

                                    QQC2.CheckBox {
                                        text: "Enabled"
                                        Layout.alignment: Qt.AlignVCenter
                                        checked: providerState.enabled !== false
                                        onToggled: configRoot.setProviderField(descriptor.id, "enabled", checked ? "true" : "false")
                                    }
                                }

                                Loader {
                                    active: configRoot.expandedProviderId === descriptor.id
                                    Layout.fillWidth: true

                                    sourceComponent: ColumnLayout {
                                        spacing: 8

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            QQC2.Label {
                                                text: "Source"
                                                color: Kirigami.Theme.disabledTextColor
                                                visible: descriptor.sourceModes && descriptor.sourceModes.length > 0
                                            }

                                            QQC2.ComboBox {
                                                visible: descriptor.sourceModes && descriptor.sourceModes.length > 0
                                                Layout.fillWidth: true
                                                model: descriptor.sourceModes || []
                                                currentIndex: {
                                                    var current = providerState.source || (descriptor.sourceModes && descriptor.sourceModes.length > 0 ? descriptor.sourceModes[0] : "")
                                                    for (var i = 0; i < model.length; i++) {
                                                        if (model[i] === current)
                                                            return i
                                                    }
                                                    return 0
                                                }
                                                onActivated: {
                                                    if (model[currentIndex] !== undefined)
                                                        configRoot.setProviderField(descriptor.id, "source", model[currentIndex])
                                                }
                                            }
                                        }

                                        Repeater {
                                            model: descriptor.configFields || []

                                            delegate: RowLayout {
                                                required property var modelData
                                                readonly property var field: modelData
                                                Layout.fillWidth: true
                                                spacing: 8

                                                QQC2.Label {
                                                    text: field.label
                                                    color: Kirigami.Theme.disabledTextColor
                                                    Layout.preferredWidth: 120
                                                    wrapMode: Text.Wrap
                                                }

                                                Loader {
                                                    Layout.fillWidth: true
                                                    sourceComponent: field.kind === "choice" ? choiceField : textField

                                                    Component {
                                                        id: textField

                                                        QQC2.TextField {
                                                            Layout.fillWidth: true
                                                            placeholderText: field.placeholder || field.label
                                                            echoMode: field.secret ? TextInput.Password : TextInput.Normal
                                                            text: providerState[field.key] || ""
                                                            onEditingFinished: configRoot.setProviderField(descriptor.id, field.key, text)
                                                        }
                                                    }

                                                    Component {
                                                        id: choiceField

                                                        QQC2.ComboBox {
                                                            Layout.fillWidth: true
                                                            model: field.options || []
                                                            currentIndex: {
                                                                var current = providerState[field.key] || (field.options && field.options.length > 0 ? field.options[0] : "")
                                                                for (var i = 0; i < model.length; i++) {
                                                                    if (model[i] === current)
                                                                        return i
                                                                }
                                                                return 0
                                                            }
                                                            onActivated: {
                                                                if (model[currentIndex] !== undefined)
                                                                    configRoot.setProviderField(descriptor.id, field.key, model[currentIndex])
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
