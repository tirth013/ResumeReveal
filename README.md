# Resume Data Extraction Pipeline

An AI-powered resume data extraction application that transforms unstructured resumes into structured data using Large Language Models.

## Features

- Extract structured data from **resumes** using AI
- Support for multiple file formats (PDF, DOCX, TXT)
- Configurable LLM providers (Groq's Llama 3 by default)
- Beautiful, user-friendly web interface
- Command-line interface for batch processing
- Instant, formatted results display

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tirth013/ResumeReveal.git
cd ResumeReveal
```

2. Install pipenv if you don't have it:
```bash
pip install pipenv
```

3. Install project dependencies with pipenv:
```bash
pipenv install
```

4. Create necessary directories:
```bash
pipenv run python setup.py
```

5. Set up your environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API keys
# Replace 'your_groq_api_key_here' with your actual API key
```

## Usage

### Web Application

1. Start the web server using pipenv:
```bash
pipenv run python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload your resume:
   - Click the file upload button to select your resume file (PDF, DOCX, TXT)
   - Click "Extract Data" to process your resume
   
4. View the results:
   - Personal information (name, email, phone)
   - Skills (formatted as tags)
   - Work experience (chronological list)
   - Education history
   - Professional summary
   - You can also see the raw JSON data at the bottom of the results page

### Command Line Usage (Alternative)

The application also provides a command-line interface:

```bash
# Process a single resume
pipenv run python main.py process path/to/resume.pdf

# Process multiple resumes in a directory
pipenv run python main.py batch path/to/resumes/
```

## Configuration

You can configure the application by editing the `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

The application is configured to use Groq's Llama 3 model by default, which provides excellent results for resume parsing.

## Dependency Management

The project uses pipenv for dependency management. All required packages are listed in the Pipfile:

- Python 3.9 required
- Core packages: flask, langchain, langchain-groq, pydantic, etc.
- Development packages: pytest, black

To add new dependencies:
```bash
pipenv install <package_name>
```

To run the application:
```bash
pipenv run python app.py
```

Or to activate the pipenv shell:
```bash
pipenv shell
```


## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
