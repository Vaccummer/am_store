from zhipuai import ZhipuAI
import os
import argparse
import sys
class Chat:
    def __init__(self, api_key:str, model_name:str="glm-4"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = ZhipuAI(api_key=self.api_key)
        self.dialog = [{"role":"user", "content":"Hello, ZHIPU AI, you must answer my questions in Chinese enven though I ask in English."},
                       {"role":"assistant", "content":"好的，不管您用什么语言提问，您的任何问题我都会用中文回答。"}]
    def chat(self):
            while True:
                prompt_f = input("You: ")
                if prompt_f == "exit()":
                    break
                self.dialog.append({"role": "user", "content": prompt_f})
                response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.dialog,
                )
                answer = response.choices[0].message.content
                print(f"{self.model_name}: {answer}")
                self.dialog.append({"role": "assistant", "content": answer})
    def ask(self, prompt:str):
        dialog_f = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
        model=self.model_name,
        messages=dialog_f,
        )
        answer = response.choices[0].message.content
        print(f"{self.model_name}: {answer}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Chat Programm",formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--chat', help="Start a chat session", action="store_true",default=False)
    parser.add_argument('-m', "--model", help="Model name", default="glm-4")
    parser.add_argument('prompt', nargs='?', help="prompt", default="")
    args= parser.parse_args()
    server_f = Chat(api_key="316b438ba6efe02778b874ed5d5f0a52.Yjj8ybeYhidJe8ja",
                    model_name=args.model)
    if args.prompt == [""]:
        print("No prompt provided.")
        sys.exit(0)
    if args.chat:
        server_f.chat()
    else:
        server_f.ask(args.prompt) 