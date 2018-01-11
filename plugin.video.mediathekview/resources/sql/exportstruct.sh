#!/bin/bash
mysqldump -u root -p --add-drop-database --add-drop-table --events --routines --no-data --databases filmliste > filmliste-init-0.sql
sed -i'' -e 's/ AUTO_INCREMENT=[0-9]*//g' filmliste-init-0.sql
