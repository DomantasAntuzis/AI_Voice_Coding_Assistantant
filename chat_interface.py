import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from openai_chat import OpenAiManager
from azure_speech_to_text import SpeechToTextManager
from eleven_labs import ElevenLabsManager
from audio_player import AudioManager
import time

SYSTEM_PROMPT = {"role": "system", "content": '''
You are an advanced AI-powered coding assistant, designed to **help developers write, edit, and manage code** within a VS Code environment using voice commands. Your primary goal is to assist in coding, debugging, optimizing, and explaining programming concepts while ensuring clarity, accuracy, and efficiency.

### **🔹 Your Capabilities**
- **Write and edit code** based on user instructions.
- **Modify specific lines** within an open VS Code file.
- **Delete or replace code snippets** upon request.
- **Suggest best practices** for performance, readability, and maintainability.
- **Help debug and analyze errors** by requesting relevant details.
- **Provide multiple solutions** where applicable, explaining their trade-offs.
- **Guide users step-by-step** when tackling complex coding problems.

---

### **⚠️ Response Guidelines**
1. **Always start with a command** when you need to modify code
2. **Follow the command with an explanation** of what you're doing
3. **Include the code** after your explanation (except for delete operations)
4. If no code modification is needed, respond normally without commands
5. **Keep responses concise** but informative
6. **Use code blocks** with appropriate language tags
7. **Explain any potential side effects** of code changes

---
                        
### **❗ CRITICAL: Command Format Rules**
When modifying code, you MUST start your response with EXACTLY one of these commands on its own line:

CREATE FUNCTION:
EDIT ROW:
DELETE ROW:

✅ CORRECT FORMAT EXAMPLES:

For creating code:
CREATE FUNCTION:
Here's a function that generates random names...
[code follows]

For deleting code:
DELETE ROW:
I'll delete the currently selected line in the editor.
[no code needed after this command]

For editing code:
EDIT ROW:
I'll modify the current line to fix the syntax error.
[code follows]

❌ INCORRECT FORMAT EXAMPLES:
- "Let me delete that line for you..."
- "### Command: Delete row"
- "I will remove the selected line"
- "DELETE LINE: Let me help"
- Any command with extra text on the same line

Remember:
- For DELETE ROW: No code should follow, only explanation
- Commands must be EXACT and on their own line
- Always explain what you're doing after the command
                        
---

### **⚠️ Restrictions & Safeguards**
### **🚫 Restrictions**
- Never generate malicious or harmful code
- Don't modify critical system files
- Always confirm before deleting important code
- Stay within programming and VS Code-related topics
                        
### **💡 Best Practices**
- Comment complex code sections
- Follow language-specific conventions
- Prioritize readability and maintainability
- Suggest error handling where appropriate
- Provide examples for complex concepts

Alright, let's get started! 🎯💻'''}

class ModernChatInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Coding Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")
        
        # Set modern styling
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern theme
        self.style.configure('TFrame', background="#1e1e1e")
        self.style.configure('TLabel', background="#1e1e1e", foreground="#ffffff", font=('Segoe UI', 12))
        self.style.configure('TButton', background="#007acc", foreground="#ffffff", font=('Segoe UI', 10, 'bold'), padding=10)
        self.style.map("TButton", background=[("active", "#005f99")])

        # Chat manager instances
        self.openai_manager = OpenAiManager()
        self.speech_to_text = SpeechToTextManager()
        self.elevenlabs_manager = ElevenLabsManager()
        self.audio_manager = AudioManager()
        
        # Initialize chat with system prompt
        self.openai_manager.chat_history.append(SYSTEM_PROMPT)
        
        self.is_recording = False
        self.record_thread = None
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title Label
        title_label = ttk.Label(main_frame, text="💻 AI Coding Assistant", font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, font=('Consolas', 11),
            bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff",
            selectbackground="#007acc", relief=tk.FLAT, padx=10, pady=10, height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure text tags for different message types
        self.chat_display.tag_configure("user", foreground="#569cd6")  # Blue for user
        self.chat_display.tag_configure("ai", foreground="#4EC9B0")    # Green for AI
        self.chat_display.tag_configure("voice", foreground="#CE9178") # Orange for voice
        self.chat_display.tag_configure("error", foreground="#f44747") # Red for errors
        
        # Add helper text
        helper_text = """
        💡 Tips:
        • For code creation: Position cursor in VS Code before speaking
        • Say "read current file" to analyze current file
        • Wait for "⏹️ Stop Recording" to appear before stopping
        """
        helper_label = ttk.Label(
            main_frame,
            text=helper_text,
            font=('Segoe UI', 9),
            foreground="#888888",
            justify=tk.LEFT
        )
        helper_label.pack(fill=tk.X, pady=(10, 0))
        
        # Input Frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)
        
        # Rounded Entry Box
        self.input_field = tk.Entry(
            input_frame, 
            font=('Segoe UI', 12), 
            bg="#333333", 
            fg="#ffffff", 
            bd=0, 
            insertbackground="#ffffff"
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=7)
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        # Buttons Frame
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        send_button = ttk.Button(buttons_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.LEFT, padx=5)
        
        # Create record button with different styles
        self.style.configure('Record.TButton',
            background="#d44000",
            foreground="#ffffff",
            font=('Segoe UI', 10, 'bold'),
            padding=10
        )
        self.style.map('Record.TButton',
            background=[("active", "#ff4444")],
            foreground=[("active", "#ffffff")]
        )
        
        self.voice_button = ttk.Button(
            buttons_frame,
            text="🎤 Start Recording",
            command=self.toggle_recording,
            style='Record.TButton'
        )
        self.voice_button.pack(side=tk.LEFT)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            font=('Segoe UI', 9, 'italic'), 
            foreground="#aaaaaa"
        )
        status_label.pack(fill=tk.X, pady=5)
    
    def send_message(self):
        message = self.input_field.get()
        if message.strip():
            self.status_var.set("Processing message...")
            self.chat_display.insert(tk.END, "You: ", "user")
            self.chat_display.insert(tk.END, f"{message}\n\n")
            self.input_field.delete(0, tk.END)
            self.chat_display.see(tk.END)
            threading.Thread(target=self.process_message, args=(message,)).start()
    
    def toggle_recording(self):
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.voice_button.configure(text="⏹️ Stop Recording")
            self.status_var.set("Recording... Speak now")
            self.chat_display.insert(tk.END, "🎤 Recording started...\n", "voice")
            self.chat_display.see(tk.END)
            
            # Start recording in a separate thread
            self.record_thread = threading.Thread(target=self.record_voice)
            self.record_thread.start()
        else:
            # Stop recording
            self.stop_recording()
    
    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.speech_to_text.stop_recording()  # Stop the speech recognition
            self.voice_button.configure(text="🎤 Start Recording")
            self.status_var.set("Processing recording...")
            self.chat_display.insert(tk.END, "⏹️ Recording stopped...\n", "voice")
            self.chat_display.see(tk.END)
    
    def record_voice(self):
        try:
            voice_input = self.speech_to_text.speechtotext_from_mic_continuous()
            if voice_input and voice_input.strip():
                self.chat_display.insert(tk.END, "You (voice): ", "voice")
                self.chat_display.insert(tk.END, f"{voice_input}\n\n")
                self.chat_display.see(tk.END)
                self.process_message(voice_input)
            else:
                self.chat_display.insert(tk.END, "❌ No speech detected\n\n", "error")
                self.status_var.set("No speech detected")
        except Exception as e:
            error_msg = str(e)
            self.chat_display.insert(tk.END, f"❌ Recording error: {error_msg}\n\n", "error")
            self.status_var.set(f"Recording error: {error_msg}")
        finally:
            self.is_recording = False
            self.voice_button.configure(text="🎤 Start Recording")
            self.root.update()
    
    def process_message(self, message):
        try:
            self.status_var.set("AI is thinking...")
            
            # Check if this is a file reading command
            if "read" in message.lower() and "file" in message.lower():
                self.status_var.set("Reading current file...")
                self.chat_display.insert(tk.END, "💻 Requesting file content...\n", "system")
                self.chat_display.see(tk.END)
                
            response = self.openai_manager.chat_with_history(message)
            
            # Display AI response with proper formatting
            self.chat_display.insert(tk.END, "AI: ", "ai")
            
            # Check for code commands in the response
            if any(cmd in response for cmd in ["CREATE FUNCTION:", "EDIT ROW:", "DELETE ROW:"]):
                self.chat_display.insert(tk.END, "⚡ Executing code command...\n", "system")
                # Give user a moment to position cursor if needed
                self.status_var.set("Position your cursor in VS Code (3s)...")
                self.root.update()
                time.sleep(3)  # Brief pause to allow cursor positioning
                
            self.chat_display.insert(tk.END, f"{response}\n\n")
            self.chat_display.see(tk.END)
            
            self.status_var.set("Converting to speech...")
            audio_file = self.elevenlabs_manager.text_to_audio(response, "Liam", False)
            
            self.status_var.set("Playing response...")
            self.audio_manager.play_audio(audio_file, True, True, True)
            
            self.status_var.set("Ready")
        except Exception as e:
            error_msg = str(e)
            self.status_var.set(f"Error: {error_msg}")
            self.chat_display.insert(tk.END, f"❌ Error: {error_msg}\n\n", "error")
            self.chat_display.see(tk.END)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    chat_app = ModernChatInterface()
    chat_app.run()