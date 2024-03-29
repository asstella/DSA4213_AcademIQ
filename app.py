from h2o_wave import main, app, Q, ui, on, run_on
from preprocessing import preprocess_document
from h2ogpt import get_topic_summary
from db import add_document, get_topic_graph

# keep track of whether file was uploaded
files = None

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
    topics = "Topics: " + " ".join(graph['topics'])
    docs = "\n\n".join([g['summary'] for g in graph['documents']])
    q.page['knowledge_graph'] = ui.form_card(box='content', items=[
            ui.text(topics + "\n\n" + docs)
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
