import re
import os
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from llmsherpa.readers import LayoutPDFReader

def parse_file(filepath):
    # print(f'Received Files: {filepath}')
    all_text = ''
    # for filepath in filepaths:
    reader = LayoutPDFReader("http://nlm_ingestor:5001/api/parseDocument?renderFormat=all")
    documents = reader.read_pdf(filepath)
    document_text = '\n'.join([c.to_text() for c in documents.chunks()]) # print every paragraph, header, table etc.
    all_text += document_text + "\n" #add document text to accumulated string
    return all_text

#Function to preprocess text
# def preprocess_text(text):
#     # Convert to lowercase
#     text = text.lower()

#     # Remove punctuation and non-alphanumeric characters
#     text = re.sub(r'[^a-zA-Z-2-9\s]', '', text)

#     # Tokenization
#     tokens = word_tokenize(text)

#     # Remove stopwords
#     stop_words = set(stopwords.words('english'))
#     tokens = [word for word in tokens if word not in stop_words]

#     # Lemmatization
#     lemmatizer = WordNetLemmatizer()
#     tokens = [lemmatizer.lemmatize(token) for token in tokens]

#     return tokens

#Function to preprocess input document
def preprocess_document(filepath):
    uploaded_text = parse_file(filepath)
    # processed_text = preprocess_text(uploaded_text)
    filename = os.path.basename(filepath) #retrieve filename

    processed_document = {}

    processed_document["file"] = filename
    processed_document["text"] = uploaded_text
    # processed_document["processed"] = processed_text

    # print(f"Filename: {processed_document['Filename']}")
    # print(f"Original Text: {processed_document['Original_text']}")
    # print(f"Processed Text: {processed_document['Processed_text']}")

    return processed_document
