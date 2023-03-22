
#!/bin/bash

# vars
now=$(date +"%Y_%m_%d_%H.%M")
bk_dir=/home/azbah/odoo/db_backup
db_name="AZBAH"
admin_pass=sam6
file_name=$db_name"_"$now".zip"

bk_path_and_file=${bk_dir}/$file_name


#read -p "Press [Enter] key to start backup..."

# create a backup
curl -X POST \
    -F "master_pwd=${admin_pass}" \
    -F "name=${db_name}" \
    -F "backup_format=zip" \
    -o ${bk_path_and_file} \
    http://127.0.0.1:8015/web/database/backup

rclone copy ${bk_path_and_file} gdrive:odoo15_bk

# delete old backups
#find ${bk_dir} -type f -mtime +7 -name "${db_name}.*.zip" -delete
#sudo find ${bk_dir} -type f -mtime +7 -name "${db_name}.*.zip" -delete 2>&1 | tee ./find_error.log
sudo find db_backup/ -name "AZB*" -type f -mtime +7 -delete 2>&1 | tee ./find_error.log
