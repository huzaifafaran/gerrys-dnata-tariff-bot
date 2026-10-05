const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require("@whiskeysockets/baileys");
const pino = require("pino");
const express = require("express");
const path = require("path");

const PHONE_NUMBER = process.env.WHATSAPP_PHONE || "923282156448";
const WEBHOOK_URL = process.env.WEBHOOK_URL || "http://127.0.0.1:8000/webhooks/whatsapp";
const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json());

let sock = null;
const sentMessageIds = new Set();
const processedInboundIds = new Set();
const bridgeStartTime = Math.floor(Date.now() / 1000);

async function startSock() {
    const authPath = path.join(__dirname, "auth_info");
    const { state, saveCreds } = await useMultiFileAuthState(authPath);

    sock = makeWASocket({
        auth: state,
        logger: pino({ level: "silent" }),
        printQRInTerminal: false,
        browser: ["Ubuntu", "Chrome", "20.0.04"]
    });

    sock.ev.on("creds.update", saveCreds);

    if (!sock.authState.creds.registered) {
        setTimeout(async () => {
            try {
                const code = await sock.requestPairingCode(PHONE_NUMBER.replace(/\D/g, ""));
                console.log("\n==========================================");
                console.log(">>> WHATSAPP PAIRING CODE: " + code);
                console.log("==========================================\n");
            } catch (err) {
                console.error("Failed to request pairing code:", err);
            }
        }, 3000);
    }

    sock.ev.on("connection.update", (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === "close") {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log("Connection closed due to", lastDisconnect?.error, ", reconnecting:", shouldReconnect);
            if (shouldReconnect) {
                setTimeout(startSock, 3000);
            }
        } else if (connection === "open") {
            console.log(">>> WHATSAPP CONNECTED SUCCESSFULLY! <<<");
            console.log("Ready to receive and send messages on " + PHONE_NUMBER);
        }
    });

    sock.ev.on("messages.upsert", async ({ messages, type }) => {
        // Only process live incoming messages, skip historical syncs
        if (type !== "notify") return;

        for (const msg of messages) {
            const id = msg.key.id;
            const from = msg.key.remoteJid;
            const isFromMe = msg.key.fromMe;
            const timestamp = typeof msg.messageTimestamp === "number" ? msg.messageTimestamp : Number(msg.messageTimestamp);

            // Skip messages from before the bridge started
            if (timestamp && timestamp < bridgeStartTime - 5) {
                continue;
            }
            
            // Ignore duplicate notifications for the same message
            if (processedInboundIds.has(id)) continue;
            processedInboundIds.add(id);

            // Ignore messages sent by the bot's own API sendText
            if (sentMessageIds.has(id)) {
                sentMessageIds.delete(id);
                continue;
            }

            // Ignore group chats and status broadcasts
            if (!from || from.endsWith("@g.us") || from.includes("broadcast")) continue;

            const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text;
            if (!text) continue;

            // If it's fromMe but NOT to yourself (i.e. you replying to someone else from the phone), skip it
            const myJid = sock.user?.id?.split(":")[0] + "@s.whatsapp.net";
            if (isFromMe && from !== myJid) {
                continue;
            }

            console.log(`[INBOUND] Live message from ${from}: "${text}"`);

            const payload = {
                event: "message",
                session: "default",
                payload: {
                    id: id,
                    from: from,
                    body: text,
                    fromMe: false
                }
            };

            try {
                const response = await fetch(WEBHOOK_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                console.log(`[WEBHOOK] Forwarded to ${WEBHOOK_URL} - Status: ${response.status}`);
            } catch (err) {
                console.error(`[WEBHOOK] Error forwarding to ${WEBHOOK_URL}:`, err.message);
            }
        }
    });
}

// REST API for sending messages (compatible with WAHA interface)
app.post("/api/sendText", async (req, res) => {
    try {
        const { chatId, text } = req.body;
        if (!sock) {
            return res.status(503).json({ error: "WhatsApp socket not initialized" });
        }
        let jid = String(chatId).replace("@c.us", "@s.whatsapp.net");
        if (!jid.includes("@")) {
            jid = `${jid}@s.whatsapp.net`;
        }
        const result = await sock.sendMessage(jid, { text });
        if (result?.key?.id) {
            sentMessageIds.add(result.key.id);
        }
        console.log(`[OUTBOUND] Sent to ${jid}: ${text.substring(0, 40)}...`);
        return res.json({ id: result.key.id, status: "sent" });
    } catch (err) {
        console.error("[OUTBOUND] Error sending text:", err.message);
        return res.status(500).json({ error: err.message });
    }
});

app.get("/health", (req, res) => {
    res.json({ status: sock ? "online" : "connecting", phone: PHONE_NUMBER });
});

app.listen(PORT, () => {
    console.log(`WhatsApp Bridge running on http://127.0.0.1:${PORT}`);
    startSock();
});
