"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const node_1 = require("vscode-languageclient/node");
let client;
function activate(context) {
    const serverOptions = {
        run: { command: "malls", args: ["--stdio"] },
        debug: { command: "malls", args: ["--stdio"] }
    };
    const clientOptions = {
        documentSelector: [{ scheme: "file", language: "mal" }]
    };
    client = new node_1.LanguageClient("malLanguageServer", "MAL Language Server", serverOptions, clientOptions);
    // Register client so it's disposed on extension shutdown
    context.subscriptions.push(client);
    // Then start it
    client.start();
}
function deactivate() {
    return client ? client.stop() : undefined;
}
//# sourceMappingURL=extension.js.map