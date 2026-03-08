import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    property var configRoot
    property var descriptor: ({})
    property var providerState: ({})
    property var liveState: null

    readonly property string capabilitiesText: configRoot.providerCapabilitiesText(descriptor, liveState)
    readonly property string strategyText: configRoot.providerStrategyText(providerState, liveState)
    readonly property string availabilityText: configRoot.providerAvailabilityText(descriptor, providerState, liveState)
    readonly property string sourceReasonText: configRoot.providerSourceReason(providerState, liveState)
    readonly property var sourceOptions: configRoot._sourceOptionItems(descriptor)

    spacing: 6

    Kirigami.Separator {
        Layout.fillWidth: true
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 10
        rowSpacing: 4

        QQC2.Label {
            visible: root.sourceReasonText !== ""
            text: "Why this source"
            color: Kirigami.Theme.disabledTextColor
            Layout.preferredWidth: configRoot.formLabelWidth
        }

        QQC2.Label {
            Layout.fillWidth: true
            text: root.sourceReasonText
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            wrapMode: Text.Wrap
            visible: text !== ""
        }

        QQC2.Label {
            text: "Capabilities"
            color: Kirigami.Theme.disabledTextColor
            Layout.preferredWidth: configRoot.formLabelWidth
        }

        QQC2.Label {
            Layout.fillWidth: true
            text: root.capabilitiesText
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            wrapMode: Text.Wrap
        }

        QQC2.Label {
            text: "Source strategy"
            color: Kirigami.Theme.disabledTextColor
            Layout.preferredWidth: configRoot.formLabelWidth
        }

        QQC2.Label {
            Layout.fillWidth: true
            text: root.strategyText
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            wrapMode: Text.Wrap
        }

        QQC2.Label {
            text: "Availability"
            color: Kirigami.Theme.disabledTextColor
            Layout.preferredWidth: configRoot.formLabelWidth
        }

        QQC2.Label {
            Layout.fillWidth: true
            text: root.availabilityText
            color: Kirigami.Theme.disabledTextColor
            font.pixelSize: 10
            wrapMode: Text.Wrap
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 10
        rowSpacing: 5
        visible: root.sourceOptions.length > 0

        QQC2.Label {
            text: "Source"
            color: Kirigami.Theme.disabledTextColor
            Layout.preferredWidth: configRoot.formLabelWidth
        }

        QQC2.ComboBox {
            Layout.fillWidth: true
            model: root.sourceOptions
            textRole: "label"
            currentIndex: {
                var current = providerState.source || configRoot._defaultPreferredSource(descriptor)
                for (var i = 0; i < model.length; i++) {
                    if (model[i].value === current)
                        return i
                }
                return 0
            }
            onActivated: {
                if (model[currentIndex] !== undefined)
                    configRoot.setProviderField(descriptor.id, "source", model[currentIndex].value)
            }
        }
    }

    Repeater {
        model: descriptor.configFields || []

        delegate: GridLayout {
            required property var modelData
            readonly property var field: modelData
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 10
            rowSpacing: 5

            QQC2.Label {
                text: field.label
                color: Kirigami.Theme.disabledTextColor
                font.pixelSize: 10
                wrapMode: Text.Wrap
                Layout.preferredWidth: configRoot.formLabelWidth
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
                            var current = providerState[field.key]
                                || (field.options && field.options.length > 0 ? field.options[0] : "")
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
