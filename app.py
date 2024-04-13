from h2o_wave import main, app, Q, ui, on, run_on, site, data
from preprocessing import parse_file
from h2ogpt import extract_topics, client, generate_questions, system_prompt, llm, topic_tree_format
from db import get_all_topics, get_documents_from_topics, get_knowledge_graph, init_db, insert_graph
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# for knowledge graph
script = '''
function render(graph) {{
    const container = d3.select("#d3-chart");
    const width = 800 // container.node().getBoundingClientRect().width;
    const height = 800;

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;");

    const simulation = d3.forceSimulation(graph.nodes)
        .force("link", d3.forceLink(graph.edges).id(d => d.name).distance(150))
        .force("charge", d3.forceManyBody().strength(-200))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
        .attr("stroke", "#999")
        .selectAll("line")
        .data(graph.edges)
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
        
    node.append("title")
      .text(d => d.label);

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
        wave.emit("graph", "node_clicked", d.name);
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
    doc_topics = {}
    documents = {}
    # run the request topics in parallel to speed up execution
    with ThreadPoolExecutor() as pool:
        futures = {}
        for filepath in q.args.upload_files:
            local_path = await q.site.download(filepath, '.')
            document = parse_file(local_path)
            documents[document['file']] = document['chunks']
            future = pool.submit(extract_topics, document['chunks'])
            futures[future] = document['file']

        for future in as_completed(futures):
            file = futures[future]
            doc_topics[file] = future.result()

    # merge similar topics together with existing ones, and generate subtopic tree
    response = client.extract_data(
        system_prompt=system_prompt,
        pre_prompt_extract="Here is a JSON object mapping filenames to a list of topics and \
summaries, and a list of existing topics. Build a hierarchical topic graph with nodes representing \
topics and edges representing a subtopic relationship. Each topic should contain a brief summary of \
the topic and an array documents with the filenames that contains content relevant to the topic. \
Please combine any topics that are found to be very similar to each other. If any topic is similar \
to one that already exists, please rename it to match the existing topic.\n",
        text_context_list=[json.dumps(doc_topics), get_all_topics()],
        prompt_extract="Your response MUST be a compact JSON object with the attributes topics and \
edges, according to the format specified. The source node is the parent of the target node. Here is an example:\n" + topic_tree_format,
        llm=llm
    )
    # insert graph into the neo4j database
    for res in response.content:
        try:
            insert_graph(json.loads(res), documents)
        except json.JSONDecodeError as e:
            q.page['meta'].notification_bar = ui.notification_bar(
                text=f"Error: {e}",
                type='error',
                position='bottom-right',
            )

    q.client.files = q.args.upload_files # keep track of whether file was uploaded

    if q.client.page == 'question_generator':
        await question_generator(q)
    elif q.client.page == 'knowledge_graph':
        await knowledge_graph(q)


@on()
async def question_generator(q: Q):
    q.client.page = 'question_generator'

    items = [ui.text_xl("Questions")]
    
    topic_items = [ui.text_xl('Topic(s) Selected:')]
    # display selected topics
    topic_items.extend([ui.text(topic) for topic in q.client.selected_topics])
    q.page['top'] = ui.form_card(box='content', items=topic_items)

    q.page['about'] = ui.form_card(box='content', items=[
        ui.text(
        """### How to Use the Question Generator 
1. Click the *Generate* button to generate questions relevant to the selected topics
2. Wait for the questions to be generated
3. Use the chatbot to verify your answers for the generated questions"""
            ),
        ])

    # when generate button is clicked and there are selected topics, generate questions
    if q.client.selected_topics and q.args.generate_button:
        try:
            chunks = ['\n'.join(chunk) for _, chunk in get_documents_from_topics(q.client.selected_topics)]
            q.client.qna = generate_questions(q.client.selected_topics, chunks)
            # Display list of questions in markdown
            for idx, qna in enumerate(q.client.qna):
                markdown_content = f"**{idx + 1}. {qna['question']}**\n\n"
                for i in range(1, 5):
                    option_key = f"option {i}"
                    if option_key in qna:
                        markdown_content += f"{i}. {qna[option_key]}\n"
                items.append(ui.text(markdown_content))
        except:
            q.page['meta'].notification_bar = ui.notification_bar(
                text=f"Failed to generate question for topics {q.client.selected_topics}",
                type='error',
                position='bottom-right',
            )

    # if there is already chat history or user has clicked generate, show chat interface
    if q.client.chatlog or (q.args.generate_button and q.client.selected_topics):
        q.page['chat'] = ui.chatbot_card(
            box='content',
            name='chatbot',
            data = data(fields='content from_user', t='list', rows=q.client.chatlog),
        )
    
    # button to generate questions
    items.append(ui.button(name='generate_button', label='Generate', primary=True))

    q.page['body'] = ui.form_card(box='content', items=items)

    await q.page.save()


@on()
async def generate_button(q: Q):
    if not q.client.selected_topics:
        q.page['meta'] = ui.meta_card(box='', notification_bar=ui.notification_bar(
            text='No topic selected!',
            type='error',
            position='bottom-right',
        ))
    await question_generator(q)


@on()
async def chatbot(q: Q):
    '''
    Chatbot for user to verify their answers to the questions generated.
    Triggers when user submits a query to the chatbot, q.args.chatbot store the
    string representation of user query.
    '''
    # append user query to the chatlog and chat ui
    q.page['chat'].data += [q.args.chatbot, True]
    q.client.chatlog.append([q.args.chatbot, True])
    try:
        documents = get_documents_from_topics([qtn['topic'] for qtn in q.client.qna])
        reply = client.answer_question(
            q.args.chatbot,
            text_context_list=[chunk for _, chunk in documents] + [json.dumps(q.client.qna)],
            system_prompt="You are given a JSON array of MCQ questions with topical tags and \
    explanations, and the contents of a document from which the question is based on. The \
    first line in each chunk indicates the location of the chunk within the outline of the document, \
    separated by the symbol >. Use this to answer the user response to the question and its topic. \
    Please keep your response clear and concise, and answer the user query directly.",
            llm=llm
        )
        print(reply)
        # stream response from h2ogpt
        stream = ''
        q.page['chat'].data += [stream, False]
        q.client.chatlog.append([reply.content, False])
        for w in reply.content.split():
            await q.sleep(0.1)
            stream += w + ' '
            q.page['chat'].data[-1] = [stream, False]
            await q.page.save()
    except:
        q.page['meta'].notification_bar = ui.notification_bar(
            text=f"Failed to get response from LLM {q.client.qna}",
            type='error',
            position='bottom-right',
        )


@on('graph.node_clicked')
async def node_clicked(q: Q) -> None:
    topic = q.events.graph.node_clicked
    # clicking on a document node should not update selected topics
    for node in q.client.graph['nodes']:
        if node['name'] == topic and node['type'] == 'topic':
            if topic in q.client.selected_topics:
                q.client.selected_topics.remove(topic)
            else:
                q.client.selected_topics.add(topic)
    await knowledge_graph(q) # trigger re-render of knowledge graph page


@on()
async def knowledge_graph(q: Q):
    del q.page['chat']
    q.client.page = 'knowledge_graph'
    q.client.graph = get_knowledge_graph()

    header_items = [ui.text_xl('Topic(s) Selected:')]
    # display selected topics
    header_items.extend([ui.text(topic) for topic in q.client.selected_topics])
    q.page['top'] = ui.form_card(box='content', items=header_items)

    q.page['about'] = ui.form_card(box='content', items=[
        ui.text(
        """### How to Use the Knowledge Graph
1. Upload one document or multiple documents
2. Wait for the knowledge graph to be generated
3. View the relationship between the documents and the topics
4. Select any topics to view a summary or generate questions
        """
        ),
    ])

    content = '<div id="d3-chart" style="width: 100%; height: 100%"></div>'
    plot_items = [ui.markup(content=content)]
    q.page['body'] = ui.form_card(
        box='content',
        items=plot_items
    )

    graph_json = json.dumps(q.client.graph)
    # Escape single quotes and backslashes for JavaScript compatibility
    escaped_graph_json = graph_json.replace("\\", "\\\\").replace("'", "\\'")
    fmt_script = script.format(data=escaped_graph_json)

    # inject custom javascript code for displaying the knowledge graph
    q.page['meta'].script = ui.inline_script(content=fmt_script, requires=['d3'], targets=['#d3-chart'])

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
                  ]),
        ],
        scripts=[ui.script(path="https://d3js.org/d3.v6.min.js")],
    )
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
            ui.tab(name='knowledge_graph', label='Knowledge Graph'),
            ui.tab(name='question_generator', label='Question Generation')
        ]
    )
    
    # GLOBAL VARS
    q.client.initialized = True
    q.client.selected_topics = set() # set of selected topics by user
    q.client.chatlog = []


@app('/')
async def serve(q: Q) -> None:
    if not q.client.initialized:
        init_db() # initialise constraint on neo4j database
        init(q)
        await knowledge_graph(q) # set question generator as initial page
    await run_on(q)
