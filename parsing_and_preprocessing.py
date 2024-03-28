import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
import numpy as np
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

from llmsherpa.readers import LayoutPDFReader

def parse_file(filepaths: list[str]):
    print(f'Received Files: {filepaths}')
    all_text = ''
    for filepath in filepaths:
        reader = LayoutPDFReader("http://localhost:5001/api/parseDocument?renderFormat=all")
        documents = reader.read_pdf(filepath)
        document_text = '\n'.join([c.to_text() for c in documents.chunks()]) # print every paragraph, header, table etc.
        all_text += document_text + "\n" #add document text to accumulated string
    return all_text

# test code
# dir = os.getcwd()
# file = os.path.join(dir, "test.pdf")
# uploaded_text = parse_file([file])
# print(uploaded_text)

#Function to preprocess text
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation and non-alphanumeric characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Tokenization
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    return tokens

#Function to preprocess input document
def preprocess_document(file_path):
    uploaded_text = parse_file([file_path])
    processed_text = preprocess_text(uploaded_text)
    filename = os.path.basename(file_path) #retrieve filename

    processed_document = {}

    processed_document["Filename"] = filename
    processed_document["Original_text"] = uploaded_text
    processed_document["Processed_text"] = processed_text

    # print(f"Filename: {processed_document['Filename']}")
    # print(f"Original Text: {processed_document['Original_text']}")
    # print(f"Processed Text: {processed_document['Processed_text']}")

    return processed_document

# test code
# processed = preprocess_document(uploaded_text)
# print(processed)

# Save processed text into a text file
def value_to_file(dictionary, key, filename):
    if key in dictionary:
        value = str(dictionary[key]) #convert list value to string
        with open(filename, 'w') as file:
            file.write(value)
            print(f"Processed text successfully written to '{filename}'.")
    else:
        print(f"Processed text not found in dictionary.")

# test code
# value_to_file(processed, "Processed_text", "processedtext.txt")