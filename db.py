from neo4j import GraphDatabase
import hashlib
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.get_env("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = "neo4j"

def init():
    cypher_schema = [
        "CREATE CONSTRAINT topicKey IF NOT EXISTS FOR (t:Topic) REQUIRE (t.key) IS UNIQUE;",
        "CREATE CONSTRAINT documentKey IF NOT EXISTS FOR (d:Document) REQUIRE (d.key) IS UNIQUE;",
        "CREATE CONSTRAINT chunkKey IF NOT EXISTS FOR (c:Chunk) REQUIRE (c.key) IS UNIQUE;",
        "CALL db.index.vector.createNodeIndex('chunkVector', 'Chunk', 'embedding', 1536, 'COSINE');" # assuming 1536 is the dimension of the embeddings, change if necessary
    ]
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for cypher in cypher_schema:
            session.run(cypher)
    driver.close()

def add_document(document: dict, topics: list[str]):
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        doc_hash = hashlib.md5(document['file'].encode("utf-8")).hexdigest()

        # Create Document node
        session.run("MERGE (d:Document {key: $key}) ON CREATE SET d.key = $key", key=doc_hash)

        # Link Document to Topics
        for topic_key in topics:
            session.run("MERGE (t:Topic {key: $key}) ON CREATE SET t.key = $key", key=topic_key)
            session.run("MATCH (d:Document {key: $doc_key}), (t:Topic {key: $topic_key}) MERGE (d)-[:TOPIC]->(t)", doc_key=doc_hash, topic_key=topic_key)

        # Create Chunk nodes and link them to the Document
        for chunk in document['chunks']:
            chunk_key = hashlib.md5(chunk['text'].encode("utf-8")).hexdigest()
            session.run("MERGE (c:Chunk {key: $key}) ON CREATE SET c.text = $text, c.embedding = $embedding", key=chunk_key, text=chunk['text'], embedding=chunk['embedding'])
            session.run("MATCH (d:Document {key: $doc_key}), (c:Chunk {key: $chunk_key}) MERGE (d)-[:CONTAINS]->(c)", doc_key=doc_hash, chunk_key=chunk_key)

    driver.close()

def get_topic_chunks(topic_key: str):
    relevant_chunks = []
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        # Directly fetch documents tagged with the topic and their chunks
        result = session.run("MATCH (t:Topic {key: $key})<-[:TOPIC]-(d:Document)-[:CONTAINS]->(c:Chunk) RETURN c.text, c.embedding;", key=topic_key)
        for record in result.values():
            relevant_chunks.append(record)

    driver.close()
    return relevant_chunks

# Test code
# if __name__ == "__main__":
#     # Initialize the database schema
#     init()

#     # Mock document data
#     document = {
#         'file': 'file.pdf',
#         'chunks': [
#             {'text': 'This is the first chunk of text.', 'embedding': [0.1, 0.2, 0.3]},
#             {'text': 'This is the second chunk of text.', 'embedding': [0.4, 0.5, 0.6]},
#             {'text': 'This is the third chunk of text.', 'embedding': [0.7, 0.8, 0.9]}
#         ]
#     }

#     # Assume 'topic1' is a pre-existing topic in the database. 
#     # In a real scenario, you would also have functions to add topics and subtopics.
#     topics = ['topic1']

#     # Add the document to the graph
#     add_document(document, topics)

#     # Retrieve chunks for 'topic1'
#     chunks = get_topic_chunks('topic1')
#     print("Retrieved chunks for topic 'topic1':")
#     for chunk in chunks:
#         print(chunk)
