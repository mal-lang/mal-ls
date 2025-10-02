import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {

    const serverOptions: ServerOptions = {
        run: { command: "malls", args: ["--stdio"] },
        debug: { command: "malls", args: ["--stdio"] }
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: "file", language: "mal" }]
    };

    client = new LanguageClient(
        "malLanguageServer",
        "MAL Language Server",
        serverOptions,
        clientOptions
    );

    // Register client so it's disposed on extension shutdown
    context.subscriptions.push(client);

    // Then start it
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    return client ? client.stop() : undefined;
}
