import os
from llmsherpa.readers import LayoutPDFReader, Document
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
nlm_host = os.getenv('NLM_INGESTOR', 'localhost')
ingestor_url = f"http://{nlm_host}:5001/api/parseDocument?renderFormat=all"

def parse_file(filepath: str):
    """
    A function that parses a file based on its file type and returns a processed document.

    Args:
    - filepath: a string representing the path to the file to be parsed

    Returns:
    - processed_document: dictionary representing the processed document
        - file: str, the filename
        - chunks: list of str, the text chunks extracted from the document
    """
    filename = os.path.basename(filepath) # retrieve filename
    if filename.endswith('.pdf'):
        reader = LayoutPDFReader(ingestor_url)
        document = reader.read_pdf(filepath)
    elif filename.endswith('.docx') or filename.endswith('.pptx') or filename.endswith('.md') or filename.endswith('.txt'):
        with open(filepath, 'rb') as f:
            filedata = f.read()
            files = { 'file': (filename, filedata, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') }
        response = requests.post(ingestor_url, files=files)
        if response.status_code == 200:
            document = response.json()
            document = Document(document['return_dict']['result']['blocks'])
        else:
            print(f'Request failed with status code {response.status_code}')
    else:
        print('Unsupported file type')
        return

    processed_document = {}
    processed_document["file"] = filename
    # document is split into chunks based on its outline. when using to_context_text,
    # the first line in each chunk indicates the section the chunk belongs to
    # eg. "root node > parent section > chunk section"
    processed_document['chunks'] = [c.to_context_text() for c in document.chunks()]
    # TODO: Split section header and raw chunk text into separate columns
    return processed_document

def test_parse_file():
    filepath = 'attention.pdf'
    processed_document = parse_file(filepath)
    logger.info(processed_document['file'])
    logger.info('\n\n'.join(processed_document['chunks']))
