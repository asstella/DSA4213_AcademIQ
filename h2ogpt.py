from h2ogpte import H2OGPTE
import json
from preprocessing import parse_file

llm = 'mistral-large-latest' # "mistral-medium" # "mistralai/Mixtral-8x7B-Instruct-v0.1"
system_prompt = "You are an expert at identifying the key concepts and topics within paragraphs \
from academic documents, textbooks, and school notes of various formats. Always base your responses \
on well established academic concepts and topics across various fields of study."

client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-PZx6HXM0jsfJFWTHHfd0KJbVwVlnVSuKcPVwugbWaFk8ZokL' # replace with ur own api key to test
)

extract_topic_output_format = """
[\
{"topic":"Topic 1","summary":"Summary for topic 1."},\
{"topic":"Topic 2","summary":"Summary for topic 2."}\
]"""

topic_tree_format = """
{\
"topics":{\
"Main Topic":{"summary":"Summary of the main topic.","documents":["file1.pdf","file2.pptx"]},\
"Subtopic 1":{"summary":"Summary of Subtopic 1.","documents":["file3.pdf","file4.txt"]},\
"Subtopic 2":{"summary":"Summary of Subtopic 2.","documents":["file5.docx","file6.pdf"]},\
"topic 3":{"summary":"Summary.","documents":["file7.md"]},\
"topic 4":{"summary":"Summary.","documents":["file8.pdf"]}\
},\
"edges":[\
{"source":"Main Topic","target":"Subtopic 1"},\
{"source":"Subtopic 1","target":"topic 3"},\
{"source":"Main Topic","target":"Subtopic 2"},\
{"source":"Subtopic 2","target":"topic 4"},\
{"source":"Subtopic 1","target":"Subtopic 2"}\
]}"""

question_generator_output_format = """
[\
{\
"topic":"Attention Mechanism",\
"question":"What is a primary factor influencing the time required to implement an attention mechanism?",\
"option 1":"The programming language used",\
"option 2":"The complexity of the attention mechanism",\
"option 3":"The size of the dataset",\
"option 4":"The hardware specifications of the computer",\
"answer":"Option 2",\
"explanation":"This is because more complex attention mechanisms, such as those involving multiple layers or intricate attention patterns, require more time to design, code, and integrate into a system compared to simpler attention mechanisms."\
},\
{\
"topic":"Topic",\
"question":"Question",\
"option 1":"Option 1",\
"option 2":"Option 2",\
"option 3":"Option 3",\
"option 4":"Option 4",\
"answer":"Option 4",\
"explanation":"Explanation for answer based on the provided document contents."\
}\
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
        pre_prompt_extract="Extract a list of few broad topics based on the provided contents of a \
document. These topics should be broad concepts in the area of study the document is based on. The \
first line in each chunk indicates the section of the document it is located in, with the symbol \
> indicating nested sections. For each topic identified, provide a clear and concise summary of the topic and do \
not make direct references to the document.",
        text_context_list=context_list,
        prompt_extract="Respond directly with a valid list of compact JSON objects representing a topic \
and its summary in the format specified. Here is an example:\n" + extract_topic_output_format,
        llm=llm
    )
    topics = []
    for res in response.content:
        try:
            start = res.find("[")
            end = res.rfind("]")
            res = res[start:end + 1]
            topics.extend(json.loads(res))
        except json.JSONDecodeError as e:
            print(response.content)
            print(f"Error: {e}")
    return topics


def generate_questions(topics: set[str], context_list: list[str]):
    """
    Returns a list of dictionary objects each with a topic and a question answer pair.

    Args:
    - topics (list[str]): list of topics

    Returns:
    - questions (list[dict]): list of generated questions
    """
    print(f"Generating questions based on {len(context_list)} different documents...")
    response = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="You are given the contents of a set of documents based on this list of topics: " + ', '.join(topics) +
        "Use this to generate a short list of MCQ questions based on the topics given to you. The first line of each document chunk \
indicates which section of the document it is located in, with the symbol > indicating nested sections.",
        text_context_list=context_list,
        prompt_extract="Format the questions as a valid list of compact JSON objects with the attributes: topic, question, option 1, option 2, option 3, option 4, answer, explanation.\
Here is an example: " + question_generator_output_format,
        llm=llm
    )

    questions = []
    for res in response.content:
        try:
            start = res.find("[")
            end = res.rfind("]")
            res = res[start:end + 1]
            questions.extend(json.loads(res))
        except json.JSONDecodeError as e:
            print(response.content)
            print(f"Error: {e}")
    return questions


def test_extract_topics():
    filepath = 'attention.pdf'
    processed_document = parse_file(filepath)
    extract_topics(processed_document['chunks'])


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
