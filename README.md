# Ask My Docs Backend

A FastAPI-based backend service for document processing and vector database integration.

## Features
- FastAPI-based RESTful API server
- Document processing and chunking capabilities
- Vector database integration (Pinecone)
- PDF and Word document handling
- Async/await support for better performance
- Environment-based configuration
- Comprehensive error handling
- Development-friendly setup with hot-reload

## Prerequisites
- Python 3.13 or higher
- Docker (optional for containerized deployment)

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/mayank-paktolus/ask-my-docs-backend.git
cd ask-my-docs-backend
```

2. Create a virtual environment and activate it
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (based on your configuration needs)

5. Start the development server
```bash
uvicorn app.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`

## Project Structure
- `app/`: Main application code
  - `core/`: Core business logic and services
  - `api/`: API routes and controllers
  - `config/`: Configuration files
  - `initializer/`: Application initialization code

## Development
- The server runs with hot-reload enabled
- API documentation is available at `http://127.0.0.1:8000/docs`
- Use `Ctrl+C` to stop the server

## Deployment
- The project includes a Dockerfile for containerization
- Customize the Dockerfile as needed for your environment

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

