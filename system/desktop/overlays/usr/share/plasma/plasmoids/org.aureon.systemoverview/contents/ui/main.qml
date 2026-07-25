import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    property var overview: ({})
    property string statusText: i18n("Loading…")
    property bool loading: true

    toolTipMainText: i18n("Aureon System Overview")
    toolTipSubText: statusText
    preferredRepresentation: compactRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.DefaultBackground | PlasmaCore.Types.ConfigurableBackground

    function value(name) {
        return overview[name] || i18n("Unavailable")
    }

    compactRepresentation: PlasmaComponents.ToolButton {
        icon.name: "computer-symbolic"
        text: i18n("Aureon System Overview")
        display: PlasmaComponents.AbstractButton.IconOnly
        Accessible.name: text
        onClicked: root.expanded = !root.expanded
    }

    fullRepresentation: Item {
        implicitWidth: Kirigami.Units.gridUnit * 22
        implicitHeight: Math.min(Kirigami.Units.gridUnit * 28, Screen.height * 0.8)

        PlasmaComponents.ScrollView {
            anchors.fill: parent
            contentWidth: availableWidth

            ColumnLayout {
                width: parent.width
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Heading {
                    text: i18n("Aureon System Overview")
                    level: 1
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                PlasmaComponents.BusyIndicator {
                    running: root.loading
                    visible: running
                    Layout.alignment: Qt.AlignHCenter
                }

                Kirigami.Heading { text: i18n("System"); level: 2 }
                InfoRow { label: i18n("Name"); value: root.value("system_name") }
                InfoRow { label: i18n("Version"); value: root.value("system_version") }
                InfoRow { label: i18n("Kernel"); value: root.value("kernel_version") }
                InfoRow { label: i18n("Architecture"); value: root.value("architecture") }

                Kirigami.Separator { Layout.fillWidth: true }
                Kirigami.Heading { text: i18n("Resources"); level: 2 }
                InfoRow { label: i18n("Logical CPUs"); value: root.value("logical_cpus") }
                InfoRow { label: i18n("Memory"); value: root.value("memory_total") }
                InfoRow { label: i18n("Storage"); value: root.value("storage_total") }
                InfoRow { label: i18n("Available"); value: root.value("storage_available") }
                InfoRow { label: i18n("Uptime"); value: root.value("uptime") }

                Kirigami.Separator { Layout.fillWidth: true }
                Kirigami.Heading { text: i18n("Status"); level: 2 }
                InfoRow { label: i18n("Overall"); value: root.statusText }
            }
        }
    }

    component InfoRow: RowLayout {
        required property string label
        required property string value
        Layout.fillWidth: true

        PlasmaComponents.Label {
            text: parent.label
            font.bold: true
            Layout.preferredWidth: Kirigami.Units.gridUnit * 8
            wrapMode: Text.Wrap
        }
        PlasmaComponents.Label {
            text: parent.value
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }
    }

    Plasma5Support.DataSource {
        id: provider
        engine: "executable"
        connectedSources: ["/usr/bin/aureonctl overview"]

        onNewData: function(source, data) {
            root.loading = false
            if (data["exit code"] !== 0) {
                root.statusText = i18n("Unavailable")
                return
            }
            try {
                const payload = JSON.parse(data.stdout)
                if (!payload.result || !payload.result.values) {
                    throw new Error("missing result")
                }
                root.overview = payload.result.values
                root.statusText = payload.result.state || i18n("Unavailable")
            } catch (error) {
                root.overview = ({})
                root.statusText = i18n("Unavailable")
            }
        }
    }
}
