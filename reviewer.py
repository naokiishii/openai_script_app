# python reviewer.py code.py
import json

import openai
from dotenv import dotenv_values
import os
import argparse

PROMPT = """
You will receive a file's contents as text.
Generate a code review for the file. Indicate what changes should be made to improve its style, performance, readability, and maintainability. If there are any reputable libraries that could be introduced to improve the code, suggest them. Be kind and constructive. For each suggested change, include line numbers to which you are referring.
"""


def code_review(file_path, model):
    with open(file_path, 'r') as file:
        content = file.read()
    generated_code_review = make_code_review_request(content, model)
    print(generated_code_review)


def make_code_review_request(file_content, model):
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f"Code review the following file: {file_content}"}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description='Simple code reviewer for a file')
    parser.add_argument('file')
    parser.add_argument('--model', default='gpt-3.5-turbo')
    args = parser.parse_args()
    code_review(args.file, args.model)


if __name__ == '__main__':
    config = dotenv_values(".env")
    os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]

    client = openai.OpenAI()
    main()

