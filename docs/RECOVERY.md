# DxCon Recovery Checklist

## 1. Kiểm tra hệ thống
- /api/v1/system/health
- /api/v1/system/stats
- /api/v1/system/routes
- /api/v1/system/backup-status

## 2. Backup PostgreSQL
Render Dashboard:
- dxcon-postgres
- Backups
- Enable Daily Backups
- Retention: 7-30 days

## 3. Khi production lỗi
- Kiểm tra Render Logs
- Kiểm tra commit mới nhất
- Rollback deploy nếu cần
- Restore PostgreSQL backup nếu database lỗi

## 4. URL quan trọng
- /
- /executive-v9
- /finance
- /crm-pipeline
- /security
- /audit
- /api/v1/system/health
- /api/v1/system/stats
