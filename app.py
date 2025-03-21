import os
import json
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime

# Core components
from document_loaders import extract_text_from_pdf, extract_text_from_docx
from parsers import get_parser
from utils import save_extraction_result, Timer, setup_directories, logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "resume-extraction-secret-key"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc', 'txt'}

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
setup_directories("output", ["resume"])

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_document(file_path, llm_provider="groq"):
    """
    Process a resume document and extract structured data.
    
    Args:
        file_path: Path to the resume document file
        llm_provider: LLM provider to use
        
    Returns:
        Extracted data as a dictionary
    """
    logger.info(f"Processing resume: {file_path}")
    
    # Extract text based on file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    with Timer(f"Text extraction from {file_ext}"):
        if file_ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            text = extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Parse the document using LLM
    parser = get_parser("resume", llm_provider=llm_provider)
    with Timer(f"Data extraction with {llm_provider}"):
        extracted_data = parser.parse(text)
    
    # Save the extraction result
    doc_id = os.path.basename(file_path).split('.')[0]
    output_path = save_extraction_result(
        data=extracted_data,
        doc_id=doc_id,
        doc_type="resume",
        output_dir="output",
        metadata={"source_file": file_path}
    )
    
    logger.info(f"Resume processed successfully. Results saved to: {output_path}")
    return extracted_data

@app.route('/')
def index():
    """Render the main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process the resume"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            extraction_result = process_document(
                file_path=file_path
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = os.path.splitext(filename)[0] + "_" + timestamp
            
            result_data = {
                'filename': filename,
                'processed_at': timestamp,
                'extracted_data': extraction_result,
            }
            
            return render_template('results.html', result=result_data)
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(request.url)
    else:
        flash('File type not allowed')
        return redirect(request.url)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download the processed JSON result"""
    return send_file(os.path.join("output", "resume", filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 