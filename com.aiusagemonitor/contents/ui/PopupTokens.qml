import QtQuick
import org.kde.kirigami as Kirigami

QtObject {
    id: tokens

    readonly property int width: 340

    readonly property color surface: Kirigami.Theme.backgroundColor
    readonly property color raisedSurface: Kirigami.Theme.alternateBackgroundColor
    readonly property color text: Kirigami.Theme.textColor
    readonly property color mutedText: Kirigami.Theme.disabledTextColor
    readonly property color separator: Qt.rgba(text.r, text.g, text.b, 0.06)
    readonly property color accent: Kirigami.Theme.highlightColor
    readonly property color accentText: Kirigami.Theme.highlightedTextColor
    readonly property color success: Kirigami.Theme.positiveTextColor
    readonly property color warn: Kirigami.Theme.neutralTextColor
    readonly property color error: Kirigami.Theme.negativeTextColor
    readonly property color selectedTabSurface: Qt.rgba(accent.r, accent.g, accent.b, 0.16)
    readonly property color selectedTabBorder: Qt.rgba(accent.r, accent.g, accent.b, 0.34)
    readonly property color cardSurface: Qt.rgba(raisedSurface.r, raisedSurface.g, raisedSurface.b, 0.82)
    readonly property color actionHoverSurface: Qt.rgba(accent.r, accent.g, accent.b, 0.10)

    readonly property var spacing: ({
        outerPadding: 8,
        sectionGap: 5,
        rowGap: 1,
        metricInlineGap: 2,
        inlineGap: 3,
        compactSectionGap: 4,
        chipGap: 4,
        tabHorizontalPadding: 6,
        tabVerticalPadding: 3,
        tabInnerGap: 3,
        tabStackGap: 1,
        actionRowGap: 0
    })

    readonly property var radius: ({
        surface: 10,
        tabPill: 8,
        card: 8,
        chipPrimary: 7,
        chip: 6,
        actionPill: 6
    })

    readonly property var opacity: ({
        tabBadgeSurface: 0.22,
        overviewCardSurface: 0.84,
        emptyStateSurface: 0.82
    })

    readonly property int rowHeight: 21
    readonly property int dividerThickness: 1
    readonly property int progressThickness: 2
    readonly property int tabMiniLineThickness: 2
    readonly property int tabOutlineAllowance: 1
    readonly property int titleTextSize: 13
    readonly property int metaTextSize: 10
    readonly property int tabTextSize: 10
    readonly property int tabIconSize: 11
    readonly property int tabBadgeTextSize: 7
    readonly property int chipPrimaryHeight: 18
    readonly property int chipPrimaryHorizontalPadding: 12
    readonly property int chipHeight: 16
    readonly property int chipHorizontalPadding: 10
    readonly property int headerTitleTextSize: 13
    readonly property int overviewTitleTextSize: 12
    readonly property int metricDotSize: 4
    readonly property int emptyStateHeight: 72
    readonly property int emptyStateMessageWidth: 238
    readonly property int actionIconSize: 13
    readonly property int actionHorizontalPadding: 3
    readonly property int actionVerticalPadding: 1
    readonly property int contentBottomPadding: 1
    readonly property real tabMiniLineMinFillWidth: 5
}
