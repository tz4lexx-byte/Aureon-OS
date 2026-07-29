# Aureon interactive installer defaults.
# Deliberately absent: clearpart, autopart, ignoredisk, zerombr and target disk.
text
firstboot --enable
keyboard --vckeymap=latam --xlayouts='latam'
lang es_MX.UTF-8
timezone America/Mexico_City --utc
network --hostname=aureon --no-activate
bootc --source-imgref containers-storage:localhost/aureon-desktop-preview:payload --target-imgref @@AUREON_TARGET_REF@@
