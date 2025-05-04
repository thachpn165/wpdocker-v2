# WP Docker v2

A comprehensive Docker-based WordPress development environment manager.

## Features

- **WordPress Site Management**: Create, delete, and manage multiple WordPress sites
- **Database Management**: Create, backup, and restore MySQL databases
- **Nginx Configuration**: Customize Nginx settings for optimal performance
- **PHP Configuration**: Change PHP versions and configure PHP settings
- **SSL Support**: Automatically generate and manage SSL certificates
- **Backup System**: Create and restore backups with local and cloud storage support
- **Scheduled Tasks**: Automated backups and maintenance via cron jobs
- **Cloud Integration**: Rclone integration for cloud storage providers

## Backup System

The backup system provides functionality for backing up and restoring WordPress websites with support for both local and cloud storage.

### Key Features

- **Central Management**: BackupManager provides a unified interface for all backup operations
- **Multiple Storage Options**: Store backups locally or in the cloud via Rclone
- **Scheduled Backups**: Set up automated backups on daily, weekly, or monthly schedules
- **Retention Management**: Automatically maintain a configurable number of recent backups
- **User-Friendly Interface**: Interactive CLI prompts for all backup operations

### Documentation

For detailed information about the backup system, see the [backup documentation](docs/backup/index.md).

## Cron System

The cron system provides functionality for scheduling and executing automated tasks.

### Key Features

- **Flexible Scheduling**: Schedule tasks using standard cron expressions
- **Job Management**: Enable, disable, and remove scheduled jobs
- **Extensible Framework**: Plugin-based architecture for different job types
- **Detailed Logging**: Comprehensive logs for job execution
- **Command-Line Interface**: CLI tools for managing and monitoring jobs

### Documentation

For detailed information about the cron system, see the [cron documentation](docs/cron/index.md).

## Installation

1. Clone this repository
2. Run the initialization script:
   ```bash
   ./scripts/init.sh
   ```
3. Follow the prompts to configure your environment

## Usage

### Creating a WordPress Site

```bash
./wpdocker create
```

### Backing Up a Site

```bash
./wpdocker backup create
```

### Setting Up Scheduled Backups

```bash
./wpdocker backup schedule
```

### Restoring a Backup

```bash
./wpdocker backup restore
```

### Managing Scheduled Tasks

```bash
./wpdocker cron list
./wpdocker cron status <job_id>
./wpdocker cron enable <job_id>
./wpdocker cron disable <job_id>
```

## Documentation

- [Backup System](docs/backup/index.md)
- [Cron System](docs/cron/index.md)
- [Rclone Integration](docs/rclone/index.md)

## Requirements

- Docker and Docker Compose
- Python 3.8 or higher
- Bash shell

## License

This project is licensed under the MIT License - see the LICENSE file for details.