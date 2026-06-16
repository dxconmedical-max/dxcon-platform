#!/bin/bash
set -e

cd "$(dirname "$0")/.."

TS=$(date +%Y%m%d-%H%M%S)

mkdir -p backups

cp instance/dxcon.db "backups/dxcon-$TS.db"

echo "Backup created: backups/dxcon-$TS.db"
