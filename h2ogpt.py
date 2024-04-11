from h2ogpte import H2OGPTE
import json
from preprocessing import parse_file

llm = "gpt-4-1106-preview"
system_prompt = "You are an expert at identifying the key concepts and topics within paragraphs from academic documents, textbooks, and school notes of various formats. Always base your responses on well established academic concepts and topics taught in universities across various domains and fields of study."
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-a25XDdP6vOOFGxYO1kmrNmVHrQpuGTqLx7pbJlgUqIhSadCI' # replace with ur own api key so can see when testing
)


extract_topic_output_format = """
Here is an example output:
[\
{"topic": "Topic Modelling", "summary": "Topic modeling is a popular natural language processing technique used to create structured data from a collection of unstructured data. The technique enables businesses to learn the hidden semantic patterns portrayed by a text corpus and automatically identify the topics that exist inside it."}\
{"topic": "In-context Learning", "summary": "In-context learning (ICL) is a technique where task demonstrations are integrated into the prompt in a natural language format. This approach allows pre-trained LLMs to address new tasks without the need forfine-tuning the model."}\
]"""

summary_output_format = """
Here is an example output:
[\
{"main_summary": "Topic modeling is a popular natural language processing technique used to create structured data from a collection of unstructured data. The technique enables businesses to learn the hidden semantic patterns portrayed by a text corpus and automatically identify the topics that exist inside it."}\
] """

question_generator_output_format = """
Here is an example output:
[    
    {
        "topic": "Attention Mechanism",
        "question": "What is a primary factor influencing the time required to implement an attention mechanism?",
        "option 1": "The programming ladnguage used",
        "option 2": "The complexity of the attention mechanism",
        "option 3": "The size of the dataset",
        "option 4": "The hardware specifications of the computer",
        "correct option": "Option 2",
        "explanation": "This is because more complex attention mechanisms, such as those involving multiple layers or intricate attention patterns, require more time to design, code, and integrate into a system compared to simpler attention mechanisms."
    }]
"""

def extract_topics(context_list: list[str]):
    """
    Returns a list of dictionary objects representing an extracted topic and its summary.

    Args:
    - context_list (list[str]): list of text chunks to extract topics from

    Returns:
    - topics (list[dict]): list of extracted topics and their summaries
    """
    response1 = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Extract a list of topics the following chunks of text have in common. The first line in each chunk indicates the location of the chunk within the document outline, separated by the symbol >. For each topic identified, provide a clear and coherent summary of the topic based on the relevant sections of the document.\n",
        text_context_list=context_list,
        prompt_extract="Format the topics as a list of JSON objects with the following keys: topic, summary." + extract_topic_output_format,
        llm=llm
    )

    # double prompt to combine similar topics
    response2 = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Given the extracted topics and summaries, combine any overlapping topics. If they are not overlapping, do not change it.\n",
        text_context_list=response1.content,
        prompt_extract="Format the topics as a list of JSON objects with the following keys: topic, summary." + extract_topic_output_format,
        llm=llm
    )

    topics = []
    for record in response2.content:
        try:
            topics.extend(json.loads(record))
        except:
            print("Error processing record:", record)
    print(topics)
    return topics

def summary(context_list: list[str]):
    """
    Returns a summary
    """
    response = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Extract the main summary.\n",
        text_context_list=context_list,
        prompt_extract="Format the topics as a list of JSON object with the following key: summary. There should only be one summary" + summary_output_format,
        llm=llm
    )

    topics = []
    for record in response.content:
        try:
            topics.extend(json.loads(record))
        except:
            print("Error processing record:", record)
    # print(topics)
    return topics



def generate_questions(topics: set[str], context_list: list[str]):
    """
    Returns a list of dictionary objects each with a topic and a question answer pair.

    Args:
    - topics (list[str]): list of topics

    Returns:
    - questions (list[dict]): list of generated questions
    """

    response = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Using the text, generate a question for each topic in this list: " + str(topics),
        text_context_list=context_list,
        prompt_extract="Format the questions as a list of JSON objects: topic, question, option 1, option 2, option 3, option 4, correct option, explanation." + question_generator_output_format,
        llm=llm
    )

    questions = []
    for record in response.content:
        try:
            questions.extend(json.loads(record))
        except:
            print("Error processing record:", record)
    print(questions)
    return questions

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

def test_summary_topics():
    filepath = 'attention.pdf'
    processed_document = parse_file(filepath)
    summary(processed_document['chunks'])

def test_question_generation():
    filepath = 'attention.pdf'
    processed_document = parse_file(filepath)
    generate_questions(topics = [
        "Transformer Model Architecture",
        "Self-Attention Mechanism",
        "Multi-Head Attention",
        "Positional Encoding",
        "Model Generalization and Applications",
        "Computational Efficiency",
        "State-of-the-Art Performance"],
        context_list= processed_document['chunks'])

# test_generate()
#test_invalid_file()
#test_summary_topics()
# test_extract_topics()
# test_question_generation()
