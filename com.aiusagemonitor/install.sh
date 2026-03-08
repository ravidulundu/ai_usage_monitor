#!/bin/bash
# Install the AI Usage Monitor plasmoid into KDE Plasma.
# Run this from the com.aiusagemonitor directory or its parent.

WIDGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIDGET_ID="com.aiusagemonitor"
ICON_NAME="com.aiusagemonitor"
ICON_SRC="$WIDGET_DIR/contents/images/screeps-svgrepo-com.svg"
ICON_DEST_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_DEST="$ICON_DEST_DIR/$ICON_NAME.svg"
LEGACY_ICON_DEST="$HOME/.local/share/icons/hicolor/256x256/apps/$ICON_NAME.png"
SHARED_CORE_DIR="$HOME/.local/share/ai-usage-monitor"
REPO_ROOT="$(cd "$WIDGET_DIR/.." && pwd)"

echo "Installing $WIDGET_ID from $WIDGET_DIR..."

mkdir -p "$SHARED_CORE_DIR"
rm -rf "$SHARED_CORE_DIR/core"
cp -r "$REPO_ROOT/core" "$SHARED_CORE_DIR/core"

# Remove any previous installation
kpackagetool6 --type Plasma/Applet --remove "$WIDGET_ID" 2>/dev/null || true

# Install fresh
if kpackagetool6 --type Plasma/Applet --install "$WIDGET_DIR"; then
    # Install the project icon so Widget Explorer uses the intended SVG.
    if [ -f "$ICON_SRC" ]; then
        mkdir -p "$ICON_DEST_DIR"
        cp -f "$ICON_SRC" "$ICON_DEST"
        rm -f "$LEGACY_ICON_DEST"
        # Refresh icon/services cache if the tool exists.
        if command -v kbuildsycoca6 >/dev/null 2>&1; then
            kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
        fi
    fi

    echo ""
    echo "Installed successfully!"
    echo ""
    echo "To add to your panel:"
    echo "  Right-click the panel → Add Widgets → search 'AI Usage Monitor'"
    echo ""
    echo "To preview in a window:"
    echo "  plasmawindowed $WIDGET_ID"
else
    echo "Installation failed. Check the output above."
    exit 1
fi
