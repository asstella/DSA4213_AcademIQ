from h2o_wave import main, app, Q, ui, on, run_on, site
from preprocessing import preprocess_document
from h2ogpt import get_topic_summary
from db import add_document, get_topic_graph
import os
import json

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

args = []
def user_on_page(q: Q):
    """Keep track of the page the user is on before file upload."""
    if 'upload' not in str(q.args):
        args.append(str(q.args))

@on('upload_files')
async def upload_files(q: Q) -> None:
    """Triggered when user clicks the Upload button in the file upload widget."""
    for filepath in q.args.upload_files:
        local_path = await q.site.download(filepath, '.')
        file_details = preprocess_document(local_path)
        topics, summary = get_topic_summary(file_details['text'])
        document = { 'file': file_details['file'], 'summary': summary }
        add_document(document, topics)
        # TODO: Do word processing for each document and generate knowledge graph
        # TODO: Create graph in database with parsed files

    q.client.files = q.args.upload_files # keep track of whether file was uploaded

    # display on the page the user is at only
    if len(args) != 0:
        if 'knowledge_graph' in args[-1]:
            knowledge_graph(q)

@on()
async def question_generator(q: Q):
    q.page['body'] = ui.form_card(box='content', items=[
            ui.text_xl('Questions'),
    ])
    user_on_page(q)
    if q.client.files:
        q.page['body'] = ui.form_card(box='content', items=[
                ui.text_xl(f'Question Generator: {q.client.files}')
        ])
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
    if not q.client.graph:
        # q.client.graph = get_topic_graph()
        q.client.graph = {
            "nodes": [
                {"id": 0, "label": "topic 1", "type": "topic", "summary": "topic 1 summary"},
                {"id": 1, "label": "document 1", "type": "document"}
            ],
            "links": [{"source": 0, "target": 1}]
        }
    
    q.page['body'] = ui.form_card(box='content', items=[
            ui.text_xl('Knowledge Graph'),
    ])
    user_on_page(q)

    content = '<div id="d3-chart" style="width: 100%; height: 100%"></div>'
    sections = [ui.markup(content=content)]
    if 'current_topic' in q.client:
        node = next(filter(lambda n: n.get('id', None) == q.client.current_topic, q.client.graph['nodes']))
        sections.append(ui.text(node['summary']))

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
                file_extensions=['pdf', 'docx'],
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

@app('/')
async def serve(q: Q) -> None:
    if not q.client.initialized:
        init(q)
        await question_generator(q) # set question generator as initial page
    await run_on(q)
