# Resume Data Extraction Pipeline

An AI-powered resume data extraction application that transforms unstructured resumes into structured data using Large Language Models.

## Features

- Extract structured data from resumes using AI
- Support for multiple file formats (PDF, DOCX, TXT)
- Configurable LLM providers (Groq's Llama 3 by default)
- Web interface and command-line interface options
- Instant, formatted results display

## Prerequisites

- Python 3.12
- pipenv installed (`pip install pipenv`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tirth013/ResumeReveal.git
cd ResumeReveal
```

2. Install dependencies:
```bash
pipenv install
```

3. Create necessary directories:
```bash
pipenv run python setup.py
```

4. Configure environment:
```bash
# Copy the example environment file
cp .env.example .env
# Edit the .env file with your API keys
```

## Usage

### Web Application

1. Start the web server:
```bash
pipenv run python app.py
```

2. Open `http://localhost:5000` in your browser

3. Upload your resume and click "Extract Data"

4. View the structured results:
   - Personal information
   - Skills
   - Work experience
   - Education history
   - Professional summary

### Command Line Interface

```bash
# Process a single resume
pipenv run python main.py process path/to/resume.pdf

# Process multiple resumes
pipenv run python main.py batch path/to/resumes/
```

## Configuration

Edit the `.env` file to configure API keys:
```
GROQ_API_KEY=your_api_key_here
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.