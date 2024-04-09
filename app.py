from h2o_wave import main, app, Q, ui, on, run_on, site, data
from preprocessing import parse_file
from h2ogpt import extract_topics, client
from db import add_document, get_topic_graph
import os
import json

# for knowledge graph
script = '''
function render(graph) {{
    const container = d3.select("#d3-chart");
    const width = 600 // container.node().getBoundingClientRect().width;
    const height = 800;

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height);

    const simulation = d3.forceSimulation(graph.nodes)
        .force("link", d3.forceLink(graph.links).id(d => d.id).distance(150))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
        .attr("stroke", "#999")
        .selectAll("line")
        .data(graph.links)
        .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value));

    const color = d3.scaleOrdinal()
        .domain(["topic", "document", "topic-active", "document-active"])
        .range(["#87C0D0", "#E74C3C", "#A7E0F0", "#F39C12"]);
    
    const colorHover = d3.scaleOrdinal()
        .domain(["topic", "document"])
        .range(["#A7E0F0", "#F39C12"]);

    const drag = simulation => {{
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}

        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }};

    const node = svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .selectAll("circle")
        .data(graph.nodes)
        .join("circle")
        .attr("r", 40)
        .attr("fill", d => color(d.type))
        .call(drag(simulation));

    node.on("mouseover", function(event, d) {{
        d3.select(this)
            .style("cursor", "pointer")
            .style("fill", d => colorHover(d.type));
    }})

    node.on("mouseout", function(d) {{
        d3.select(this)
            .style("fill", d => color(d.type));
    }});

    // when we click on a node we will toggle it as a topic for question generation
    node.on('click', (event, d) => {{
        container.remove() // remove the div to make sure new run waits on new div
        wave.emit("graph", "node_clicked", d.id);
    }});

    simulation.on("tick", () => {{
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
    }});
}}

render(JSON.parse('{data}'));
'''

@on('upload_files')
async def upload_files(q: Q) -> None:
    """Triggered when user clicks the Upload button in the file upload widget."""
    for filepath in q.args.upload_files:
        local_path = await q.site.download(filepath, '.')
        document = parse_file(local_path)
        topics = extract_topics(document['chunks'])
        add_document(document, topics)
    # TODO: Add some form topic refinement to make sure similar topics are merged

    q.client.files = q.args.upload_files # keep track of whether file was uploaded

    if q.client.page == 'question_generator':
        await question_generator(q)
    elif q.client.page == 'knowledge_graph':
        await knowledge_graph(q)

@on()
async def question_generator(q: Q):
    q.client.page = 'question_generator'
    
    # basic form setup
    items = [ui.text_xl('Questions')]
    topic_items = [ui.text_xl('Topic(s) Selected:')]

    # if topics are selected, display them
    if q.client.selected_topics:
        for topic in q.client.selected_topics:
            node = next(filter(lambda n: n.get('id', None) == topic, q.client.graph['nodes']), None)
            if node:
                topics = [node['label']]
                topic_items.extend([ui.text(item) for item in topics])
    
    q.page['top'] = ui.form_card(box='content', items = topic_items)
    
    # display questions if available
    if q.client.files and q.args.generate_button:
        if not q.client.qna:
            # TODO: replace with real data
            q.client.qna = [
                {"id": 0, "question": "What is 1+1?", "answer": "2"},
                {"id": 1, "question": "How to draw a circle?", "answer": "Use a pencil."}
            ]
        items.extend([ui.text(item['question']) for item in q.client.qna])
        q.page['body1'] = ui.chatbot_card(
            box='content',
            name='chatbot',
            data = data(fields='content from_user', t='list'),
            generating=True,
            events=['stop']
        )
        if len(topic_items) != 0:
            # display different qna for specific topic
            pass
    
    # button to generate questions
    items.append(ui.button(name='generate_button', label='Generate', primary=True))

    q.page['body'] = ui.form_card(box='content', items=items)
    await q.page.save()

@on('generate_button')
async def generate_button(q: Q):
    await question_generator(q)

@on()
async def chatbot(q: Q):
    '''
    Chatbot for user to verify their answers to the questions generated.
    Displayed when user clicks on button to generate questions on question_generation page.
    '''
    qna_str = json.dumps(q.client.qna)
    tmp = client.upload('qna.txt', qna_str)
    client.ingest_uploads(q.client.collection_id, [tmp])
    with client.connect(q.client.chat_session_id) as session:
        # append user query to the chatbot
        q.page['body1'].data += [q.args.chatbot, True]
        reply = session.query(q.args.chatbot, timeout=60)
        # stream response from h2ogpt
        stream = ''
        if not reply:
            print("No reply received")
        q.page['body1'].data += [reply.content, False]
        for w in reply.content.split():
            await q.sleep(0.1)
            stream += w + ' '
            q.page['body1'].data[-1] = [stream, False]
            await q.page.save()

@on('graph.node_clicked')
async def node_clicked(q: Q) -> None:
    id = q.events.graph.node_clicked
    if id in q.client.selected_topics:
        q.client.selected_topics.remove(id)
    else:
        q.client.selected_topics.add(id)
    q.client.current_topic = id # knowledge graph will show information about topic clicked on
    await knowledge_graph(q) # trigger re-render of knowledge graph page

@on()
async def knowledge_graph(q: Q):
    del q.page['body1']
    q.client.page = 'knowledge_graph'
    if not q.client.graph:
        # q.client.graph = get_topic_graph()
        # TODO: Remove sample data for testing
        q.client.graph = {
            "nodes": [
                {"id": 0, "label": "topic 1", "type": "topic", "summary": "topic 1 summary"},
                {"id": 2, "label": "topic 2", "type": "topic", "summary": "topic 2 summary"},
                {"id": 1, "label": "document 1", "type": "document"}
            ],
            "links": [{"source": 0, "target": 1, "source": 0, "target": 2}]
        }
    
    q.page['body'] = ui.form_card(box='content', items=[
            ui.text_xl('Knowledge Graph'),
    ])

    content = '<div id="d3-chart" style="width: 100%; height: 100%"></div>'
    sections = [ui.markup(content=content)]
    topic_items = [ui.text_xl('Topic(s) Selected:')]

    # if topics are selected, display them
    if q.client.selected_topics:
        for topic in q.client.selected_topics:
            node = next(filter(lambda n: n.get('id', None) == topic, q.client.graph['nodes']), None)
            if node:
                topics = [node['label']]
                topic_items.extend([ui.text(item) for item in topics])

    q.page['top'] = ui.form_card(box='content', items = topic_items)

    q.page['body'] = ui.form_card(
        box='content',
        items=sections
    )

    fmt_script = script.format(data=json.dumps(q.client.graph))
    q.page['meta'] = ui.meta_card(
        box='',
        script=ui.inline_script(content=fmt_script, requires=['d3'], targets=['#d3-chart']),
        scripts=[ui.script(path="https://d3js.org/d3.v6.min.js")],
    )

    await q.page.save()

def init(q: Q):
    q.page['meta'] = ui.meta_card(box='', title='AcademIQ', theme='nord', layouts=[
        ui.layout(breakpoint='xs', 
                  zones=[ui.zone('header', wrap='stretch'),
                         ui.zone('body', direction=ui.ZoneDirection.ROW, size='1', zones=[
                                ui.zone('sidebar', size='25%'),
                                ui.zone('body2', direction=ui.ZoneDirection.COLUMN, zones=[ui.zone('nav'),
                                    ui.zone('content')])
                        ])
                  ])
    ])
    q.page['header'] = ui.header_card(
        box='header',
        title='AcademIQ',
        subtitle='Educational tool to empower educators and learners in knowledge acquisition and assessment',
        image='https://www.svgrepo.com/show/288267/studying-student.svg',
    )
    q.page['sidebar'] = ui.form_card(
        box='sidebar',
        title='Upload Files',
        items=[
            ui.file_upload(
                name='upload_files',
                multiple=True,
                required=True,
                file_extensions=['pdf', 'docx', 'pptx', 'txt', 'md'],
            ),
        ]
    )
    q.page['nav'] = ui.tab_card(
        box='nav',
        items=[
            ui.tab(name='question_generator', label='Question Generation'),
            ui.tab(name='knowledge_graph', label='Knowledge Graph')  
        ]
    )
    
    # GLOBAL VARS
    q.client.initialized = True
    q.client.selected_topics = set() # set of selected topics by user
    # take the most recent collection in the API key
    recent_collections = client.list_recent_collections(0, 1000)
    for c in recent_collections:
        if c.name == "AcademIQ":
            q.client.collection_id = c.id
            break
    q.client.chat_session_id = client.create_chat_session(q.client.collection_id)


@app('/')
async def serve(q: Q) -> None:
    if not q.client.initialized:
        init(q)
        await question_generator(q) # set question generator as initial page
    await run_on(q)
