from h2o_wave import main, app, Q, ui, on, run_on
import concurrent.futures
from file_handler import parse_file

@on('upload_files')
async def upload_files(q: Q) -> None:
    """Triggered when user clicks the Upload button in the file upload widget."""
    # pass file through processing pipeline to create the knowledge graph
    with concurrent.futures.ProcessPoolExecutor() as pool:
        documents = await q.exec(pool, parse_file, q.args.upload_files)
    # TODO: Do word processing for each document and generate knowledge graph
    # TODO: Create graph in database with parsed files


@app('/')
async def serve(q: Q) -> None:
    q.page['sidebar'] = ui.form_card(
        box='1 1 3 -1',
        title='Collections',
        items=[
            ui.file_upload(
                name='upload_files',
                multiple=True,
                required=True,
                file_extensions=['pdf', 'docx'],
            ),
        ]
    )

    await run_on(q)
    await q.page.save()
