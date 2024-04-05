from h2ogpte import H2OGPTE

client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-rWllOURibnB1EzBeMCvWstytoiaDv2xRNa1QilqFPzNVYvkM',
)
# give fixed format to ensure that the prompt output always returns in the format we read it
output_format = "Example output\n Topic: Topic Modelling\n Summary: Topic modeling is a popular natural language processing \
                technique used to create structured data from a collection of unstructured data. In other words, the technique enables businesses \
                to learn the hidden semantic patterns portrayed by a text corpus and automatically identify the topics that exist inside it.\n\
                Topic: In-context Learning\n Summary: In-context learning (ICL) is a technique where task demonstrations are integrated \
                into the prompt in a natural language format. This approach allows pre-trained LLMs to address new tasks without fine-tuning the model."

def text_summariser(text_content: str):
    summary = client.summarize_content(
        pre_prompt_summary="Summarize the content below.\n",
        text_context_list=[text_content],
        prompt_summary=f"summarize the above into a couple of paragraphs and give me a topic for each short paragraph.\n {output_format}"
    )
    return summary.content

def get_topic_summary(text_document: str):
    summary = text_summariser(text_document)
    lines = summary.split('\n')

    topics = []
    paragraphs = []
    for line in lines:
        if line.startswith('Topic'):
            topics.append(line.split(":")[-1].strip())
        else:
            paragraphs.append(line.strip())

    clean_paragraphs = [string.strip() for string in paragraphs if string.strip()]
    return topics, '\n\n'.join(clean_paragraphs)

## test

# text_document = "processedtext.txt"

# print("Titles:")
# for title in titles:
#     print(title)

# # Print all paragraphs
# print("\nParagraphs:")
# for paragraph in clean_paragraphs:
#     print(paragraph)