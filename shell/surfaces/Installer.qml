import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Disk installer wizard. It only collects choices and shows progress; the plan is
// validated and executed by `prismctl installer` and a polkit-protected helper.
PanelWindow {
    id: root
    // 0 welcome, 1 region, 2 network, 3 disk, 4 account, 5 review, 6 installing, 7 done
    property int step: 0
    property string locale: "en_US.UTF-8"
    property string keyboard: "us"
    property string timezone: ""
    property string diskPath: ""
    property string fullname: ""
    property string username: ""
    property bool usernameEdited: false
    property string hostname: "prism"
    property string password: ""
    property string repeat: ""
    property string typed: ""
    readonly property bool opened: ShellState.installerOpen && ShellState.activeScreen === screen
    readonly property var disk: InstallerState.disks.find(item => item.path === diskPath) || null
    readonly property var reserved: ["root", "greeter", "nobody", "daemon", "bin", "sys", "sync", "games", "man", "mail", "ftp", "http", "dbus", "polkitd", "avahi", "uuidd", "git", "ntp"]
    readonly property bool userValid: /^[a-z_][a-z0-9_-]{0,31}$/.test(username) && reserved.indexOf(username) < 0 && username.indexOf("systemd-") !== 0
    readonly property bool hostValid: hostname.length <= 63 && /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/.test(hostname)
    readonly property bool nameValid: fullname.length <= 64 && !/[\x00-\x1f\x7f:,=]/.test(fullname)
    readonly property bool passwordValid: /^[^\x00-\x1f\x7f]{8,128}$/.test(password)
    readonly property bool accountValid: userValid && hostValid && nameValid && passwordValid && password === repeat
    readonly property bool confirmed: disk !== null && typed === disk.name
    readonly property bool canContinue: step === 0 ? true : step === 1 ? locale.length > 0 && keyboard.length > 0 && timezone.length > 0 : step === 2 ? InstallerState.online : step === 3 ? disk !== null && disk.eligible : step === 4 ? accountValid : step === 5 ? confirmed && InstallerState.preview !== null && !InstallerState.previewing : false
    readonly property var zoneChoices: InstallerState.timezones.map(name => ({
                id: name,
                label: name.replace(/_/g, " ")
            }))
    function localeLabel() {
        const found = InstallerState.locales.find(item => item.id === locale);
        return found ? found.label : locale;
    }
    function keyboardLabel() {
        const found = InstallerState.keyboards.find(item => item.id === keyboard);
        return found ? found.label : keyboard;
    }
    function request(confirm) {
        return {
            disk: diskPath,
            confirm: confirm,
            hostname: hostname,
            username: username,
            fullname: fullname.trim(),
            password: password,
            timezone: timezone,
            locale: locale,
            keyboard: keyboard
        };
    }
    function summarize(item) {
        const parts = (item.partitions || []).slice(0, 3).map(part => (part.label || part.fstype || "Partition") + " " + part.size_label);
        return parts.length ? parts.join(" · ") : "Empty disk";
    }
    function goTo(index) {
        step = index;
        if (index === 3)
            InstallerState.refreshDisks();
        if (index === 2)
            InstallerState.probe();
        if (index === 5) {
            typed = "";
            InstallerState.requestPreview(request(disk ? disk.name : ""));
        }
    }
    function advance() {
        if (!canContinue)
            return;
        if (step === 5) {
            InstallerState.start(request(typed));
            step = 6;
        } else {
            goTo(step + 1);
        }
    }
    function dismiss() {
        if (InstallerState.running)
            return;
        password = "";
        repeat = "";
        typed = "";
        ShellState.installerOpen = false;
        if (step === 7)
            step = 0;
    }
    onFullnameChanged: if (!usernameEdited)
        username = fullname.toLowerCase().replace(/[^a-z0-9_-]/g, "").replace(/^[^a-z_]+/, "").slice(0, 32)
    Connections {
        target: InstallerState
        function onDoneChanged() {
            if (InstallerState.done) {
                root.step = 7;
                root.password = "";
                root.repeat = "";
            }
        }
        function onDefaultTimezoneChanged() {
            if (root.timezone.length === 0)
                root.timezone = InstallerState.defaultTimezone;
        }
    }
    Component.onCompleted: if (InstallerState.defaultTimezone && timezone.length === 0)
        timezone = InstallerState.defaultTimezone
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "prism-installer"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    visible: opened
    color: Theme.surface
    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceContainerLow
        Rectangle {
            x: parent.width - 340
            y: -150
            width: 500
            height: 500
            radius: 250
            color: Theme.tertiaryContainer
            opacity: 0.7
        }
        Rectangle {
            x: -150
            y: parent.height - 280
            width: 440
            height: 440
            radius: 140
            color: Theme.primaryContainer
            opacity: 0.75
        }
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(980, root.width - 32)
        height: Math.min(700, root.height - 48)
        radius: Theme.shape.extraExtraLarge - 6
        color: Theme.surface
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.7)
        focus: root.opened
        Keys.onEscapePressed: root.dismiss()
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 18
            Row {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: 8
                    delegate: Rectangle {
                        required property int index
                        width: (card.width - 64 - 42) / 8
                        height: 6
                        radius: 3
                        color: index <= root.step ? Theme.primary : Theme.surfaceContainerHigh
                        Behavior on color {
                            ColorAnimation {
                                duration: Theme.fast
                            }
                        }
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                // 0: welcome
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 0
                    Rectangle {
                        Layout.preferredWidth: 88
                        Layout.preferredHeight: 88
                        radius: 30
                        color: Theme.primaryContainer
                        Symbol {
                            anchors.centerIn: parent
                            width: 46
                            height: 46
                            name: "download"
                            color: Theme.primaryContainerInk
                        }
                    }
                    Label {
                        text: "Install PrismOS"
                        role: "displaySmall"
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "Put PrismOS on this computer so it starts on its own, keeps your files and settings, and no longer needs the USB drive."
                        role: "titleMedium"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    SettingsGroup {
                        Layout.fillWidth: true
                        ListRow {
                            width: parent.width
                            interactive: false
                            title: "Startup mode"
                            supporting: InstallerState.firmware === "uefi" ? "UEFI, with a boot partition" : "Legacy BIOS, with a boot area"
                            symbol: "settings"
                        }
                        ListRow {
                            width: parent.width
                            interactive: false
                            title: InstallerState.online ? "Connected to the internet" : "Not connected to the internet"
                            supporting: "PrismOS downloads its base system while installing"
                            symbol: InstallerState.online ? "wifi" : "wifi_off"
                        }
                        ListRow {
                            width: parent.width
                            interactive: false
                            visible: InstallerState.battery.available === true && InstallerState.battery.charging !== true && InstallerState.battery.value < 40
                            title: "Plug in your charger"
                            supporting: "Battery is at " + InstallerState.battery.value + "%. Installing can take a while."
                            symbol: "battery"
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "You can keep trying PrismOS from the USB and install later. Nothing changes on your computer until you confirm the disk on the last step."
                        role: "bodyMedium"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
                // 1: language, keyboard, time zone
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    visible: root.step === 1
                    Label {
                        text: "Language and region"
                        role: "headlineLarge"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 18
                        ChoiceList {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            title: "Language"
                            model: InstallerState.locales
                            current: root.locale
                            onPicked: id => root.locale = id
                        }
                        ChoiceList {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            title: "Keyboard"
                            model: InstallerState.keyboards
                            current: root.keyboard
                            onPicked: id => root.keyboard = id
                        }
                        ChoiceList {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            title: "Time zone"
                            searchable: true
                            model: root.zoneChoices
                            current: root.timezone
                            onPicked: id => root.timezone = id
                        }
                    }
                }
                // 2: network
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 2
                    Label {
                        text: "Connect to the internet"
                        role: "headlineLarge"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "The installer downloads the base system from Arch Linux mirrors. Saved Wi-Fi networks are kept on the installed system."
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    SettingsGroup {
                        Layout.fillWidth: true
                        ListRow {
                            width: parent.width
                            interactive: false
                            chipColor: InstallerState.online ? Theme.primaryContainer : Theme.errorContainer
                            chipInk: InstallerState.online ? Theme.primaryContainerInk : Theme.errorContainerInk
                            title: InstallerState.online ? "You're online" : "Not connected"
                            supporting: InstallerState.online ? (InstallerState.connectivity === "full" ? "Internet access confirmed" : "Connected; internet access is limited") : "Join a network to continue"
                            symbol: InstallerState.online ? "wifi" : "wifi_off"
                        }
                    }
                    RowLayout {
                        spacing: 10
                        PillButton {
                            text: "Network settings"
                            variant: "tonal"
                            symbol: "wifi"
                            onClicked: SystemBridge.action("network-settings")
                        }
                        PillButton {
                            text: "Check again"
                            variant: "neutral"
                            symbol: "refresh"
                            onClicked: InstallerState.probe()
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
                // 3: disk
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    visible: root.step === 3
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: "Choose a disk"
                            role: "headlineLarge"
                        }
                        PillButton {
                            text: "Refresh"
                            variant: "neutral"
                            symbol: "refresh"
                            enabled: !InstallerState.loadingDisks
                            onClicked: InstallerState.refreshDisks()
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "PrismOS uses the whole disk. Everything on the disk you pick will be erased. Disks that are in use, read-only, or smaller than " + InstallerState.minDisk + " can't be chosen."
                        role: "bodyMedium"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    ListView {
                        id: diskList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        model: InstallerState.disks
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                        }
                        delegate: ListRow {
                            required property var modelData
                            width: diskList.width
                            enabled: modelData.eligible
                            selected: root.diskPath === modelData.path
                            title: modelData.model + " · " + modelData.size_label
                            supporting: modelData.eligible ? modelData.name + " · " + root.summarize(modelData) : modelData.name + " · " + modelData.reason
                            symbol: modelData.removable || modelData.transport === "USB" ? "usb" : "storage"
                            Accessible.role: Accessible.RadioButton
                            onClicked: root.diskPath = modelData.path
                        }
                        Label {
                            anchors.centerIn: parent
                            visible: diskList.count === 0
                            text: InstallerState.loadingDisks ? "Looking for disks…" : "No disks found"
                            role: "bodyLarge"
                            color: Theme.surfaceVariantInk
                        }
                    }
                }
                // 4: account
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    visible: root.step === 4
                    Label {
                        text: "Create your account"
                        role: "headlineLarge"
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: width >= 640 ? 2 : 1
                        columnSpacing: 20
                        rowSpacing: 10
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.alignment: Qt.AlignTop
                            spacing: 4
                            Label {
                                text: "Your name"
                                role: "labelLarge"
                                color: Theme.surfaceVariantInk
                            }
                            ExpressiveTextField {
                                Layout.fillWidth: true
                                placeholderText: "Alex Doe"
                                text: root.fullname
                                Accessible.name: "Your name"
                                onTextEdited: root.fullname = text
                            }
                            Label {
                                text: "User name"
                                role: "labelLarge"
                                color: Theme.surfaceVariantInk
                            }
                            ExpressiveTextField {
                                Layout.fillWidth: true
                                placeholderText: "alex"
                                text: root.username
                                Accessible.name: "User name"
                                onTextEdited: {
                                    root.usernameEdited = true;
                                    root.username = text;
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: root.username.length > 0 && !root.userValid ? "Use lowercase letters, numbers, - and _, starting with a letter" : ""
                                visible: text.length > 0
                                role: "bodySmall"
                                color: Theme.error
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                text: "Computer name"
                                role: "labelLarge"
                                color: Theme.surfaceVariantInk
                            }
                            ExpressiveTextField {
                                Layout.fillWidth: true
                                placeholderText: "prism"
                                text: root.hostname
                                Accessible.name: "Computer name"
                                onTextEdited: root.hostname = text.toLowerCase()
                            }
                            Label {
                                Layout.fillWidth: true
                                text: !root.hostValid ? "Use letters, numbers and hyphens" : ""
                                visible: text.length > 0
                                role: "bodySmall"
                                color: Theme.error
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.alignment: Qt.AlignTop
                            spacing: 4
                            Label {
                                text: "Password"
                                role: "labelLarge"
                                color: Theme.surfaceVariantInk
                            }
                            ExpressiveTextField {
                                Layout.fillWidth: true
                                echoMode: TextInput.Password
                                placeholderText: "At least 8 characters"
                                text: root.password
                                Accessible.name: "Password"
                                onTextEdited: root.password = text
                            }
                            Label {
                                text: "Repeat password"
                                role: "labelLarge"
                                color: Theme.surfaceVariantInk
                            }
                            ExpressiveTextField {
                                Layout.fillWidth: true
                                echoMode: TextInput.Password
                                placeholderText: "Type it again"
                                text: root.repeat
                                Accessible.name: "Repeat password"
                                onTextEdited: root.repeat = text
                            }
                            Label {
                                Layout.fillWidth: true
                                text: root.password.length > 0 && !root.passwordValid ? "Passwords need 8 to 128 characters" : root.repeat.length > 0 && root.repeat !== root.password ? "The passwords don't match" : ""
                                visible: text.length > 0
                                role: "bodySmall"
                                color: Theme.error
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                Layout.fillWidth: true
                                text: "You'll use this password to sign in and for administrator tasks. The root account is locked."
                                role: "bodySmall"
                                color: Theme.surfaceVariantInk
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
                // 5: review and confirm
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10
                    visible: root.step === 5
                    Label {
                        text: "Ready to install"
                        role: "headlineLarge"
                    }
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentHeight: summary.height
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                        }
                        SettingsGroup {
                            id: summary
                            width: parent.width
                            ListRow {
                                width: parent.width
                                interactive: false
                                title: root.disk ? root.disk.model + " · " + root.disk.size_label : ""
                                supporting: (root.disk ? root.disk.path : "") + " · " + (InstallerState.firmware === "uefi" ? "UEFI" : "Legacy BIOS")
                                symbol: "storage"
                            }
                            ListRow {
                                width: parent.width
                                interactive: false
                                title: "Disk layout"
                                supporting: InstallerState.preview ? InstallerState.preview.partitions.map(part => part.name).join(" + ") : "Preparing…"
                                symbol: "apps_grid"
                            }
                            ListRow {
                                width: parent.width
                                interactive: false
                                title: root.fullname.trim() || root.username
                                supporting: root.username + " · computer " + root.hostname
                                symbol: "person"
                            }
                            ListRow {
                                width: parent.width
                                interactive: false
                                title: root.localeLabel() + " · " + root.keyboardLabel() + " keyboard"
                                supporting: root.timezone.replace(/_/g, " ")
                                symbol: "globe"
                            }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: warning.implicitHeight + 24
                        radius: Theme.shape.large
                        color: Theme.errorContainer
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            Symbol {
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                name: "warning"
                                color: Theme.errorContainerInk
                            }
                            Label {
                                id: warning
                                Layout.fillWidth: true
                                text: root.disk ? "Everything on " + root.disk.model + " (" + root.disk.size_label + ") will be erased. This can't be undone." : ""
                                role: "bodyMedium"
                                color: Theme.errorContainerInk
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    ExpressiveTextField {
                        Layout.fillWidth: true
                        placeholderText: root.disk ? "Type " + root.disk.name + " to confirm" : ""
                        text: root.typed
                        Accessible.name: "Type the disk name to confirm"
                        onTextEdited: root.typed = text.trim()
                        onAccepted: root.advance()
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: InstallerState.error.length > 0
                        text: InstallerState.error
                        role: "bodySmall"
                        color: Theme.error
                        wrapMode: Text.WordWrap
                    }
                }
                // 6: installing / failed
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 6
                    Item {
                        Layout.fillHeight: true
                    }
                    ExpressiveLoader {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 96
                        Layout.preferredHeight: 96
                        visible: !InstallerState.failed
                    }
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 88
                        Layout.preferredHeight: 88
                        radius: 30
                        color: Theme.errorContainer
                        visible: InstallerState.failed
                        Symbol {
                            anchors.centerIn: parent
                            width: 44
                            height: 44
                            name: "warning"
                            color: Theme.errorContainerInk
                        }
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: InstallerState.failed ? "The installation didn't finish" : InstallerState.label || "Starting…"
                        role: "headlineSmall"
                    }
                    LinearProgress {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: Math.min(460, card.width - 80)
                        visible: !InstallerState.failed
                        value: InstallerState.percent / 100
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        visible: !InstallerState.failed
                        text: Math.round(InstallerState.percent) + "%"
                        role: "labelLarge"
                        color: Theme.surfaceVariantInk
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.maximumWidth: card.width - 80
                        visible: !InstallerState.failed && InstallerState.detail.length > 0
                        text: InstallerState.detail
                        role: "bodySmall"
                        color: Theme.surfaceVariantInk
                        elide: Text.ElideMiddle
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.maximumWidth: card.width - 80
                        visible: InstallerState.failed
                        text: InstallerState.error
                        role: "bodyMedium"
                        color: Theme.error
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        visible: !InstallerState.failed
                        text: "Keep this computer plugged in and turned on."
                        role: "bodyMedium"
                        color: Theme.surfaceVariantInk
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
                // 7: done
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 7
                    Item {
                        Layout.fillHeight: true
                    }
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 96
                        Layout.preferredHeight: 96
                        radius: 32
                        color: Theme.primaryContainer
                        Symbol {
                            anchors.centerIn: parent
                            width: 50
                            height: 50
                            name: "check"
                            color: Theme.primaryContainerInk
                        }
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "PrismOS is installed"
                        role: "displaySmall"
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.maximumWidth: card.width - 80
                        text: "Remove the USB drive, then restart. You'll sign in with the account you just created."
                        role: "titleMedium"
                        color: Theme.surfaceVariantInk
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                PillButton {
                    text: root.step === 0 ? "Not now" : "Back"
                    variant: "text"
                    visible: root.step < 6 || (root.step === 6 && InstallerState.failed)
                    enabled: !InstallerState.running
                    onClicked: {
                        if (root.step === 0)
                            root.dismiss();
                        else if (root.step === 6) {
                            InstallerState.reset();
                            root.goTo(5);
                        } else
                            root.goTo(root.step - 1);
                    }
                }
                Item {
                    Layout.fillWidth: true
                }
                PillButton {
                    text: "Keep exploring"
                    variant: "text"
                    visible: root.step === 7
                    onClicked: root.dismiss()
                }
                PillButton {
                    text: root.step === 0 ? "Get started" : root.step === 5 ? "Erase and install" : root.step === 7 ? "Restart" : "Continue"
                    variant: "filled"
                    visible: root.step < 6 || root.step === 7
                    enabled: root.step === 7 || root.canContinue
                    onClicked: {
                        if (root.step === 7)
                            SystemBridge.action("restart");
                        else
                            root.advance();
                    }
                }
            }
        }
    }
}
