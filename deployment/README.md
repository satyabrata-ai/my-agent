# Deployment

This directory contains the Terraform configurations for provisioning the necessary Google Cloud infrastructure for your agent.

The recommended way to deploy the infrastructure and set up the CI/CD pipeline is by using the `agent-starter-pack setup-cicd` command from the root of your project.

However, for a more hands-on approach, you can always apply the Terraform configurations manually for a do-it-yourself setup.

For detailed information on the deployment process, infrastructure, and CI/CD pipelines, please refer to the official documentation:

**[Agent Starter Pack Deployment Guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment.html)**

Local migration helpers
-----------------------

The repository includes a small migration helper to create the `realtime_alerts` BigQuery table from the SQL template:

```bash
python scripts/migrate_realtime_alerts.py --dry-run  # preview DDL
python scripts/migrate_realtime_alerts.py           # execute (requires ADC)
```

The DDL template is at `deployment/terraform/sql/realtime_alerts.sql` and is used by CI/CD or manual migrations.