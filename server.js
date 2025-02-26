const express = require('express');
const WebSocket = require('ws');

const app = express();
app.use(express.json());

const PORT = 5000;
const wss = new WebSocket.Server({ port: 5001 });

let vscodeClient = null;

wss.on('connection', (ws) => {
    console.log("✅ VS Code extension connected!");
    vscodeClient = ws;

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message.toString());
            console.log("📩 Message from Python client:", data);
            
            // Forward the command to VS Code
            if (data.command === 'insertGeneratedCode') {
                console.log("🔄 Forwarding insertGeneratedCode command");
                sendToVSCode("insertGeneratedCode", data.content);
            } else if (data.command === 'editLine') {
                console.log("🔄 Forwarding editLine command");
                sendToVSCode("editLine", null);
            } else if (data.command === 'deleteLine') {
                console.log("🔄 Forwarding deleteLine command");
                sendToVSCode("deleteLine", null);
            }
        } catch (error) {
            console.error("❌ Error processing message:", error);
        }
    });

    ws.on('close', () => {
        console.log("❌ VS Code extension disconnected!");
        vscodeClient = null;
    });
});

app.post('/insertGeneratedCode', (req, res) => {
    sendToVSCode("insertGeneratedCode", res);
});

app.post('/editLine', (req, res) => {
    sendToVSCode("editLine", res);
});

app.post('/deleteLine', (req, res) => {
    sendToVSCode("deleteLine", res);
});

function sendToVSCode(command, content) {
    if (vscodeClient) {
        vscodeClient.send(JSON.stringify({ command, content }));
        if (content && content.send) {
            content.send({ message: `✅ Sent ${command} command to VS Code!` });
        }
    } else {
        if (content && content.status) {
            content.status(500).send({ error: "❌ No active VS Code extension connection!" });
        }
        console.error("❌ No active VS Code extension connection!");
    }
}

app.listen(PORT, () => {
    console.log(`🚀 VS Code API Server running on port ${PORT}`);
    console.log(`🔗 Waiting for VS Code extension connection on WebSocket port 5001...`);
});
