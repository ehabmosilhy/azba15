#!/bin/bash

# Set the admin password
admin_pass=sam6

# Set the name of the database to be backed up
db_name=azbah3

# Set the path and file name for the backup file
bk_path_and_file=/home/azbah/staging/bk/${db_name}.zip
echo "Starting Backup ... "
# Backup the database from the live server
curl -X POST \
    -F "master_pwd=${admin_pass}" \
    -F "name=${db_name}" \
    -F "backup_format=zip" \
    -o ${bk_path_and_file} \
    http://127.0.0.1:8015/web/database/backup

echo "Starting Restore ... "
# Restore the backed up database to the staging server
curl -X POST -F "master_pwd=${admin_pass}" -F "backup_file=@./azbah3.zip" -F "name=azbah3" -F "copy=true" http://127.0.0.1:8055/web/database/restore
