import QtQuick
import org.kde.plasma.plasmoid

QtObject {
    id: root

    function _internalAction(name) {
        return Plasmoid.internalAction(name)
    }

    function _triggerInternalAction(name) {
        var action = _internalAction(name)
        if (action)
            action.trigger()
    }

    function isSupported(actionData) {
        if (!actionData)
            return false
        switch (actionData.intent) {
        case "open_url":
            return true
        case "open_settings":
            return !!_internalAction("configure")
        case "about":
            return !!actionData.target
        case "quit":
            return !!_internalAction("quit")
        default:
            return true
        }
    }

    function visibleActions(actions) {
        var source = actions || []
        return source.filter(function(actionData) {
            return actionData && actionData.visible === true && root.isSupported(actionData)
        })
    }

    function dispatch(actionData) {
        if (!actionData || actionData.enabled !== true)
            return

        switch (actionData.intent) {
        case "open_url":
            if (actionData.target)
                Qt.openUrlExternally(actionData.target)
            break
        case "open_settings":
            _triggerInternalAction("configure")
            break
        case "about":
            if (actionData.target)
                Qt.openUrlExternally(actionData.target)
            break
        case "quit":
            _triggerInternalAction("quit")
            break
        default:
            break
        }
    }
}
