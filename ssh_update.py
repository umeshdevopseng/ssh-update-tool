#!/usr/bin/env python3
"""
Minimal SSH runner: sequentially SSH to hosts and run a command (default: yum update -y).

Usage:
  python ssh_update.py --hosts 192.0.2.10,192.0.2.11 --user root --key ~/.ssh/id_rsa
  python ssh_update.py --hosts-file hosts.txt --user ec2-user --password

This file is intentionally small and simple.
"""
from __future__ import annotations
import argparse
import getpass
import os
import socket
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import paramiko
except Exception:
    print("Missing dependency 'paramiko'. Install with: pip install paramiko", file=sys.stderr)
    raise


def parse_args():
    p = argparse.ArgumentParser(description="Run a command on multiple hosts over SSH (minimal tool).")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--hosts", help="Comma-separated hosts (ip or hostname)")
    group.add_argument("--hosts-file", type=Path, help="File with one host per line")
    p.add_argument("--user", help="SSH username (default: current user)")
    p.add_argument("--password", action="store_true", help="Prompt for SSH password (instead of key)")
    p.add_argument("--key", help="Path to private key file for key-based auth")
    p.add_argument("--port", type=int, default=22, help="SSH port (default 22)")
    p.add_argument("--command", default="yum update -y", help='Command to run on remote hosts (default: "yum update -y")')
    p.add_argument("--timeout", type=float, default=30.0, help="Connection/command timeout seconds")
    p.add_argument("--dry-run", action="store_true", help="Show commands only; don't execute")
    return p.parse_args()


def load_hosts_from_args(args) -> List[str]:
    hosts: List[str] = []
    if args.hosts:
        for h in args.hosts.split(","):
            hh = h.strip()
            if hh:
                hosts.append(hh)
    elif args.hosts_file:
        if not args.hosts_file.exists():
            raise FileNotFoundError(f"Hosts file not found: {args.hosts_file}")
        for line in args.hosts_file.read_text(encoding="utf-8").splitlines():
            ln = line.split("#", 1)[0].strip()
            if ln:
                hosts.append(ln)
    return hosts


def run_command_on_host(host: str, username: str, password: Optional[str], keyfile: Optional[str], port: int,
                        timeout: float, command: str, dry_run: bool = False) -> Dict[str, Any]:
    result: Dict[str, Any] = {"host": host, "ok": False, "exit_status": None, "stdout": "", "stderr": "", "error": None, "elapsed": None}
    if dry_run:
        result.update({"ok": True, "stdout": f"DRY-RUN: would run on {host}: {command}"})
        return result

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    start = time.time()
    try:
        connect_kwargs = {"hostname": host, "port": port, "username": username, "timeout": timeout}
        if password is not None:
            connect_kwargs.update({"password": password, "look_for_keys": False, "allow_agent": False})
        elif keyfile:
            keypath = os.path.expanduser(keyfile)
            connect_kwargs.update({"key_filename": keypath, "look_for_keys": False, "allow_agent": False})

        client.connect(**connect_kwargs)
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read()
        err = stderr.read()
        result["stdout"] = out.decode("utf-8", errors="replace") if isinstance(out, (bytes, bytearray)) else str(out)
        result["stderr"] = err.decode("utf-8", errors="replace") if isinstance(err, (bytes, bytearray)) else str(err)
        try:
            result["exit_status"] = stdout.channel.recv_exit_status()
            result["ok"] = (result["exit_status"] == 0)
        except Exception:
            result["ok"] = True
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
        result["error"] = f"{e.__class__.__name__}: {e}"
    finally:
        try:
            client.close()
        except Exception:
            pass
        result["elapsed"] = time.time() - start
    return result


def main(argv=None) -> int:
    args = parse_args()
    user = args.user or getpass.getuser()
    password = None
    if args.password:
        password = getpass.getpass("SSH password: ")

    hosts = load_hosts_from_args(args)
    if not hosts:
        print("No hosts provided.", file=sys.stderr)
        return 2

    print(f"Will run on {len(hosts)} host(s): {', '.join(hosts)}")
    if args.dry_run:
        print("DRY RUN: no commands will be executed")

    all_ok = True
    for h in hosts:
        print(f"-- {h} --")
        res = run_command_on_host(h, user, password, args.key, args.port, args.timeout, args.command, dry_run=args.dry_run)
        if res.get("ok"):
            print(f"OK ({res.get('elapsed'):.1f}s)")
            if res.get("stdout"):
                print(res.get("stdout"))
        else:
            all_ok = False
            print(f"FAILED: {res.get('error') or ('exit='+str(res.get('exit_status')))} ({res.get('elapsed'):.1f}s)")
            if res.get("stderr"):
                print(res.get("stderr"))

    print("\nDone.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
