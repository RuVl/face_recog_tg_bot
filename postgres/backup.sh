#!/bin/bash

# Settings
BACKUP_DIR=/var/backups/postgres
DATE=$(date +\%Y-\%m-\%d_\%H-\%M-\%S)
FILENAME=backup_$DATE.dump

# Password for postgres utilities 
export PGPASSWORD="$POSTGRES_PASSWORD"

# Make dirs if not exist
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -F c "$POSTGRES_DB" > "$BACKUP_DIR/$FILENAME" &&
echo "Backup done at $DATE"

# Deleting old backups (older than 60 days)
find $BACKUP_DIR -type f -name "*.dump" -mtime +60 -exec rm {} \;
