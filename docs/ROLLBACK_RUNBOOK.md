# Rollback Runbook

1. Enable maintenance mode
2. Redeploy previous Docker image tag
3. Restore database from last good backup if needed
4. Run health checks
5. Disable maintenance mode
