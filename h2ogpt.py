from h2ogpte import H2OGPTE
import re

client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-rWllOURibnB1EzBeMCvWstytoiaDv2xRNa1QilqFPzNVYvkM',
)

def text_summariser(text_content: str):
    summary = client.summarize_content(
        pre_prompt_summary="Summarize the content below.\n",
        text_context_list=[text_content],
        prompt_summary="summarize the above into a couple of paragraphs and give me a topic for each short paragraph."
    )
    return summary.content


def get_topic_summary(text_document: str):
    with open(text_document, "r", encoding="utf-8") as file:
        text_content = file.read()
    summary = text_summariser(text_content)
    lines = summary.split('\n')

    titles = []
    paragraphs = []
    for line in lines:
        if line.startswith('Topic:'):
            titles.append(line.strip())
        else:
            paragraphs.append(line.strip())

    clean_paragraphs = [string.strip() for string in paragraphs if string.strip()]
    return titles, clean_paragraphs

## test

# text_document = "processedtext.txt"

# print("Titles:")
# for title in titles:
#     print(title)

# # Print all paragraphs
# print("\nParagraphs:")
# for paragraph in clean_paragraphs:
#     print(paragraph)