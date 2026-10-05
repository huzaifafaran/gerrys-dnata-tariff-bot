# Meta WhatsApp Cloud API Setup Guide (Graph API v21.0)

This guide documents the exact configuration required to connect this application to live Meta WhatsApp Cloud API.

---

## 1. Meta Developer & Business Account Prerequisites

1. **Meta Developer Account:** Register at [developers.facebook.com](https://developers.facebook.com/).
2. **Meta Business Account:** Ensure access to a verified or test Meta Business Account in Meta Business Manager.
3. **WhatsApp Business App:**
   - In Meta App Dashboard, click **Create App** → Select **Business** type.
   - Under "Add products to your app", click **Set up** on **WhatsApp**.

---

## 2. Credentials Checklist for `.env`

Retrieve the following values from the Meta App Dashboard and place them in your `.env` file:

| Variable | Location in Meta Dashboard | Description |
|---|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp → API Setup → Phone number ID | Identifies the sending WhatsApp number. |
| `WHATSAPP_ACCESS_TOKEN` | Business Settings → System Users → Generate Token | Permanent System User Token with `whatsapp_business_messaging` permission. |
| `WHATSAPP_APP_SECRET` | App Settings → Basic → App Secret | Used for HMAC SHA256 webhook signature verification. |
| `WHATSAPP_VERIFY_TOKEN` | User-defined secret string | Any secure random string shared between Meta Webhook setup and your `.env`. |
| `WHATSAPP_API_VERSION` | Fixed in app as `v21.0` | Pinned official Graph API version. |

Example `.env` snippet:
```dotenv
WHATSAPP_PROVIDER=meta
WHATSAPP_PHONE_NUMBER_ID=109876543210987
WHATSAPP_ACCESS_TOKEN=EAAG...
WHATSAPP_APP_SECRET=a1b2c3d4e5f6...
WHATSAPP_VERIFY_TOKEN=my_secure_random_verify_token_2026
WHATSAPP_API_VERSION=v21.0
```

---

## 3. Webhook Configuration

1. In your Meta App Dashboard, navigate to **WhatsApp** → **Configuration**.
2. Click **Edit** on the **Webhook** section.
3. **Callback URL:** `https://<YOUR_PUBLIC_HTTPS_DOMAIN>/webhooks/whatsapp`
   *(Must be publicly reachable over HTTPS with a valid SSL certificate)*
4. **Verify Token:** Enter the exact value configured in `WHATSAPP_VERIFY_TOKEN`.
5. Click **Verify and Save**. Meta will send a `GET` challenge to your endpoint. The app will validate `hub.verify_token` and return `hub.challenge`.
6. Under **Webhook fields**, click **Manage** and subscribe to **`messages`**.

### Local Testing with Tunnel
For local development, expose port 8000 using ngrok or Cloudflare tunnel:
```bash
# Using ngrok
ngrok http 8000

# Set Meta Callback URL to:
https://<your-subdomain>.ngrok-free.app/webhooks/whatsapp
```

---

## 4. Architecture & Delivery Guarantees

1. **HMAC Signature Validation:**
   Every incoming POST request contains the `X-Hub-Signature-256` header. The application validates this against the raw body bytes using `WHATSAPP_APP_SECRET`. Unsigned or tampered requests are rejected with `401 Unauthorized`.
2. **Immediate Acknowledgment & Asynchronous Worker:**
   Webhooks are acknowledged with `200 OK` promptly to avoid Meta retry storms. Outbound replies are stored in the `outbox_jobs` table and dispatched by the background worker.
3. **Idempotency & Deduplication:**
   Every Meta message has a unique `id` (e.g. `wamid.HBgL...`). The system records all processed message IDs in `inbound_events`. Retried or duplicate events are safely ignored.
4. **24-Hour Customer Care Window:**
   The bot replies directly to inbound user queries. Standard customer-service replies do not require pre-approved message templates as long as they occur within 24 hours of the customer's last message.
5. **Safe Status Handling:**
   Status notifications (`sent`, `delivered`, `read`) sent by Meta are safely parsed and acknowledged without triggering infinite reply loops.
