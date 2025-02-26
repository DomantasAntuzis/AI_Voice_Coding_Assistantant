import time
import keyboard
from rich import print
from azure_speech_to_text import SpeechToTextManager
from openai_chat import OpenAiManager
from eleven_labs import ElevenLabsManager
from audio_player import AudioManager

ELEVENLABS_VOICE = "Liam" # Replace this with the name of whatever voice you have created on Elevenlabs

BACKUP_FILE = "ChatHistoryBackup.txt"

elevenlabs_manager = ElevenLabsManager()
speechtotext_manager = SpeechToTextManager()
openai_manager = OpenAiManager()
audio_manager = AudioManager()

FIRST_SYSTEM_MESSAGE = {"role": "system", "content": '''
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
3. **Include the code** after your explanation
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

✅ CORRECT FORMAT EXAMPLE:
CREATE FUNCTION:
Here's a function that generates random names...
[code follows]

❌ INCORRECT FORMAT EXAMPLES:
- "Let me create a function..."
- "### Command: Create a function"
- "Here's the function you requested..."

Always start with the exact command phrase, then follow with your explanation and code.
                        
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

Alright, let's get started! 🎯💻'''
}

openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)

print("[green]Starting the loop, press F4 to begin")
while True:
    # Wait until user presses "f4" key
    if keyboard.read_key() != "f4":
        time.sleep(0.1)
        continue

    print("[green]User pressed F4 key! Now listening to your microphone:")

    # Get question from mic
    mic_result = speechtotext_manager.speechtotext_from_mic_continuous()
    
    if mic_result == '':
        print("[red]Did not receive any input from your microphone!")
        continue

    # Send question to OpenAi
    openai_result = openai_manager.chat_with_history(mic_result)
    
    # Write the results to txt file as a backup
    with open(BACKUP_FILE, "w", encoding="utf-8") as file:
        file.write(str(openai_manager.chat_history))

    # Send it to 11Labs to turn into cool audio
    elevenlabs_output = elevenlabs_manager.text_to_audio(openai_result, ELEVENLABS_VOICE, False)

    # Play the mp3 file
    audio_manager.play_audio(elevenlabs_output, True, True, True)

    print("[green]\n!!!!!!!\nFINISHED PROCESSING DIALOGUE.\nREADY FOR NEXT INPUT\n!!!!!!!\n")
    
