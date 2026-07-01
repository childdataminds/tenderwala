# TenderWala Deployment Setup

This webhook flow is designed to avoid restarting the `tenderwala` app from
inside its own web request process.

## Files

- `deploy.sh`
  - Pulls the latest `main` branch
  - Restarts the `tenderwala` systemd service
  - Writes deploy logs to `/var/log/tenderwala-deploy.log`
- `deployment/tenderwala-deploy.service.example`
  - Example oneshot systemd unit for running deploys outside the web process
- `deployment/tenderwala-webhook-sudoers.example`
  - Example sudoers rule that lets the app service user start only the deploy unit

## VPS Setup

1. Copy `deploy.sh` to `/var/www/tenderwala/deploy.sh`
2. Make it executable:

```bash
chmod +x /var/www/tenderwala/deploy.sh
```

3. Copy `deployment/tenderwala-deploy.service.example` to:

```bash
/etc/systemd/system/tenderwala-deploy.service
```

4. Update the example values inside the unit:
   - `DEPLOY_RUN_AS`
   - `APP_DIR`
   - `APP_SERVICE_NAME`

5. Reload systemd:

```bash
sudo systemctl daemon-reload
```

6. Add the sudoers rule from `deployment/tenderwala-webhook-sudoers.example`
   using `visudo`

7. Test the deploy unit manually:

```bash
sudo systemctl start tenderwala-deploy.service
sudo journalctl -u tenderwala-deploy.service -n 50 --no-pager
tail -n 50 /var/log/tenderwala-deploy.log
```

## Webhook Logs

Webhook trigger logs are written by the app to:

```bash
/var/www/tenderwala/deploy-webhook.log
```

This lets you distinguish:

- GitHub webhook reached the app
- deploy unit start succeeded or failed
- deploy script output and restart result
