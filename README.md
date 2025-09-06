#💾 Backup & Recovery Validation Tool
This project provides a robust solution for backing up critical files and directories, validating their integrity, and ensuring recoverability. It is built in Python and designed to be a reliable component of any data management strategy.
---
#✨ Features
Automated Backup: Automatically copies or compresses source files and directories to a designated backup location (local or network).

Integrity Validation: Computes and compares SHA256 checksums of source and backup files to verify data integrity.

Resilience: Automatically retries the backup process up to N times if validation fails.

Logging & Rotation: Maintains a simple, structured CSV log of all backup operations and automatically rotates old backups to manage storage space.

Restore Validation: Includes a dedicated --restore function to test the recovery process, ensuring backups are usable.
---
#📁 Repository Structure
The project is organized with a clear and logical directory structure to separate scripts, configurations, and data.

backup-validate/
├── README.md
├── backup_validate.py
├── config.example.yaml
├── scripts/
│   └── run_backup.sh
├── backups/           # (gitignored) contains backups
└── logs/
    └── backup_log.csv
---
#🚀 How to Use
Prerequisites
You need Python 3.8+ installed. It is highly recommended to use a virtual environment to manage dependencies.

Bash

python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Running the Backup
The main script is backup_validate.py. You can configure its behavior using command-line arguments.

Example: Backing up a directory with compression

This command will compress the /var/log/myapp directory, back it up to ./backups, and run the integrity check.

Bash

python backup_validate.py --source /var/log/myapp --dest ./backups --compress
Example: Backing up a single file without compression

This command will copy server_logs.csv to ./backups without compression.

Bash

python backup_validate.py --source ./server_logs.csv --dest ./backups --no-compress
Validating Restore
To ensure a backup is recoverable, use the --restore flag.

Bash

python backup_validate.py --restore --backup ./backups/server_logs.csv_20250906.tar.gz --target ./restore_test
This will extract the specified backup file into the ./restore_test directory.

Scheduling with Cron
For automated daily backups, you can add a cron job. This example runs the backup every day at 3:30 AM and logs its output.

Code snippet

30 3 * * * /usr/bin/python3 /path/to/backup-validate/backup_validate.py --source /var/log/myapp --dest /path/to/backups --compress >> /path/to/backup-validate/logs/cron_run.log 2>&1
---
#⚙️ Configuration & Alerting
Environment Variables
The config.example.yaml file shows how you can manage configuration variables. For alerting, you can use environment variables:

Variable	Description
SLACK_WEBHOOK	The URL for a Slack Incoming Webhook to send notifications.
ADMIN_EMAIL	The email address to send alert messages to.
