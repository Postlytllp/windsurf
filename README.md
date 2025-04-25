# Clinical Trials & FDA Data Search App

A secure web application that allows authenticated users to search and analyze data from clinical trials and FDA databases, with an integrated AI chat interface for natural language queries about the data.

## Features

- **User Authentication**
  - Email/Password registration and login
  - OAuth login via Google and LinkedIn
  - Secure session management

- **Data Search**
  - Search for clinical trials and FDA data by keyword
  - Filter by domain (disease or drug)
  - View comprehensive results in a user-friendly dashboard

- **Interactive Dashboard**
  - Scrollable data tables for clinical trials and FDA information
  - Interactive charts showing trial status and phases distribution
  - Expandable details for each clinical trial and FDA drug entry

- **AI-Powered Chat Interface**
  - Ask natural language questions about the displayed data
  - Get contextual answers based on the search results
  - View sources for the information provided

## Tech Stack

- **Backend**
  - Python with FastAPI
  - Supabase for authentication
  - LangGraph for LLM-powered chat agent
  - Pandas for data processing

- **Frontend**
  - HTML5, CSS3, JavaScript
  - Bootstrap 5 for responsive UI
  - Chart.js for data visualization
  - Supabase JS client for authentication

- **External Services**
  - ClinicalTrials.gov API
  - OpenFDA API
  - OpenAI API (for LLM integration)

## Project Structure

```
app/
├── api/                 # API endpoints
│   ├── auth.py          # Authentication routes
│   ├── search.py        # Search functionality
│   └── chat.py          # Chat functionality
├── agents/              # LLM agents
│   └── chat_agent.py    # LangGraph agent for answering questions
├── frontend/            # Frontend files
│   ├── index.html       # Main HTML file
│   ├── styles.css       # CSS styles
│   └── app.js           # JavaScript functionality
├── models/              # Pydantic models
│   └── user.py          # User models
├── tests/               # Unit tests
│   ├── test_auth.py     # Authentication tests
│   ├── test_search.py   # Search tests
│   └── test_chat.py     # Chat tests
└── main.py              # FastAPI application entry point
```

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd windsurf
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   SUPABASE_URL=https://sgtguuqbuqtpwmfknovr.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   OPENAI_API_KEY=your-openai-api-key
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## Testing

Run the test suite with pytest:
```bash
pytest app/tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
