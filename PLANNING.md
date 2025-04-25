# PLANNING.md

## 1. Purpose & Vision

**Purpose:** To create a secure web application that allows authenticated users to get and analyze data of clinical trials and FDA by querying the clinicaltrials.gov and fda.gov databases via their respective APIs. The application will present the aggregated data in a user-friendly dashboard and provide an integrated AI chat interface for users to ask follow-up questions based on the presented data. Access to the search, dashboard, and chat features requires user login.

**Vision:** A one-stop, intuitive platform for researchers, healthcare professionals, and consultants to access and interact with clinical trial and FDA data, enhanced by AI-driven conversational insights.

## 2. High-Level Architecture

* **Frontend:** A single-page web application (SPA) built with a modern JavaScript framework (e.g., React, Vue, Angular) or vanilla HTML/CSS/JS. It will handle:
    * User authentication flows (Login/Signup pages/components).
    * Interaction with Supabase for authentication (Email/Password, Google, LinkedIn).
    * Securely storing and managing user sessions/tokens.
    * User input (search term, type selection) *after* login.
    * Displaying the dashboard and managing the chat interface *after* login.
    * Making authenticated requests to the backend API.
    * Data Visualization: Recharts or D3.js for dashboard visualizations	
* **Backend:** A FastAPI acting as an API gateway. It will:
    * Require valid authentication (e.g., JWT provided by Supabase) for accessing core API endpoints (`/api/search`, `/api/chat`).
    * Receive search requests from authenticated frontend users.
    * Call the provided Python modules (`clinical_trials_module`, `openfda`) to fetch data.
    * Process and aggregate data from both sources.
    * Serve the processed data to the frontend for dashboard display.
    * Handle chat requests from authenticated frontend users.
    * Format the relevant dashboard data as context for the LLM.
    * Interact with an external Large Language Model (LLM) API.
    * Send LLM responses back to the frontend.
    * (Optional) Interact with Supabase backend library (`supabase-py`) for server-side validation if needed.
* **Authentication Provider:** **Supabase** (handling Auth, user management).
* **Data Sources:**
    * ClinicalTrials.gov (accessed via `clinical_trials_module.get_clinical_trials_data`) example to use it get_clinical_trials_data(keyword) and Open_FDA.open_fda_main(domain=domain, user_keyword=keyword).
    * OpenFDA (accessed via `openfda.Open_FDA.open_fda_main`)
* **AI Integration:** LangChain for connecting to LLM services, service accessed via its API.

## 3. Constraints & Considerations

* **API Rate Limits:** clinicaltrials.gov, openFDA, and LLM APIs may have usage limits. Caching and queueing might be needed.
* **Data Volume & Structure:** APIs can return large/complex datasets. Efficient data handling is crucial. Data harmonization or distinct presentation is needed. The data schema and structure is saved in fda_column.csv and clinical_trials_column.csv files.
* **API Availability & Errors:** External APIs (ClinicalTrials, FDA, LLM, **Supabase**) might be unavailable. Robust error handling is essential.
* **Data Interpretation:** AI chat needs careful prompting to avoid giving medical advice. Disclaimer required.
* **Scalability:** Design backend and choose Supabase plan considering concurrent users.
* **Security:**
    * Protect API keys (LLM, Supabase Service Key for backend if used).
    * Securely manage Supabase Anon Key on the frontend.
    * Implement proper authentication checks on all protected backend routes.
    * Configure OAuth providers (Google, LinkedIn) securely, including redirect URIs.
    * Handle user data privacy according to relevant regulations.
* **OAuth Configuration:** Setting up Google and LinkedIn OAuth requires creating applications on their respective developer platforms and configuring secrets/keys in Supabase.
* **Scrollable UI:** Dashboard results and chat interface need independent scrolling.

## 4. Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (React, Vue, or Angular highly recommended for managing auth state and components)
* **Backend:** Python (Flask or Django recommended)
* **Authentication:** **Supabase**
    * Frontend: `supabase-js` library
    * Backend (Optional/Validation): `supabase-py` library
* **Data Fetching Modules:** `clinical_trials_module`, `openfda` (as provided)
* **HTTP Requests (if needed within backend):** `requests` Python library
* **AI:** LLM Provider API i.e OpenAI API) + corresponding Python SDK

## 5. Tools

* **Package Manager:** pip, conda (backend); npm, yarn (frontend)
* **Virtual Environment:** `venv`, `conda`
* **API Testing:** Postman, Insomnia
* **Project Management:** TASK.md
* **Supabase:** Supabase Dashboard (for project setup, auth configuration) use project name Postlytllp's Project and project ID-sgtguuqbuqtpwmfknovr 
* **OAuth Provider Consoles:** Google Cloud Console, LinkedIn Developer Portal

## 6. Key Features

* **User Authentication:**
    * Registration & Login via Email/Password.
    * Login via Google (OAuth).
    * Login via LinkedIn (OAuth).
    * Logout functionality.
* **Access Control:** Core application (search, dashboard, chat) accessible only to logged-in users.
* Keyword search input.
* Selection for search type (Disease/Drug).
* Backend integration with `clinical_trials_module` and `openfda` modules.
* Data aggregation and processing logic.
* Scrollable dashboard UI to display results from both sources.
* Scrollable, full-width AI chat bar at the bottom.
* LLM integration for answering questions based on displayed dashboard data.
* Clear separation and labeling of data from clinicaltrials.gov vs. fda.gov.
