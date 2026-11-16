from library.database import get_processed_filenames
from library.config import PAPERS_DIR

def find_new_pdf():
    """
    Scan pdf from the .config path and look if there are new pdf papers 
    by comparing in the database.
    If they are new the function return their path
    """
    db_papers = get_processed_filenames()
    new_pdf = [
        str(pdf) for pdf in sorted(PAPERS_DIR.glob("*.pdf"))
        if pdf.name not in db_papers
    ]
    
    return new_pdf
