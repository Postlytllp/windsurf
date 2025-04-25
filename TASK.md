# TASK.md

**Purpose:** Tracks tasks for the Clinical Trials & FDA Data Search App project.

---

## Backlog

* [ ] User Profile Management Page
* [ ] Password Reset Functionality (for Email/Password Auth)
* [ ] Email Verification Requirement after Signup
* [ ] Search History Feature (potentially associated with user accounts)
* [ ] Advanced Filtering/Sorting Options for Dashboard Data
* [ ] Data Export Feature (e.g., CSV)
* [ ] Caching mechanism for API responses (ClinicalTrials/FDA)
* [ ] Rate Limiting implementation on backend endpoints
* [ ] More sophisticated error handling and reporting (e.g., Sentry)
* [ ] Add unit/integration tests for frontend components (including Auth)
* [ ] Implement CI/CD pipeline for automated testing and deployment

---

## Current Sprint / To Do

### Setup & Foundation
* [x] Initialize Git repository and push to remote (e.g., GitHub).
* [x] **Set up Supabase Project:** Create a new project in the Supabase dashboard.
* [x] **Configure Supabase Auth:**
    * [x] Enable Email/Password Authentication.
    * [x] Enable and configure Google Provider (requires setup in Google Cloud Console).
    * [x] Enable and configure LinkedIn Provider (requires setup in LinkedIn Developer Portal).
    * [x] Note Supabase Project URL and Anon Key.
* [x] Set up Python backend project structure FastAPI.
* [x] Create and manage Python virtual environment (`venv`).
* [x] Install core backend dependencies (`FastAPI`, `requests`, `supabase-py` - *optional, if backend needs Supabase interaction*).
* [x] Set up basic frontend project structure (HTML, CSS, JS or framework CLI).
* [x] Install frontend dependencies (e.g., `supabase-js`, framework-specific libraries).
* [x] Securely configure Supabase URL/Anon Key in frontend environment variables.
* [x] Securely configure Supabase URL/Service Key in backend environment variables (*only if using `supabase-py`*).
* [x] Integrate provided `clinical_trials_module` and `openfda` modules into the backend.

### Authentication (Frontend)
* [x] Create Login Page/Component UI.
* [x] Create Signup Page/Component UI (if allowing email registration).
* [x] Implement Email/Password Login form using `supabase-js`.
* [x] Implement Email/Password Signup form using `supabase-js` (if applicable).
* [x] Implement "Login with Google" button using `supabase-js` OAuth flow.
* [x] Implement "Login with LinkedIn" button using `supabase-js` OAuth flow.
* [x] Implement Logout button/functionality using `supabase-js`.
* [x] Implement frontend routing:
    * [x] Redirect unauthenticated users to Login page.
    * [x] Protect main application routes (dashboard/search/chat).
    * [x] Handle OAuth redirect callbacks.
* [x] Manage application state based on user authentication status (e.g., show/hide elements, store user info).
* [x] Modify frontend API calls (to `/api/search`, `/api/chat`) to include the Supabase Auth JWT in the `Authorization` header.

### Authentication (Backend)
* [x] Implement middleware or decorator for protected API endpoints (`/api/search`, `/api/chat`).
* [x] Add logic within middleware/decorator to:
    * [x] Extract JWT from `Authorization: Bearer <token>` header.
    * [x] Validate the JWT using Supabase (either via `supabase-py` or by decoding/verifying against Supabase public keys/settings if preferred).
    * [x] Reject request with 401/403 error if token is invalid or missing.
* [x] (Optional) Extract user ID from validated token if needed for logging or associating data.

### Core Feature Backend Development
* [x] Create backend API endpoint (`/api/search`) - *ensure it's protected*.
* [x] Implement logic in `/api/search` to call `get_clinical_trials_data(keyword)`.
* [x] Implement logic in `/api/search` to call `Open_FDA.open_fda_main(domain=domain, user_keyword=keyword)`. Determine appropriate `domain`.
* [x] Develop data processing/aggregation logic.
* [x] Implement error handling for external API calls.
* [x] Choose LLM provider and obtain API key.
* [x] Install LLM provider's Python SDK.
* [x] Create backend API endpoint (`/api/chat`) - *ensure it's protected*.
* [x] Implement logic in `/api/chat` to format context and query the LLM API.
* [x] Implement error handling for LLM API calls.

### Core Feature Frontend Development
* [x] Create main application page structure (search form, dashboard area, chat bar area) - *visible only when logged in*.
* [x] Style the page layout using CSS (dashboard/chat distinct, scrollable, full-width chat).
* [x] Implement search form (input, type selection, submit).
* [x] Write JavaScript to send *authenticated* POST request to `/api/search`.
* [x] Develop dashboard component(s) to render data received from `/api/search`.
* [x] Implement CSS/JS for scrollable dashboard area.
* [x] Develop chat bar component (input, message display, send button).
* [x] Implement CSS/JS for scrollable chat message area.
* [x] Write JavaScript to send *authenticated* POST request to `/api/chat`.
* [x] Write JavaScript to display AI responses in chat.
* [x] Handle loading states and error messages in the UI.

### Testing & Deployment
* [x] Write basic unit tests for backend logic.
* [ ] **Test Authentication Flows:** Manually test Email/Pass login/signup, Google login, LinkedIn login, logout, accessing protected routes.
* [ ] Perform manual end-to-end testing of search and chat features *after* login.
* [ ] Choose deployment platform.
* [ ] Configure environment variables (API keys, Supabase keys) for deployment.
* [ ] Configure correct OAuth Redirect URIs in Supabase/Google/LinkedIn for the deployed application URL.
* [ ] Create deployment configuration file (e.g., `Procfile`, `Dockerfile`, `app.yaml`).
* [ ] Perform initial deployment.

---

## In Progress

* [ ] Configure environment variables (API keys, Supabase keys) for deployment.

---

## Done

* [x] Set up project structure for FastAPI backend and frontend
* [x] Create authentication API endpoints
* [x] Create search API endpoint
* [x] Create chat API endpoint with LangGraph integration
* [x] Implement frontend UI with Bootstrap
* [x] Create interactive dashboard with Chart.js
* [x] Implement chat interface for natural language queries
* [x] Write unit tests for backend APIs
* [x] Create README.md with project documentation

---

## Discovered During Work

* [ ] Add proper error handling for API rate limits
* [ ] Implement caching for API responses to improve performance
* [ ] Add pagination for search results when there are many matches
* [ ] Create user profile page for account management
* [ ] Add export functionality for search results (CSV/PDF)
* [ ] Implement advanced filtering options for search results
* [ ] Add more interactive visualizations for the dashboard
* [ ] Improve chat agent with better context handling for complex queries