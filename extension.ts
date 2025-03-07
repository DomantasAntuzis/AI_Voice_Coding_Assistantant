import * as vscode from 'vscode';
import WebSocket = require('ws');

let ws: WebSocket | null = null;

function connectWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:5001', {
            perMessageDeflate: false
        });

        ws.on('open', () => {
            vscode.window.showInformationMessage('Connected to AI Assistant Server');
            console.log('Connected to WebSocket server');
        });

        ws.on('message', (data: WebSocket.Data) => {
            try {
                console.log('Raw WebSocket message received:', data.toString());
                const message = JSON.parse(data.toString());
                console.log('Parsed message:', message);
                
                if (message.command === 'insertGeneratedCode' && message.content) {
                    console.log('Attempting to insert code:', message.content);
                    const editor = vscode.window.activeTextEditor;
                    if (editor) {
                        console.log('Active editor found, inserting code...');
                        editor.edit(editBuilder => {
                            const position = editor.selection.active;
                            editBuilder.insert(position, message.content);
                        }).then(success => {
                            console.log('Edit result:', success);
                            if (success) {
                                vscode.window.showInformationMessage('Code inserted!');
                            }
                        });
                    } else {
                        vscode.window.showErrorMessage('No active editor found. Please open a file first.');
                    }
                } else if (message.command === 'deleteLine') {
                    console.log('Attempting to delete line');
                    const editor = vscode.window.activeTextEditor;
                    if (editor) {
                        const selection = editor.selection;
                        const lineToDelete = selection.active.line;
                        
                        editor.edit(editBuilder => {
                            // Create a range that includes the line break
                            const range = editor.document.validateRange(
                                new vscode.Range(
                                    lineToDelete, 0,
                                    lineToDelete + 1, 0
                                )
                            );
                            editBuilder.delete(range);
                        }).then(success => {
                            console.log('Delete line result:', success);
                            if (success) {
                                vscode.window.showInformationMessage('Line deleted!');
                            }
                        });
                    } else {
                        vscode.window.showErrorMessage('No active editor found. Please open a file first.');
                    }
                }
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
                vscode.window.showErrorMessage('An error occurred while processing the WebSocket message.');
            }
        }); 

        ws.on('error', (error: Error) => {
            console.error('WebSocket error:', error);
            vscode.window.showErrorMessage('WebSocket error: ' + error.message);
        });

        ws.on('close', () => {
            console.log('Connection closed, attempting to reconnect...');
            setTimeout(connectWebSocket, 3000);
        });
    } catch (error) {
        console.error('Connection error:', error);
        setTimeout(connectWebSocket, 3000);
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Assistant extension is now active!');
    
    // Initial connection
    connectWebSocket();

    // Register reconnect command
    let disposable = vscode.commands.registerCommand('ai-assistant.reconnect', () => {
        if (ws) {
            ws.terminate();
        }
        connectWebSocket();
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {
    if (ws) {
        ws.terminate();
    }
}