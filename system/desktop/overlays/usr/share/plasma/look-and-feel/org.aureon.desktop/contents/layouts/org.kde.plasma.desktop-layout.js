var panel = new Panel;

panel.location = "bottom";
panel.height = 42;
panel.alignment = "center";
panel.lengthMode = "fit";
panel.opacity = "translucent";
panel.floating = true;

panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.pager");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.aureon.systemoverview");
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
