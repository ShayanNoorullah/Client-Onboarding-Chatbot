# n8n integration for ATI webhooks

Receive ATI onboarding events in [n8n](https://n8n.io/) (self-hosted or Cloud) with no changes to the ATI application.

**Cost:** Self-hosted n8n is free. n8n Cloud has paid tiers. ATI does not charge per webhook event.

## Quick start

### 1. Run n8n (local example)

```powershell
docker run -d --name n8n -p 5678:5678 -e ATI_WEBHOOK_SECRET=your-shared-secret n8nio/n8n
```

Open http://localhost:5678 and complete the n8n setup wizard.

Set `ATI_WEBHOOK_SECRET` to the same value you will enter in the ATI admin webhook **Secret** field (optional but recommended).

### 2. Import the sample workflow

1. In n8n: **Workflows** → **Import from File**
2. Select [`ati-webhook-receiver.workflow.json`](ati-webhook-receiver.workflow.json)
3. Open the **ATI Webhook** node and note the **Production URL** (e.g. `http://localhost:5678/webhook/ati-onboarding`)
4. **Activate** the workflow (toggle in top-right — inactive workflows do not receive production webhooks)

### 3. Register the URL in ATI admin

Admin → **Configuration → Webhooks** → http://127.0.0.1:8001/admin/config-webhooks.html

| Field | Value |
|-------|-------|
| Name | `n8n automation` |
| URL | n8n **Production** webhook URL (not Test URL) |
| Secret | Same as `ATI_WEBHOOK_SECRET` (leave empty to skip signature check) |
| Events | `brief.created, user.registered, session.created` |

Save, then click **Test** on the webhook row. You should see a `test.ping` execution in n8n and status **delivered** under **Recent Deliveries** in ATI.

## Workflow overview

```
ATI Webhook → Normalize Payload → Route by Event → placeholder branches
```

| Node | Purpose |
|------|---------|
| **ATI Webhook** | POST receiver at path `ati-onboarding` |
| **Normalize Payload** | Flattens `body.event` / `body.data` for routing (no crypto required) |
| **Route by Event** | Branches on `event` field |
| **NoOp stubs** | Replace with CRM, Slack, email, or your own logic |

### Payload shape

ATI sends:

```json
{
  "event": "brief.created",
  "timestamp": "2026-06-08T12:00:00Z",
  "data": {
    "brief_id": "abc123",
    "client_name": "Acme Corp",
    "user_email": "client@acme.com"
  }
}
```

After **Normalize Payload**, use `$json.event` and `$json.data.*` in downstream nodes.

### Supported events

- `brief.created`, `brief.updated`
- `user.registered`
- `session.created`, `session.completed`, `session.abandoned`
- `test.ping` (ATI admin **Test** button)

Add more event names to the ATI webhook **Events** field and extend the **Route by Event** switch as needed.

## Networking

| Environment | URL to use in ATI |
|-------------|-------------------|
| Local dev (same PC) | `http://localhost:5678/webhook/ati-onboarding` |
| n8n on another server | Public `https://` URL reachable from the ATI host |
| ATI in cloud, n8n local | Use a tunnel (ngrok, Cloudflare Tunnel) or host n8n publicly |

ATI must be able to `POST` to the n8n URL. A failed connection appears in **Recent Deliveries** on the Webhooks admin page.

## Signature verification (optional)

Leave **Secret** empty in ATI admin for local dev (recommended). The sample workflow does not use `require('crypto')`, which n8n blocks by default.

If you need HMAC verification later, set the same secret in ATI admin and start n8n with:

```powershell
$env:NODE_FUNCTION_ALLOW_BUILTIN = "crypto"
npx n8n
```

ATI sends `X-Webhook-Signature: <hmac-sha256-hex>` when a secret is configured.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No executions in n8n | Activate the workflow; use Production URL |
| ATI shows `delivered` but n8n execution failed | n8n returns 200 before later nodes run — check **Executions** for errors |
| `Module 'crypto' is disallowed` | Re-import updated workflow, or edit Code node to remove `require('crypto')` |
| ATI delivery failed | Confirm n8n is running and URL is reachable |
| `test.ping` works, live events do not | Add event names to ATI webhook **Events** field |

## Related docs

- [SETUP.md Section 8](../../SETUP.md#8-webhooks--crm-integrations) — full webhook setup
- [IMPLEMENTATION.md](../../IMPLEMENTATION.md) — notification architecture
