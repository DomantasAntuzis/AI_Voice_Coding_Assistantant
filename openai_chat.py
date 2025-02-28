from openai import OpenAI
import tiktoken
import os
from rich import print
from vscode_api_handler import VSCodeAPIHandler

def num_tokens_from_messages(messages, model='gpt-4o'):
  """Returns the number of tokens used by a list of messages.
  Copied with minor changes from: https://platform.openai.com/docs/guides/chat/managing-tokens """

  encoding_name = None
  if "gpt-4" in model or "gpt-3.5" in model or "o3-" in model:
     encoding_name = "cl100k_base"
# For older models like davinci  
  elif "davinci" in model or "curie" in model or "babbage" in model or "ada" in model:
     encoding_name = "p50k_base"
  else:
    # Default to cl100k_base for unknown models (safest for newer models)
     encoding_name = "cl100k_base"

  try:
      encoding = tiktoken.get_encoding(encoding_name)
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  except Exception:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
      #See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
      

class OpenAiManager:
    
    def __init__(self):
        self.chat_history = [] # Stores the entire conversation
        self.vscode_api = VSCodeAPIHandler()  # Create an instance of VSCodeAPIHandler
        try:
            self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        except TypeError:
            exit("Ooops! You forgot to set OPENAI_API_KEY in your environment!")

    # Asks a question with no chat history
    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        print(f"\n🎤 [bold blue]Received prompt:[/] {prompt}")  # Added color

        # Check that the prompt is under the token context limit
        chat_question = [{"role": "user", "content": prompt}]
        
        if num_tokens_from_messages(chat_question) > 8000:
            print("[red]The length of this chat question is too large for the GPT model[/]")
            return

        print("[yellow]\nAsking ChatGPT a question...[/]")
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=chat_question
            )
            
            # Process the answer
            openai_answer = completion.choices[0].message.content
            print(f"[green]\nAI Response:[/]\n{openai_answer}\n")
            
            print("[bold yellow]🔍 Starting command processing...[/]")  # NEW
            # print(f"[bold blue]First line of response:[/] '{openai_answer.split('\n')[0]}'")  # NEW
            self.process_ai_command(openai_answer)
            return openai_answer
            
        except Exception as e:
            print(f"[red]❌ Error calling OpenAI: {str(e)}[/]")

    
    def process_ai_command(self, ai_response):
        """Process AI response and send commands to VS Code API"""
        
        print("working")
        # Remove debug prints that might interfere with command detection
        lines = ai_response.strip().split('\n')
        if not lines:
            print("[red]❌ Empty response from AI[/]")
            return
            
        first_line = lines[0].strip()
        print(f"[blue]📝 Processing command:[/] '{first_line}'")
        
        # Extract the code content after the command
        code_content = '\n'.join(lines[2:]) if len(lines) > 2 else ""
        
        # Check for commands without any trailing characters
        if first_line == "CREATE FUNCTION:":
            print("[green]✅ Code generation command detected![/]")
            self.vscode_api.insert_generated_code(code_content)
            return True
        elif first_line == "EDIT ROW:":
            print("[green]✅ Edit line command detected![/]")
            self.vscode_api.edit_line()
            return True
        if first_line == "DELETE ROW:":
            print("[green]✅ Delete line command detected![/]")
            # If there's any specific line number or content in code_content, we could process it here
            self.vscode_api.delete_line()
            print("[blue]🗑️ Sending delete command to VS Code[/]")
            return True
        
        print(f"[yellow]ℹ No command detected. First line: '{first_line}'[/]")
        return False

    # Asks a question that includes the full conversation history
    def chat_with_history(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        # Add our prompt into the chat history
        self.chat_history.append({"role": "user", "content": prompt})

        # Check total token limit. Remove old messages as needed
        print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}")
        while num_tokens_from_messages(self.chat_history) > 8000:
            self.chat_history.pop(1) # We skip the 1st message since it's the system message
            print(f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}")

        print("[yellow]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4o",
          messages=self.chat_history
        )

        # Add this answer to our chat history
        self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        
        # Add this line to process commands in chat_with_history
        self.process_ai_command(openai_answer)
        
        return openai_answer
   

if __name__ == '__main__':
    openai_manager = OpenAiManager()
    openai_manager.chat("Sukurk funkciją fetchData su parametru url")  # Example test command

    # CHAT TEST
    chat_without_history = openai_manager.chat("Hey ChatGPT what is 2 + 2? But tell it to me as Yoda")

    # CHAT WITH HISTORY TEST
    FIRST_SYSTEM_MESSAGE = {"role": "system", "content": "Act like you are Captain Jack Sparrow from the Pirates of Carribean movie series!"}
    FIRST_USER_MESSAGE = {"role": "user", "content": "Ahoy there! Who are you, and what are you doing in these parts? Please give me a 1 sentence background on how you got here."}
    openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)
    openai_manager.chat_history.append(FIRST_USER_MESSAGE)

    while True:
        new_prompt = input("\nSakyk komandą AI (pvz., 'Sukurk funkciją', 'Redaguok eilutę', 'Ištrink eilutę'): \n\n")
        openai_manager.chat(new_prompt)  # 🚀 AI processes and executes the command
