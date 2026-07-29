var panel = new Panel;

panel.location = "bottom";
panel.height = 52;
panel.alignment = "center";
panel.lengthMode = "fill";
panel.hiding = "none";
panel.opacity = "translucent";
panel.floating = false;

panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.pager");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.kde.plasma.systemtray");

// An optional Aureon widget must never prevent Plasma from retaining the
// panel and its essential controls if the package cannot be instantiated.
try {
    panel.addWidget("org.aureon.systemoverview");
} catch (error) {
    // Keep constructing the core panel even when the optional applet fails.
}
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
