from h2ogpte import H2OGPTE
import json
from preprocessing import parse_file

llm = "gpt-4-1106-preview"
system_prompt = "You are an expert at identifying the key concepts and topics within paragraphs from academic documents, textbooks, and school notes of various formats. Always base your responses on well established academic concepts and topics taught in universities across various domains and fields of study."
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='' # replace with ur own api key so can see when testing
)

output_format = """
Here is an example output:
[\
{"topic": "Topic Modelling", "summary": "Topic modeling is a popular natural language processing technique used to create structured data from a collection of unstructured data. The technique enables businesses to learn the hidden semantic patterns portrayed by a text corpus and automatically identify the topics that exist inside it."}\
{"topic": "In-context Learning", "summary": "In-context learning (ICL) is a technique where task demonstrations are integrated into the prompt in a natural language format. This approach allows pre-trained LLMs to address new tasks without the need forfine-tuning the model."}\
]"""

def extract_topics(context_list: list[str]):
    """
    Returns a list of dictionary objects representing an extracted topic and its summary.

    Args:
    - context_list (list[str]): list of text chunks to extract topics from

    Returns:
    - topics (list[dict]): list of extracted topics and their summaries
    """
    response = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Extract a list of topics the following chunks of text have in common. The first line in each chunk indicates the location of the chunk within the document outline, separated by the symbol >. For each topic identified, provide a concise summary of the topic based on the relevant sections of the document.\n",
        text_context_list=context_list,
        prompt_extract="Format the topics as a list of JSON objects with the following keys: topic, summary." + output_format,
        llm=llm
    )

    if response.error:
        # TODO: Add retry mechanism on error response
        print(f"Error when getting response: {response.error}")

    topics = []
    for record in response.content:
        try:
            topics.extend(json.loads(record))
        except:
            print("Error processing record:", record)
    return topics

def generate_questions(topics: set[str]):
    """
    Returns a list of dictionary objects each with a topic and a question answer pair.

    Args:
    - topics (list[str]): list of topics

    Returns:
    - questions (list[dict]): list of generated questions
    """
    # TODO: Retrieve list of documents from topics
    pass

# # APIs to look at
# client.extract_data()
# client.answer_question()
# client.summarize_document()
# client.create_collection()

# # uploading documents
# upload_id = client.upload()
# client.ingest_uploads(collection_id, upload_id)

# chat_id = client.create_chat_session()
# with client.connect(chat_id) as session:
#     session.query()

def test_extract_topics():
    filepath = 'attention.pdf'
    processed_document = parse_file(filepath)
    extract_topics(processed_document['chunks'])
