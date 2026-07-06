# Backup Runbook

## Database
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

## Files
Backup `/var/lib/dxcon/uploads` volume.
