from __future__ import division

import os
import random
import re
import time
from dataclasses import dataclass
from typing import Dict, List

import openai
from dotenv import dotenv_values
import requests
import tiktoken
from utilities import (
    memoize_to_file,
    num_tokens_from_messages,
    split_text_into_sections,
    summarization_prompt_messages,
)

config = dotenv_values(".env")
os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
client = openai.OpenAI()

actual_tokens = 0


def gpt_summarize(text: str, target_summary_size: int) -> str:
    global actual_tokens
    # Otherwise, we can just summarize the text directly
    tries = 0
    while True:
        try:
            tries += 1
            result = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=summarization_prompt_messages(text, target_summary_size),
            )
            actual_tokens += result.usage.total_tokens
            return "[[[" + result.choices[0].message.content + "]]]"
        except (openai.APIConnectionError, openai.APIError, openai.RateLimitError) as e:
            if tries >= MAX_ATTEMPTS:
                print(f"OpenAI exception after {MAX_ATTEMPTS} tries. Aborting. {e}")
                raise e
            if hasattr(e, "should_retry") and not e.should_retry:
                print(f"OpenAI exception with should_retry false. Aborting. {e}")
                raise e
            else:
                print(f"Summarize failed (Try {tries} of {MAX_ATTEMPTS}). {e}")
                random_wait = (
                    random.random() * 4.0 + 1.0
                )  # Wait between 1 and 5 seconds
                random_wait = (
                    random_wait * tries
                )  # Scale that up by the number of tries (more tries, longer wait)
                time.sleep(random_wait * tries)


# Using repr allows us to use this is in our memoization function.
# Specifying frozen=True causes python to generate a __hash__ and __eq__ function for us.


@dataclass(frozen=True, repr=True)
class SummarizationParameters:
    # Pass around our parameters for summarization in a hashable dataclass (like a namedtuple)
    target_summary_size: int
    summary_input_size: int


def summarization_token_parameters(
    target_summary_size: int, model_context_size: int
) -> SummarizationParameters:
    """
    Compute the number of tokens that should be used for the context window, the target summary, and the base prompt.
    """
    base_prompt_size = num_tokens_from_messages(
        summarization_prompt_messages("", target_summary_size), model=model_name
    )
    summary_input_size = model_context_size - (base_prompt_size + target_summary_size)
    return SummarizationParameters(
        target_summary_size=target_summary_size,
        summary_input_size=summary_input_size,
    )


@memoize_to_file(cache_file="cache.json")
def summarize(
    text: str,
    token_quantities: SummarizationParameters,
    division_point: str,
    model_name: str,
) -> str:
    # Shorten text for our console logging
    text_to_print = re.sub(r" +\|\n\|\t", " ", text).replace("\n", "")
    print(
        f"\nSummarizing {len(enc.encode(text))}-token text: {text_to_print[:60]}{'...' if len(text_to_print) > 60 else ''}"
    )

    if len(enc.encode(text)) <= token_quantities.target_summary_size:
        # If the text is already short enough, just return it
        return text
    elif len(enc.encode(text)) <= token_quantities.summary_input_size:
        summary = gpt_summarize(text, token_quantities.target_summary_size)
        print(
            f"Summarized {len(enc.encode(text))}-token text into {len(enc.encode(summary))}-token summary: {summary[:250]}{'...' if len(summary) > 250 else ''}"
        )
        return summary
    else:
        # The text is too long, split it into sections and summarize each section
        split_input = split_text_into_sections(
            text, token_quantities.summary_input_size, division_point, model_name
        )

        summaries = [
            summarize(x, token_quantities, division_point, model_name)
            for x in split_input
        ]

        return summarize(
            "\n\n".join(summaries), token_quantities, division_point, model_name
        )


@memoize_to_file(cache_file="cache.json")
def synthesize_summaries(summaries: List[str], model: str) -> str:
    """
    Use a more powerful GPT model to synthesize the summaries into a single summary.
    """
    print(f"Synthesizing {len(summaries)} summaries into a single summary.")

    summaries_joined = ""
    for i, summary in enumerate(summaries):
        summaries_joined += f"Summary {i + 1}: {summary}\n\n"

    messages = [
        {
            "role": "user",
            "content": f"""
A less powerful GPT model generated {len(summaries)} summaries of a book.

Because of the way that the summaries are generated, they may not be perfect. Please review them
and synthesize them into a single more detailed summary that you think is best.

The summaries are as follows: {summaries_joined}
""".strip(),
        },
    ]

    # Check that the summaries are short enough to be synthesized
    assert num_tokens_from_messages(messages, model=model_name) <= 8192
    print(messages)

    result = openai.chat.completions.create(model=model, messages=messages)
    return result.choices[0].message.content


model_name = "gpt-4o-mini"
enc = tiktoken.encoding_for_model(model_name)


# Great Gatsby
# response = requests.get("https://www.gutenberg.org/cache/epub/64317/pg64317.txt")

# PETER PAN
#response = requests.get("https://www.gutenberg.org/files/16/16-0.txt")

# Metamorphosis
# response = requests.get("https://www.gutenberg.org/files/5200/5200-0.txt")

#assert response.status_code == 200
book_complete_text = """
Produced by: Duncan Research

*** START OF THE PROJECT GUTENBERG EBOOK PETER PAN ***




Peter Pan

[PETER AND WENDY]

by J. M. Barrie [James Matthew Barrie]

A Millennium Fulcrum Edition produced in 1991 by Duncan Research. Note
that while a copyright was initially claimed for the labor involved in
digitization, that copyright claim is not consistent with current
copyright requirements. This text, which matches the 1911 original
publication, is in the public domain in the US.


Contents

 Chapter I. PETER BREAKS THROUGH
 Chapter II. THE SHADOW
 Chapter III. COME AWAY, COME AWAY!
 Chapter IV. THE FLIGHT
 Chapter V. THE ISLAND COME TRUE
 Chapter VI. THE LITTLE HOUSE
 Chapter VII. THE HOME UNDER THE GROUND
 Chapter VIII. THE MERMAIDS’ LAGOON
 Chapter IX. THE NEVER BIRD
 Chapter X. THE HAPPY HOME
 Chapter XI. WENDY’S STORY
 Chapter XII. THE CHILDREN ARE CARRIED OFF
 Chapter XIII. DO YOU BELIEVE IN FAIRIES?
 Chapter XIV. THE PIRATE SHIP
 Chapter XV. “HOOK OR ME THIS TIME”
 Chapter XVI. THE RETURN HOME
 Chapter XVII. WHEN WENDY GREW UP




Chapter I.
PETER BREAKS THROUGH


All children, except one, grow up. They soon know that they will grow
up, and the way Wendy knew was this. One day when she was two years old
she was playing in a garden, and she plucked another flower and ran
with it to her mother. I suppose she must have looked rather
delightful, for Mrs. Darling put her hand to her heart and cried, “Oh,
why can’t you remain like this for ever!” This was all that passed
between them on the subject, but henceforth Wendy knew that she must
grow up. You always know after you are two. Two is the beginning of the
end.

Of course they lived at 14, and until Wendy came her mother was the
chief one. She was a lovely lady, with a romantic mind and such a sweet
mocking mouth. Her romantic mind was like the tiny boxes, one within
the other, that come from the puzzling East, however many you discover
there is always one more; and her sweet mocking mouth had one kiss on
it that Wendy could never get, though there it was, perfectly
conspicuous in the right-hand corner.
"""#response.text

# We replace the carriage return character. Because why do these exist in the first place.
book_complete_text = book_complete_text.replace("\r", "")

# We remove Project Gutenberg's header and footer
# Project Gutenberg's header is always the same, so we can just remove it:
split = re.split(r"\*\*\* .+ \*\*\*", book_complete_text)
print(split[0])

print("Divided into parts of length:", [len(s) for s in split])

# We select the middle of the split, which is the actual book
book = split[1]

print(f"Text contains {len(enc.encode(book))} tokens")
MAX_ATTEMPTS = 3

num_tokens = len(enc.encode(book))
cost_per_token = 0.001 / 1000
print(
    f"As of Q1 2024, the approximate price of this summary will somewhere be on the order of: ${num_tokens * cost_per_token:.2f}"
)

division_point = "."

# summary = summarize(
#     book,
#     summarization_token_parameters(target_summary_size=1000, model_context_size=4097),
#     division_point,
#     model_name
# ).replace("[[[", "").replace("]]]", "")

# print(summary)


summaries: Dict[int, str] = {}
target_summary_sizes = [500, 750, 1000]
for target_summary_size in target_summary_sizes:
    actual_tokens = 0
    summaries[target_summary_size] = (
        summarize(
            book,
            summarization_token_parameters(
                target_summary_size=target_summary_size, model_context_size=16000
            ),
            division_point,
            model_name,
        )
        .replace("[[[", "")
        .replace("]]]", "")
    )
print(summaries)


print(synthesize_summaries(list(summaries.values()), "gpt-4"))
