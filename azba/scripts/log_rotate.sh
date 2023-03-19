#!/bin/bash

# Define the log files to check
files=( "/home/azbah/odoo/monitor/logs/odoo/odoo.log" "/home/azbah/odoo/monitor/logs/postgresql/postgresql.log" )

# Define the size limit in MB
limit=100

# Define the sequence prefix
prefix="_0"

# Define the maximum number of files to keep
max_files=10


  for file in "${files[@]}"; do
    # Check the size of the file
    size=$(du -m "$file" | cut -f1)

    # If the size exceeds the limit, rotate the file
    if [ "$size" -gt "$limit" ]; then
      # Determine the next suffix
      suffix=$(ls "${file}${prefix}"* 2> /dev/null | awk -F "${prefix}" '{print $2}' | sort -nr | head -n 1)
      suffix=$((suffix + 1))

      # Rename the file and add the suffix
      new_file="${file}${prefix}${suffix}"
      mv "$file" "$new_file"

      # Compress the new file
      gzip "$new_file"

      # If the number of files exceeds the maximum, remove the last one
      num_files=$(ls "${file}${prefix}"* 2> /dev/null | wc -l)
      if [ "$num_files" -gt "$max_files" ]; then
        last_file=$(ls "${file}${prefix}"* 2> /dev/null | sort | head -n 1)
        rm "$last_file"
      fi
    fi
  done
