from h2o_wave import main, app, Q, ui, on, run_on, site
from preprocessing import preprocess_document
from h2ogpt import get_topic_summary
from db import add_document, get_topic_graph
import os
import json

# keep track of whether file was uploaded
files = None

script = '''
const
  width = 300,
  height = Math.min(640, width),
  groupTicks = (d, step) => {{
    const k = (d.endAngle - d.startAngle) / d.value;
    return d3.range(0, d.value, step).map(value => {{
      return {{ value: value, angle: value * k + d.startAngle }};
    }});
  }},
  formatValue = d3.formatPrefix(",.0", 1e3),
  chord = d3.chord()
    .padAngle(0.05)
    .sortSubgroups(d3.descending),
  outerRadius = Math.min(width, height) * 0.5 - 30,
  innerRadius = outerRadius - 20,
  arc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius),
  ribbon = d3.ribbon()
    .radius(innerRadius),
  color = d3.scaleOrdinal()
    .domain(d3.range(4))
    .range(["#000000", "#FFDD89", "#957244", "#F26223"]),
  render = (data) => {{
    const svg = d3.select("#d3-chart")
      .append("svg")
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("font-size", 10)
      .attr("font-family", "sans-serif");

    const chords = chord(data);

    const group = svg.append("g")
      .selectAll("g")
      .data(chords.groups)
      .join("g");

    group.append("path")
      .attr("fill", d => color(d.index))
      .attr("stroke", d => d3.rgb(color(d.index)).darker())
      .attr("d", arc);

    const groupTick = group.append("g")
      .selectAll("g")
      .data(d => groupTicks(d, 1e3))
      .join("g")
      .attr("transform", d => `rotate(${{d.angle * 180 / Math.PI - 90}}) translate(${{outerRadius}},0)`);

    groupTick.append("line")
      .attr("stroke", "#000")
      .attr("x2", 6);

    groupTick
      .filter(d => d.value % 5e3 === 0)
      .append("text")
      .attr("x", 8)
      .attr("dy", ".35em")
      .attr("transform", d => d.angle > Math.PI ? "rotate(180) translate(-16)" : null)
      .attr("text-anchor", d => d.angle > Math.PI ? "end" : null)
      .text(d => formatValue(d.value));

    svg.append("g")
      .attr("fill-opacity", 0.67)
      .selectAll("path")
      .data(chords)
      .join("path")
      .attr("d", ribbon)
      .attr("fill", d => color(d.target.index))
      .attr("stroke", d => d3.rgb(color(d.target.index)).darker());
  }};

  render({data})
'''

args = []
def user_on_page(q: Q):
    """Keep track of the page the user is on before file upload."""
    if 'upload' not in str(q.args):
        args.append(str(q.args))

@on('upload_files')
async def upload_files(q: Q) -> None:
    """Triggered when user clicks the Upload button in the file upload widget."""
    # pass file through processing pipeline to create the knowledge graph
    for filepath in q.args.upload_files:
        local_path = await q.site.download(filepath, '.')
        file_details = preprocess_document(local_path)
        topics, summary = get_topic_summary(file_details['text'])
        document = { 'file': file_details['file'], 'summary': summary }
        add_document(document, topics)
        # TODO: Do word processing for each document and generate knowledge graph
        # TODO: Create graph in database with parsed files

    global files
    files = q.args.upload_files

    # display on the page the user is at only
    if len(args) != 0:
        if 'knowledge_graph' in args[-1]:
            knowledge_graph(q)

# display MCQ questions
def question_generator(q: Q):
    del q.page['knowledge_graph']
    q.page['question_generator'] = ui.form_card(box='content', items=[
            ui.text_xl('Questions'),
    ])
    user_on_page(q)
    if files:
        q.page['question_generator'] = ui.form_card(box='content', items=[
                ui.text_xl(f'Question Generator: {files}')
        ])


# display knowledge graph
def knowledge_graph(q: Q):
    graph = get_topic_graph()
    del q.page['question_generator']
    q.page['knowledge_graph'] = ui.form_card(box='content', items=[
            ui.text_xl('Knowledge Graph'),
    ])
    user_on_page(q)

    # TODO: Remove after using graph
    data = [
        [11975, 5871, 8916, 2868],
        [1951, 10048, 2060, 6171],
        [8010, 16145, 8090, 8045],
        [1013, 990, 940, 6907],
    ]
    q.page['meta'] = ui.meta_card(
        box='',
        script=ui.inline_script(content=script.format(data=json.dumps(data)), requires=['d3']),
        scripts=[ui.script(path="https://d3js.org/d3.v5.min.js")],
    )
    content = '<div id="d3-chart" style="width: 100%; height: 100%"></div>'
    topics = "Topics: " + " ".join(graph['topics'])
    docs = "\n\n".join([g['summary'] for g in graph['documents']])
    q.page['knowledge_graph'] = ui.form_card(box='content', items=[
            ui.text(topics + "\n\n" + docs),
            ui.markup(content=content)
    ])

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
        
    q.client.initialized = True


@app('/')
async def serve(q: Q) -> None:
    if not q.client.initialized:
        init(q)
        question_generator(q)
    elif q.args.question_generator:
        question_generator(q)
    elif q.args.knowledge_graph:
        knowledge_graph(q)

    await run_on(q)
    await q.page.save()
