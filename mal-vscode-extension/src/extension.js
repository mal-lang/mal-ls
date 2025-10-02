"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
var path = require("path");
var node_1 = require("vscode-languageclient/node");
var client;
function activate(context) {
    var serverCommand = "uv";
    var serverArgs = ["run", "python", path.join(context.extensionPath, "server.py")];
    var serverOptions = {
        run: { command: serverCommand, args: serverArgs },
        debug: { command: serverCommand, args: serverArgs }
    };
    var clientOptions = {
        documentSelector: [{ scheme: "file", language: "mal" }]
    };
    client = new node_1.LanguageClient("malLanguageServer", "MAL Language Server", serverOptions, clientOptions);
    context.subscriptions.push(client.start());
}
function deactivate() {
    return client ? client.stop() : undefined;
}
