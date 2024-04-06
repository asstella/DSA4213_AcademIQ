from neo4j import GraphDatabase
import hashlib
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = "neo4j"

def init():
    cypher_schema = [
        "CREATE CONSTRAINT topicKey IF NOT EXISTS FOR (t:Topic) REQUIRE (t.key) IS UNIQUE;",
        "CREATE CONSTRAINT documentKey IF NOT EXISTS FOR (d:Document) REQUIRE (d.key) IS UNIQUE;",
        "CREATE INDEX ON :Document(filename);",
        "CREATE INDEX ON :Document(summary)",
    ]
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for cypher in cypher_schema:
            session.run(cypher)
    driver.close()

def add_document(document: dict, topics: list[dict]):
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        doc_hash = hashlib.md5(document['file'].encode("utf-8")).hexdigest()
        session.run("MERGE (d:Document {key: $key, filename: $filename}) ON CREATE SET d.key = $key", key=doc_hash, filename=document['file'])
        for topic in topics:
            session.run("MERGE (t:Topic {key: $key, summary: $summary}) ON CREATE SET t.key = $key", key=topic['topic'], summary=topic['summary'])
            session.run("MATCH (d:Document {key: $doc_key}), (t:Topic {key: $topic_key}) MERGE (d)-[:TOPIC]->(t)", doc_key=doc_hash, topic_key=topic['topic'])
    driver.close()

def get_topic_graph():
    data = {'documents': [], 'topics': []}
    driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        documents = session.run("MATCH (d:Document) RETURN d.key AS key, d.filename AS filename, d.summary AS summary")
        for record in documents:
            data["documents"].append({'key': record['key'], 'filename': record.get('filename', ''), 'summary': record.get('summary', '')})
        topics = session.run("MATCH (t:Topic) RETURN t.key AS key")
        for record in topics:
            data["topics"].append(record['key'])
    driver.close()
    return data
