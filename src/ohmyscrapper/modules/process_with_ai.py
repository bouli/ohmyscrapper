import ohmyscrapper.models.urls_manager as urls_manager
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
import random
import time
import os
import yaml

load_dotenv()


def process_with_ai(recursive=True):
    prompt = _get_prompt()
    if not prompt:
        return

    url_type = "linkedin_post"
    df = urls_manager.get_urls_by_url_type_for_ai_process(url_type)

    if len(df) == 0:
        print("no urls to process with ai anymore")
        return
    texts = ""
    for index, row in df.iterrows():
        texts = (
            texts
            + f"""
        <texto>
        <id>{str(row['id'])}</id>
        {row['description']}
        </texto>
        """
        )
    if texts == "":
        print("no urls to process")
        return

    print("starting...")
    print("prompt:", prompt["name"])
    print("model:", prompt["model"])
    print("description:", prompt["description"])
    prompt["instrusctions"] = prompt["instrusctions"].replace("{ohmyscrapper_texts}", texts)

    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client()
    response = client.models.generate_content(model=prompt["model"], contents=prompt["instrusctions"])
    response = str(response.text)
    urls_manager.add_ai_log(instructions=prompt["instrusctions"], response=response, model=prompt["model"])
    print(response)
    print("^^^^^^")
    soup = BeautifulSoup(response, "html.parser")
    for vaga in soup.find_all(prompt["xml-item"]):

        url = urls_manager.get_url_by_id(vaga.find("id").text)
        if len(url) > 0:
            url = url.iloc[0]
        # TODO: make it dynamic
        h1 = vaga.find("titulo").text
        if (
            vaga.find("contratante").text != "desconhecido"
            and vaga.find("contratante").text != ""
        ):
            h1 = h1 + " - " + vaga.find("contratante").text
        if url["description_links"] > 1 and vaga.find("id").text != "":
            urls_manager.set_url_h1(vaga.find("url").text, h1)
            urls_manager.set_url_ai_processed_by_url(vaga.find("url").text)

            print("-- child updated -- ", vaga.find("url").text, h1)
        elif url["description_links"] <= 1:
            urls_manager.set_url_h1_by_id(vaga.find("id").text, h1)
            urls_manager.set_url_ai_processed_by_id(vaga.find("id").text)
            print("-- parent updated -- ", url["url"], h1)
        else:
            print("-- not updated -- ", url["url"], h1)

    print("ending...")

    if recursive:
        wait = random.randint(1, 3)
        print("sleeping for", wait, "seconds before next round")
        time.sleep(wait)
        process_with_ai(recursive=recursive)

    return

def _get_prompt():
    prompts_path = "prompts"
    default_prompt = """---
model: "gemini-2.5-flash"
name: "default-prompt"
description: "Put here your prompt description."
xml-item: "position"
---
Process with AI this prompt: {ohmyscrapper_texts}
"""
    if not os.path.exists(prompts_path):
        os.mkdir(prompts_path)

        open(f"{prompts_path}/prompt.md", "w").write(default_prompt)
        print(f"You didn't have a prompt file. One was created in the /{prompts_path} folder. You can change it there.")
        return False

    prompt_files = os.listdir(prompts_path)
    if len(prompt_files) == 0:
        open(f"{prompts_path}/prompt.md", "w").write(default_prompt)
        print(f"You didn't have a prompt file. One was created in the /{prompts_path} folder. You can change it there.")
        return False

    if len(prompt_files) == 1:
        prompt = _parse_prompt(prompts_path, prompt_files[0])
    else:
        print("Choose a prompt:")
        prompts = {}
        for index, file in enumerate(prompt_files):
            prompts[index] = _parse_prompt(prompts_path, file)
            print(index, ":", prompts[index]['name'])
        input_prompt = input("Type the number of the prompt you want to use or 'q' to quit: ")
        if input_prompt == "q":
            return False
        try:
            prompt = prompts[int(input_prompt)]
        except:
            print("! Invalid prompt\n")
            prompt = _get_prompt()

    return prompt

def _parse_prompt(prompts_path, prompt_file):
    prompt = {}
    raw_prompt = open(f"{prompts_path}/{prompt_file}", "r").read().split("---")
    prompt = yaml.safe_load(raw_prompt[1])
    prompt["instrusctions"] = raw_prompt[2].strip()

    return prompt
# TODO: Separate gemini from basic function
def _process_with_gemini(model, instructions):
    response = """"""
    return response


def _process_with_openai(model, instructions):
    # import os
    # from openai import OpenAI

    # client = OpenAI(
    #    # This is the default and can be omitted
    #    api_key=os.environ.get("OPENAI_API_KEY"),
    # )

    # response = client.responses.create(
    #    model="gpt-4o",
    #    instructions="You are a coding assistant that talks like a pirate.",
    #    input="How do I check if a Python object is an instance of a class?",
    # )

    # print(response.output_text)

    response = """"""
    return response
