#!/usr/bin/env python3
"""
backup_validate.py
Usage examples:
  python backup_validate.py --source /var/log/myapp --dest ./backups --compress
  python backup_validate.py --source ./server_logs.csv --dest ./backups --no-compress
  python backup_validate.py --restore --backup ./backups/myapp_20250906.tar.gz --target ./restore_test
"""

import argparse, hashlib, tarfile, shutil, os, time, datetime, pathlib, csv

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def make_backup(source, dest_dir, compress=True):
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    src = pathlib.Path(source)
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        fname = f"{src.name}_{ts}.tar.gz" if compress else f"{src.name}_{ts}.tar"
        out_path = pathlib.Path(dest_dir) / fname
        mode = "w:gz" if compress else "w"
        with tarfile.open(out_path, mode) as tar:
            tar.add(str(src), arcname=src.name)
        return str(out_path)
    else:
        # file
        base = src.name
        fname = f"{base}_{ts}.gz" if compress else f"{base}_{ts}"
        out_path = pathlib.Path(dest_dir) / fname
        if compress:
            with tarfile.open(out_path, "w:gz") as tar:
                tar.add(str(src), arcname=base)
        else:
            shutil.copy2(str(src), str(out_path))
        return str(out_path)

def verify_backup(source, backup_path):
    # For simple approach: compare checksum of source and of a restored copy
    # If backup is a tar.gz for a file, extract temp and compute checksum
    tmpdir = pathlib.Path("./.tmp_restore")
    if tmpdir.exists():
        shutil.rmtree(str(tmpdir))
    tmpdir.mkdir()
    try:
        if tarfile.is_tarfile(backup_path):
            with tarfile.open(backup_path, "r:*") as tar:
                tar.extractall(path=str(tmpdir))
            # assume single root item
            restored_items = list(tmpdir.iterdir())
            # if source was file, restored item path will match
            # compute checksum of first file encountered (works for simple cases)
            # For directories, we can compute aggregated checksum
            srcpath = pathlib.Path(source)
            if srcpath.is_file():
                restored_file = next(tmpdir.rglob(srcpath.name))
                src_sum = sha256_of_file(str(srcpath))
                restored_sum = sha256_of_file(str(restored_file))
                return src_sum == restored_sum
            else:
                # directory: compute aggregated checksums (sorted)
                def agg_checksum(root):
                    items = sorted([p for p in pathlib.Path(root).rglob("*") if p.is_file()])
                    h = hashlib.sha256()
                    for f in items:
                        h.update(sha256_of_file(str(f)).encode())
                    return h.hexdigest()
                return agg_checksum(str(srcpath)) == agg_checksum(str(tmpdir / srcpath.name))
        else:
            # plain file copy
            return sha256_of_file(source) == sha256_of_file(backup_path)
    finally:
        shutil.rmtree(str(tmpdir))

def rotate_backups(dest_dir, keep=7):
    p = pathlib.Path(dest_dir)
    files = sorted([f for f in p.iterdir() if f.is_file()], key=lambda x: x.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        old.unlink()

def log_entry(logfile, source, backup_path, status, attempts, msg=""):
    t = datetime.datetime.utcnow().isoformat()
    row = [t, source, backup_path, status, attempts, msg]
    first = not os.path.exists(logfile)
    with open(logfile, "a", newline="") as f:
        writer = csv.writer(f)
        if first:
            writer.writerow(["timestamp","source","backup_path","status","attempts","message"])
        writer.writerow(row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--compress", action="store_true", default=False)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--keep", type=int, default=7)
    parser.add_argument("--logfile", default="./logs/backup_log.csv")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--backup", help="path to backup to restore")
    parser.add_argument("--target", help="restore target path")
    args = parser.parse_args()

    if args.restore:
        # quick restore test
        if not args.backup or not args.target:
            print("For restore: provide --backup and --target")
            return
        with tarfile.open(args.backup, "r:*") as tar:
            tar.extractall(path=args.target)
        print("Restore completed.")
        return

    attempts = 0
    success = False
    backup_path = ""
    while attempts <= args.retries and not success:
        attempts += 1
        try:
            backup_path = make_backup(args.source, args.dest, compress=args.compress)
            ok = verify_backup(args.source, backup_path)
            if ok:
                log_entry(args.logfile, args.source, backup_path, "success", attempts, "")
                rotate_backups(args.dest, keep=args.keep)
                success = True
                print("Backup verified successfully:", backup_path)
            else:
                log_entry(args.logfile, args.source, backup_path, "failure", attempts, "checksum mismatch")
                print("Verification failed, retrying...")
                time.sleep(5)
        except Exception as e:
            log_entry(args.logfile, args.source, backup_path or "n/a", "failure", attempts, str(e))
            print("Error during backup:", e)
            time.sleep(5)

    if not success:
        print("Backup failed after retries.")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
