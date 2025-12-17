# SSH Multi-Server Update Tool

A minimal Python tool to SSH into multiple servers and run commands (default: `yum update -y`).

## Features
- Sequential SSH connections to multiple hosts
- Support for password and key-based authentication
- Timeout support
- Dry-run mode to preview commands
- Simple CLI interface

## Installation

```bash
pip install paramiko
```

## Usage

### Run on multiple hosts via command line:
```bash
python ssh_update.py --hosts 192.0.2.10,192.0.2.11 --user root --key ~/.ssh/id_rsa
```

### Run on hosts from a file:
```bash
python ssh_update.py --hosts-file hosts.txt --user ec2-user --password
```

### Dry-run mode:
```bash
python ssh_update.py --hosts 192.0.2.10 --user root --dry-run
```

### Custom command:
```bash
python ssh_update.py --hosts 192.0.2.10 --user root --command "uptime"
```

## Docker Usage

Build the Docker image:
```bash
docker build -t ssh-update-tool .
```

Run with Docker:
```bash
docker run -it --rm -v ~/.ssh:/root/.ssh ssh-update-tool python ssh_update.py --hosts 192.0.2.10 --user root --key /root/.ssh/id_rsa
```

## Options

- `--hosts` — Comma-separated list of hosts (IP or hostname)
- `--hosts-file` — File with one host per line
- `--user` — SSH username (default: current user)
- `--password` — Prompt for SSH password
- `--key` — Path to private key file
- `--port` — SSH port (default: 22)
- `--command` — Command to run (default: `yum update -y`)
- `--timeout` — Connection/command timeout in seconds (default: 30)
- `--dry-run` — Show commands without executing

## License

MIT
