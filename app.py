import os
import json
import openai
from flask import Flask, render_template, request
from dotenv import dotenv_values

config = dotenv_values('.env')
os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
client = openai.OpenAI()

app = Flask(__name__,
            template_folder='templates',
            static_url_path='',
            static_folder='static',
            )


def get_colors(msg):
  prompt = f"""
  You are a color palette generating assistant that responds to text prompts for color palettes.
  You should generate color palettes that fit the theme, mood, or instructions in the prompt.
  The palettes should be between 2 and 8.

  Desired Format: a JSON format of single array of hexadecimal color codes without explanations that can be parsed by python's json.loads()
  Text: {msg}

  Result:
  """

  response = client.completions.create(
      prompt=prompt,
      model="gpt-3.5-turbo-instruct",
      max_tokens=200
  )

  print(response.model_dump_json(indent=2))

  return json.loads(response.choices[0].text)

@app.route("/palette", methods=["POST"])
def prompt_to_palette():
    app.logger.info("Hit the palette endpoint")
    query = request.form.get("query")
    app.logger.info(query)
    colors = get_colors(query)
    app.logger.info(colors)
    return {"colors": colors}


@app.route("/")
def index():
    #response = openai.completions.create(
    #    model="gpt-3.5-turbo-instruct",
    #    prompt="Give me a funny word: "
    #)
    #return response.choices[0].text
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
