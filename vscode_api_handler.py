import websocket
import json

class VSCodeAPIHandler:
    def __init__(self):
        self.ws_url = "ws://localhost:5001"  # WebSocket server URL
        try:
            self.ws = websocket.create_connection(self.ws_url)
            print("✅ Prisijungta prie WebSocket serverio!")  # DEBUG
        except Exception as e:
            print(f"❌ WebSocket prisijungimo klaida: {e}")

    def extract_code_from_markdown(self, text):
        """Extract code from markdown code blocks."""
        if not text:
            return ""
        
        lines = text.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:  # Start of code block
                    in_code_block = True
                    continue
                else:  # End of code block
                    in_code_block = False
                    break  # Stop after first code block
            elif in_code_block:
                # Skip the language identifier line (e.g., "python")
                if code_lines or not line.strip().lower() == 'python':
                    code_lines.append(line)
        
        return '\n'.join(code_lines)

    def send_command(self, command, content=None):
        """Siunčia komandą į WebSocket serverį (`server.js`)."""
        try:
            # Clean up the content if it's a code insertion
            if command == "insertGeneratedCode":
                content = self.extract_code_from_markdown(content)
                print(f"Extracted code to insert: {content}")  # Debug print
            
            message = json.dumps({"command": command, "content": content})
            self.ws.send(message)
            print(f"✅ Sent command to VS Code: {command}")  # DEBUG
        except Exception as e:
            print(f"❌ Klaida siunčiant komandą: {e}")

    def insert_generated_code(self, content=None):  # Modified to accept content
        """Sends command to insert generated code into VS Code."""
        self.send_command("insertGeneratedCode", content)

    def edit_line(self):
        """Siunčia komandą redaguoti pasirinktą eilutę VS Code."""
        self.send_command("editLine")

    def delete_line(self):
        """Sends command to delete the selected line in VS Code."""
        self.send_command("deleteLine")  # Make sure we use exactly "deleteLine" to match the extension

    def close(self):
        """Uždaro WebSocket ryšį."""
        self.ws.close()

# ❌ Ištriname `if __name__ == '__main__':` dalį, kad nesivykdytų automatiškai.
