import json
from neo4j import GraphDatabase
from h2ogpt import topic_tree_format
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = "neo4j"

driver = GraphDatabase.driver(NEO4J_URI, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))

def init_db():
    cypher_schema = [
        "CREATE CONSTRAINT topicUnique IF NOT EXISTS FOR (t:Topic) REQUIRE (t.name) IS UNIQUE;",
        "CREATE CONSTRAINT documentUnique IF NOT EXISTS FOR (d:Document) REQUIRE (d.name) IS UNIQUE;",
    ]
    with driver.session() as session:
        for cypher in cypher_schema:
            session.run(cypher)


def create_topic(topic, graph, documents):
    with driver.session() as session:
        topic_node = graph['topics'].get(topic, None)
        if topic_node:
            summary = topic_node['summary']
            docnames = topic_node['documents']
            # Create or merge the topic node
            session.run("MERGE (t:Topic {name: $name}) ON CREATE SET t.summary = $summary ON MATCH SET t.summary = $summary RETURN t", name=topic, summary=summary)
            # Create or merge the document nodes and create relationships
            for doc in docnames:
                content = documents.get(doc, "")
                session.run("MERGE (d:Document {name: $name}) ON CREATE SET d.content = $content ON MATCH SET d.content = $content RETURN d", name=doc, content=content)
                session.run("MATCH (t:Topic {name: $topic}), (d:Document {name: $doc}) MERGE (t)-[:TOPIC]->(d)", topic=topic, doc=doc)


def create_relationship(source, target):
    with driver.session() as session:
        session.run("MATCH (a:Topic {name: $source}), (b:Topic {name: $target}) MERGE (a)-[:SUBTOPIC]->(b)", source=source, target=target)


def insert_graph(graph, documents):
    for topic in graph['topics'].keys():
        create_topic(topic, graph, documents)
    for edge in graph['edges']:
        create_relationship(edge['source'], edge['target'])


def get_documents_from_topics(topics):
    """Return list of tuples containing document names and list of chunks from a list of topic strings."""
    documents = []
    with driver.session() as session:
        for topic in topics:
            result = session.run("MATCH (t:Topic {name: $topic})-[:TOPIC]->(d:Document) RETURN d.name AS name, d.content AS content", topic=topic)
            documents.extend([(record["name"], record["content"]) for record in result])
    return documents


def get_all_topics():
    """Get comma separated topic strings from neo4j database."""
    with driver.session() as session:
        result = session.run("MATCH (t:Topic) RETURN t.name AS name")
        return ', '.join([record['name'] for record in result])


def get_knowledge_graph():
    nodes = []
    edges = []
    added = set() # keep track of files and topics we have already added
    with driver.session() as session:
        result = session.run("MATCH (d:Document)<-[:TOPIC]-(t:Topic) RETURN d.name AS doc_name, d.content AS content, t.name AS topic_name, t.summary AS summary")
        for record in result:
            # Add document node if not already added
            doc = record['doc_name']
            if doc not in added:
                doc_node = {"name": doc, "type": "document", "content": record['content']}
                nodes.append(doc_node)
                added.add(doc)
            
            # Add topic node if not already added
            topic = record['topic_name']
            if topic not in added:
                topic_node = {"name": topic, "type": "topic", "content": record['summary']}
                nodes.append(topic_node)
                added.add(topic)
            
            # Add link from document to topic (reverse of the original since we are showing documents belonging to topics)
            edges.append({"source": topic, "target": doc})

        result = session.run("MATCH (s:Topic)<-[:SUBTOPIC]-(t:Topic) RETURN s.name AS subtopic, s.summary AS subtopic_summary, t.name AS topic, t.summary AS topic_summary")
        for record in result:
            subtopic = record['subtopic']
            if subtopic not in added:
                subtopic_node = {"name": topic, "type": "topic", "content": record['subtopic_summary']}
                nodes.append(subtopic_node)
                added.add(subtopic)

            topic = record['topic']
            if topic not in added:
                topic_node = {"name": topic, "type": "topic", "content": record['topic_summary']}
                nodes.append(topic_node)
                added.add(topic)

            edges.append({"source": topic, "target": subtopic})

    return {"nodes": nodes, "edges": edges}

def test_insert_graph():
    documents = {
        "file1.pdf": ["pdf stuff"],
        "file2.pptx": ["pptx", "stuff"],
        "file3.pdf": ["pdfff"],
        "file5.docx": ["documents", "word"]
    }
    insert_graph(json.loads(topic_tree_format), documents)
    return get_knowledge_graph()