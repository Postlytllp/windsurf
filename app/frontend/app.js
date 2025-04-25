// Supabase configuration
const SUPABASE_URL = 'https://sgtguuqbuqtpwmfknovr.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNndGd1dXFidXF0cHdtZmtub3ZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NjM2NjEsImV4cCI6MjA2MTEzOTY2MX0.CQMb2uuBx7Tf0Flzh5XYiU8VdwlbRqFaZelXSb3xm1I';

// API base URL
const API_BASE_URL = '/api';

// Initialize Supabase client
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Global state
let currentUser = null;
let searchResults = {
    clinicalTrials: [],
    fdaData: []
};
let chatHistory = [];

// DOM Elements
// Auth elements
const authContainer = document.getElementById('auth-container');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const loginFormElement = document.getElementById('login-form-element');
const signupFormElement = document.getElementById('signup-form-element');
const loginError = document.getElementById('login-error');
const signupError = document.getElementById('signup-error');
const showSignupLink = document.getElementById('show-signup');
const showLoginLink = document.getElementById('show-login');
const googleLoginBtn = document.getElementById('google-login');
const linkedinLoginBtn = document.getElementById('linkedin-login');

// App elements
const appContainer = document.getElementById('app-container');
const userEmailElement = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');
const searchForm = document.getElementById('search-form');
const keywordInput = document.getElementById('keyword');
const searchTypeRadios = document.querySelectorAll('input[name="searchType"]');
const searchBtn = document.getElementById('search-btn');
const searchSpinner = document.getElementById('search-spinner');
const clinicalTrialsContainer = document.getElementById('clinical-trials-container');
const clinicalTrialsPlaceholder = document.getElementById('clinical-trials-placeholder');
const clinicalTrialsCount = document.getElementById('clinical-trials-count');
const fdaContainer = document.getElementById('fda-container');
const fdaPlaceholder = document.getElementById('fda-placeholder');
const fdaCount = document.getElementById('fda-count');
const dashboardWidgets = document.getElementById('dashboard-widgets');
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatSubmitBtn = document.getElementById('chat-submit-btn');
const chatSpinner = document.getElementById('chat-spinner');

// Charts
let statusChart = null;
let phasesChart = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', initApp);

// Auth event listeners
showSignupLink.addEventListener('click', showSignup);
showLoginLink.addEventListener('click', showLogin);
loginFormElement.addEventListener('submit', handleLogin);
signupFormElement.addEventListener('submit', handleSignup);
googleLoginBtn.addEventListener('click', handleGoogleLogin);
linkedinLoginBtn.addEventListener('click', handleLinkedinLogin);
logoutBtn.addEventListener('click', handleLogout);

// App event listeners
searchForm.addEventListener('submit', handleSearch);
chatForm.addEventListener('submit', submitChatMessage);

// Functions
function initApp() {
    // Check if user is already logged in
    checkAuthState();
}

async function checkAuthState() {
    try {
        const { data: { user }, error } = await supabaseClient.auth.getUser();
        
        if (error) throw error;
        
        if (user) {
            currentUser = user;
            showApp();
        } else {
            showAuth();
        }
    } catch (error) {
        console.error('Auth state error:', error);
        showAuth();
    }
}

function showAuth() {
    authContainer.classList.remove('d-none');
    appContainer.classList.add('d-none');
}

function showApp() {
    authContainer.classList.add('d-none');
    appContainer.classList.remove('d-none');
    
    // Display user email
    if (currentUser && currentUser.email) {
        userEmailElement.textContent = currentUser.email;
    }
}

function showSignup(e) {
    e.preventDefault();
    loginForm.classList.add('d-none');
    signupForm.classList.remove('d-none');
}

function showLogin(e) {
    e.preventDefault();
    signupForm.classList.add('d-none');
    loginForm.classList.remove('d-none');
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        loginError.classList.add('d-none');
        
        // Use Supabase client directly for login
        const { data, error } = await supabaseClient.auth.signInWithPassword({
            email,
            password
        });
        
        if (error) {
            throw new Error(error.message || 'Login failed');
        }
        
        // Session is handled by Supabase client
        
        // Set current user
        currentUser = data.user;
        
        // Show app
        showApp();
    } catch (error) {
        console.error('Login error:', error);
        loginError.textContent = error.message;
        loginError.classList.remove('d-none');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    
    try {
        signupError.classList.add('d-none');
        
        // Use Supabase client directly for signup
        const { data, error } = await supabaseClient.auth.signUp({
            email,
            password
        });
        
        if (error) {
            throw new Error(error.message || 'Signup failed');
        }
        
        // Store session in localStorage (handled by Supabase client)
        
        // Set current user
        currentUser = data.user;
        
        // Show app or confirmation message
        if (data.user) {
            showApp();
        } else {
            // Email confirmation might be required
            signupError.textContent = "Please check your email for confirmation link";
            signupError.classList.remove('d-none');
            signupError.classList.remove('alert-danger');
            signupError.classList.add('alert-success');
        }
    } catch (error) {
        console.error('Signup error:', error);
        signupError.textContent = error.message;
        signupError.classList.remove('d-none');
        signupError.classList.add('alert-danger');
        signupError.classList.remove('alert-success');
    }
}

async function handleGoogleLogin() {
    try {
        const { data, error } = await supabaseClient.auth.signInWithOAuth({
            provider: 'google'
        });
        
        if (error) throw error;
    } catch (error) {
        console.error('Google login error:', error);
        loginError.textContent = 'Google login failed. Please try again.';
        loginError.classList.remove('d-none');
    }
}

async function handleLinkedinLogin() {
    try {
        const { data, error } = await supabaseClient.auth.signInWithOAuth({
            provider: 'linkedin'
        });
        
        if (error) throw error;
    } catch (error) {
        console.error('LinkedIn login error:', error);
        loginError.textContent = 'LinkedIn login failed. Please try again.';
        loginError.classList.remove('d-none');
    }
}

async function handleLogout() {
    try {
        // Use Supabase client directly for logout
        const { error } = await supabaseClient.auth.signOut();
        
        if (error) {
            throw error;
        }
        
        // Clear current user
        currentUser = null;
        
        // Show auth
        showAuth();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

async function handleSearch(e) {
    e.preventDefault();
    
    const keyword = keywordInput.value.trim();
    const searchType = Array.from(searchTypeRadios).find(radio => radio.checked).value;
    
    console.log("Search initiated with keyword:", keyword, "and search type:", searchType);
    
    if (!keyword) {
        alert("Please enter a keyword to search");
        return;
    }
    
    try {
        // Show loading state
        searchBtn.disabled = true;
        searchSpinner.classList.remove('d-none');
        
        // Clear previous results
        clinicalTrialsContainer.innerHTML = '';
        fdaContainer.innerHTML = '';
        clinicalTrialsPlaceholder.classList.add('d-none');
        fdaPlaceholder.classList.add('d-none');
        
        console.log("Getting Supabase session...");
        // Get session from Supabase for authentication
        const { data, error } = await supabaseClient.auth.getSession();
        
        if (error) {
            console.error("Supabase session error:", error);
            throw new Error('Authentication error: ' + (error.message || 'Failed to get session'));
        }
        
        if (!data || !data.session) {
            console.error("No session data returned from Supabase");
            throw new Error('Authentication required. Please log in again.');
        }
        
        // Get the JWT token
        const token = data.session.access_token;
        console.log("Got authentication token, preparing to make API request");
        
        // Prepare request payload
        const payload = { keyword, searchType };
        console.log("Request payload:", payload);
        
        // Make API request
        console.log("Sending search request to API...");
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        console.log("API response status:", response.status, response.statusText);
        
        if (!response.ok) {
            let errorMessage = `Search failed with status ${response.status}`;
            try {
                const errorData = await response.json();
                console.error("API error response:", errorData);
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                console.error("Failed to parse error response:", e);
                // If parsing JSON fails, use the status text
                errorMessage = `${errorMessage}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        console.log("Parsing API response...");
        const responseData = await response.json();
        console.log("Search response received:", responseData);
        
        // Store results
        searchResults.clinicalTrials = responseData.clinical_trials || [];
        searchResults.fdaData = responseData.fda_data || [];
        
        console.log("Clinical trials data:", searchResults.clinicalTrials.length, "records");
        console.log("FDA data:", searchResults.fdaData.length, "records");
        
        // Update counts
        clinicalTrialsCount.textContent = searchResults.clinicalTrials.length;
        fdaCount.textContent = searchResults.fdaData.length;
        
        // Render results
        console.log("Rendering results...");
        renderClinicalTrials();
        renderFdaData();
        
        // Generate dashboard charts if we have data
        if (searchResults.clinicalTrials.length > 0 || searchResults.fdaData.length > 0) {
            dashboardWidgets.classList.remove('d-none');
            generateDashboardCharts();
        } else {
            dashboardWidgets.classList.add('d-none');
        }
        
        console.log("Search completed successfully");
    } catch (error) {
        console.error('Search error:', error);
        
        // Show error message to user
        clinicalTrialsPlaceholder.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <p class="mt-2">${error.message}</p>
            </div>
        `;
        clinicalTrialsPlaceholder.classList.remove('d-none');
        
        fdaPlaceholder.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <p class="mt-2">${error.message}</p>
            </div>
        `;
        fdaPlaceholder.classList.remove('d-none');
        
        // Hide dashboard widgets
        dashboardWidgets.classList.add('d-none');
    } finally {
        // Reset UI
        searchBtn.disabled = false;
        searchSpinner.classList.add('d-none');
    }
}

function renderClinicalTrials() {
    if (!searchResults.clinicalTrials || searchResults.clinicalTrials.length === 0) {
        clinicalTrialsContainer.innerHTML = '<div class="alert alert-info">No clinical trials found</div>';
        return;
    }
    
    try {
        console.log("Rendering clinical trials data:", searchResults.clinicalTrials.length, "records");
        
        const html = searchResults.clinicalTrials.map((trial, index) => {
            // Validate each trial object to prevent rendering errors
            const safeTrialData = {
                briefTitle: trial.briefTitle || 'Untitled Trial',
                nctId: trial.nctId || 'N/A',
                overallStatus: trial.overallStatus || 'Unknown',
                conditions: trial.conditions || 'Not specified',
                organization: trial.organization || 'Not specified',
                interventionDrug: trial.interventionDrug || 'Not specified',
                eligibilityCriteria: trial.eligibilityCriteria || 'Not specified',
                primaryOutcomes: trial.primaryOutcomes || 'Not specified',
                startDate: trial.startDate || null,
                completionDate: trial.completionDate || null
            };
            
            return `
                <div class="card data-card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(safeTrialData.briefTitle)}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">
                            ID: ${escapeHtml(safeTrialData.nctId)} | 
                            Status: ${escapeHtml(safeTrialData.overallStatus)}
                        </h6>
                        <p class="card-text">
                            <strong>Conditions:</strong> ${escapeHtml(safeTrialData.conditions)}
                        </p>
                        <p class="card-text">
                            <strong>Organization:</strong> ${escapeHtml(safeTrialData.organization)}
                        </p>
                        <button class="btn btn-sm btn-outline-primary" type="button" data-bs-toggle="collapse" data-bs-target="#trialDetails${index}">
                            Show Details
                        </button>
                        <div class="collapse mt-3" id="trialDetails${index}">
                            <div class="collapse-content">
                                <p><strong>Intervention:</strong> ${escapeHtml(safeTrialData.interventionDrug)}</p>
                                <p><strong>Eligibility:</strong> ${escapeHtml(truncateText(safeTrialData.eligibilityCriteria, 200))}</p>
                                <p><strong>Primary Outcomes:</strong> ${escapeHtml(truncateText(safeTrialData.primaryOutcomes, 200))}</p>
                                <p><strong>Start Date:</strong> ${formatDate(safeTrialData.startDate)}</p>
                                <p><strong>Completion Date:</strong> ${formatDate(safeTrialData.completionDate)}</p>
                                ${safeTrialData.nctId !== 'N/A' ? 
                                    `<a href="https://clinicaltrials.gov/study/${safeTrialData.nctId}" target="_blank" class="btn btn-sm btn-primary">View on ClinicalTrials.gov</a>` : 
                                    ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        clinicalTrialsContainer.innerHTML = html;
    } catch (error) {
        console.error("Error rendering clinical trials:", error);
        clinicalTrialsContainer.innerHTML = `
            <div class="alert alert-danger">
                <p>Error rendering clinical trials data: ${error.message}</p>
            </div>
        `;
    }
}

function renderFdaData() {
    if (!searchResults.fdaData || searchResults.fdaData.length === 0) {
        fdaContainer.innerHTML = '<div class="alert alert-info">No FDA data found</div>';
        return;
    }
    
    try {
        console.log("Rendering FDA data:", searchResults.fdaData.length, "records");
        
        const html = searchResults.fdaData.map((drug, index) => {
            // Validate each drug object to prevent rendering errors
            const safeDrugData = {
                brand_name: drug.brand_name || 'Unnamed Drug',
                generic_name: drug.generic_name || 'N/A',
                manufacturer_name: drug.manufacturer_name || 'Not specified',
                dosage_form: drug.dosage_form || 'Not specified',
                route: drug.route || 'Not specified',
                product_type: drug.product_type || 'Not specified',
                application_number: drug.application_number || 'Not specified',
                product_id: drug.product_id || 'Not specified'
            };
            
            return `
                <div class="card data-card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(safeDrugData.brand_name)}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">
                            Generic: ${escapeHtml(safeDrugData.generic_name)}
                        </h6>
                        <p class="card-text">
                            <strong>Manufacturer:</strong> ${escapeHtml(safeDrugData.manufacturer_name)}
                        </p>
                        <button class="btn btn-sm btn-outline-primary" type="button" data-bs-toggle="collapse" data-bs-target="#drugDetails${index}">
                            Show Details
                        </button>
                        <div class="collapse mt-3" id="drugDetails${index}">
                            <div class="collapse-content">
                                <p><strong>Dosage Form:</strong> ${escapeHtml(safeDrugData.dosage_form)}</p>
                                <p><strong>Route:</strong> ${escapeHtml(safeDrugData.route)}</p>
                                <p><strong>Product Type:</strong> ${escapeHtml(safeDrugData.product_type)}</p>
                                <p><strong>Application Number:</strong> ${escapeHtml(safeDrugData.application_number)}</p>
                                <p><strong>Product ID:</strong> ${escapeHtml(safeDrugData.product_id)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        fdaContainer.innerHTML = html;
    } catch (error) {
        console.error("Error rendering FDA data:", error);
        fdaContainer.innerHTML = `
            <div class="alert alert-danger">
                <p>Error rendering FDA data: ${error.message}</p>
            </div>
        `;
    }
}

function generateDashboardCharts() {
    // Status distribution chart
    const statusCtx = document.getElementById('status-chart').getContext('2d');
    const statusData = {};
    
    searchResults.clinicalTrials.forEach(trial => {
        const status = trial.overallStatus || 'Unknown';
        statusData[status] = (statusData[status] || 0) + 1;
    });
    
    const statusLabels = Object.keys(statusData);
    const statusValues = Object.values(statusData);
    const statusColors = generateColors(statusLabels.length);
    
    if (statusChart) {
        statusChart.destroy();
    }
    
    statusChart = new Chart(statusCtx, {
        type: 'pie',
        data: {
            labels: statusLabels,
            datasets: [{
                data: statusValues,
                backgroundColor: statusColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Trial Status Distribution'
                }
            }
        }
    });
    
    // Phases distribution chart
    const phasesCtx = document.getElementById('phases-chart').getContext('2d');
    const phasesData = {};
    
    searchResults.clinicalTrials.forEach(trial => {
        const phases = trial.phases || 'Not Specified';
        const phasesList = phases.split(',').map(p => p.trim());
        
        phasesList.forEach(phase => {
            if (phase) {
                phasesData[phase] = (phasesData[phase] || 0) + 1;
            }
        });
    });
    
    const phasesLabels = Object.keys(phasesData);
    const phasesValues = Object.values(phasesData);
    const phasesColors = generateColors(phasesLabels.length);
    
    if (phasesChart) {
        phasesChart.destroy();
    }
    
    phasesChart = new Chart(phasesCtx, {
        type: 'bar',
        data: {
            labels: phasesLabels,
            datasets: [{
                label: 'Number of Trials',
                data: phasesValues,
                backgroundColor: phasesColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Trial Phases Distribution'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

async function submitChatMessage(e) {
    e.preventDefault();
    
    const question = chatInput.value.trim();
    
    if (!question) return;
    
    try {
        // Add user message to chat
        addChatMessage('user', question);
        
        // Show loading indicator
        const loadingMessage = addChatMessage('ai', '<div class="loading-dots"><span>.</span><span>.</span><span>.</span></div>');
        
        // Get the current session token
        const session = await supabaseClient.auth.getSession();
        const token = session?.data?.session?.access_token;
        
        if (!token) {
            throw new Error('Authentication required. Please log in.');
        }
        
        // Send chat request to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                query: question,
                clinical_trials_data: searchResults.clinicalTrials || [],
                fda_data: searchResults.fdaData || [],
                chat_history: chatHistory || []
            })
        });
        
        // Remove loading indicator
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error("Chat API error:", errorData);
            
            // Display error message in chat
            addChatMessage('error', `Error: ${errorData.detail || 'Failed to process your request'}`);
            return;
        }
        
        try {
            const responseData = await response.json();
            
            // Validate response data
            if (!responseData || typeof responseData !== 'object') {
                throw new Error('Invalid response format');
            }
            
            const aiResponse = responseData.response || 'Sorry, I could not generate a response.';
            const sources = Array.isArray(responseData.sources) ? responseData.sources : [];
            
            // Add AI response to chat
            addChatMessage('ai', aiResponse, sources);
            
            // Add to chat history
            chatHistory.push({
                role: 'user',
                content: question
            });
            
            chatHistory.push({
                role: 'assistant',
                content: aiResponse,
                sources: JSON.stringify(sources)
            });
        } catch (parseError) {
            console.error("Chat response parsing error:", parseError);
            addChatMessage('error', 'Error: Failed to parse the response from the server.');
        }
    } catch (error) {
        console.error("Chat error:", error);
        
        // Remove loading indicator if it exists
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        // Display error message in chat
        addChatMessage('error', `Error: ${error.message || 'Failed to send your message'}`);
    }
}

function addChatMessage(role, content, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    
    // Handle different content types
    if (role === 'error') {
        // Error message styling
        messageDiv.className = 'chat-message error-message';
        const messageContent = document.createElement('p');
        messageContent.innerHTML = content;
        messageContent.className = 'error-text';
        messageDiv.appendChild(messageContent);
    } else {
        // Regular message or loading indicator
        const messageContent = document.createElement('p');
        
        // Check if content is HTML (for loading indicators)
        if (content.includes('<div class="loading-dots">')) {
            messageContent.innerHTML = content;
        } else {
            // Use innerHTML instead of textContent to support markdown
            messageContent.innerHTML = content;
        }
        
        messageDiv.appendChild(messageContent);
        
        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong> ';
            
            sources.forEach(source => {
                const sourceSpan = document.createElement('span');
                sourceSpan.className = 'source-item';
                
                if (source.type === 'clinical_trial') {
                    sourceSpan.textContent = `Trial: ${source.id}`;
                    if (source.url) {
                        const sourceLink = document.createElement('a');
                        sourceLink.href = source.url;
                        sourceLink.target = '_blank';
                        sourceLink.textContent = `Trial: ${source.id}`;
                        sourceSpan.textContent = '';
                        sourceSpan.appendChild(sourceLink);
                    }
                } else if (source.type === 'fda_data') {
                    sourceSpan.textContent = `Drug: ${source.name}`;
                } else {
                    // Generic source handling
                    sourceSpan.textContent = source.id || source.name || 'Source';
                }
                
                sourcesDiv.appendChild(sourceSpan);
                sourcesDiv.appendChild(document.createTextNode(' '));
            });
            
            messageDiv.appendChild(sourcesDiv);
        }
    }
    
    // Add to chat container
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Reset input field
    chatInput.value = '';
    chatInput.focus();
    
    return messageDiv; // Return the message div for potential removal (loading indicators)
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatDate(dateString) {
    if (!dateString) return 'Not specified';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    } catch (e) {
        return dateString;
    }
}

function generateColors(count) {
    const colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#5a5c69', '#6f42c1', '#fd7e14', '#20c9a6', '#858796'
    ];
    
    if (count <= colors.length) {
        return colors.slice(0, count);
    }
    
    // Generate more colors if needed
    const result = [...colors];
    for (let i = colors.length; i < count; i++) {
        const r = Math.floor(Math.random() * 200);
        const g = Math.floor(Math.random() * 200);
        const b = Math.floor(Math.random() * 200);
        result.push(`rgb(${r}, ${g}, ${b})`);
    }
    
    return result;
}
