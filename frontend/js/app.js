/**
 * SportsCam Frontend Application
 * Handles user interface, API communication, and real-time updates
 */

class SportsCamApp {
 constructor() {
  this.apiUrl = 'http://localhost:5000/api';
  this.token = localStorage.getItem('token');
  this.user = JSON.parse(localStorage.getItem('user') || '{}');
  this.currentSection = 'dashboard';
  this.recordingTimer = null;
  this.recordingStartTime = null;

  this.init();
 }

 init() {
  this.setupEventListeners();
  this.checkAuth();
  this.loadDashboard();
 }

 setupEventListeners() {
  // Navigation
  document.querySelectorAll('nav a[href^="#"]').forEach(link => {
   link.addEventListener('click', (e) => {
    e.preventDefault();
    const section = e.target.getAttribute('href').substring(1);
    this.showSection(section);
   });
  });

  // Authentication
  document.getElementById('login-tab').addEventListener('click', () => this.showLoginForm());
  document.getElementById('register-tab').addEventListener('click', () => this.showRegisterForm());
  document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
  document.getElementById('register-form').addEventListener('submit', (e) => this.handleRegister(e));
  document.getElementById('logout-btn').addEventListener('click', () => this.logout());

  // User menu
  document.getElementById('user-menu-btn').addEventListener('click', () => {
   document.getElementById('user-menu').classList.toggle('hidden');
  });

  // Quick actions
  document.getElementById('start-recording-btn').addEventListener('click', () => this.showRecordingModal());
  document.getElementById('view-highlights-btn').addEventListener('click', () => this.showSection('highlights'));
  document.getElementById('manage-turfs-btn').addEventListener('click', () => this.showSection('turfs'));

  // Recording modal
  document.getElementById('cancel-recording').addEventListener('click', () => this.hideRecordingModal());
  document.getElementById('confirm-recording').addEventListener('click', () => this.startRecording());
  document.getElementById('stop-recording').addEventListener('click', () => this.stopRecording());

  // Turf management
  document.getElementById('add-turf-btn').addEventListener('click', () => this.showAddTurfModal());

  // Highlights
  document.getElementById('refresh-highlights').addEventListener('click', () => this.loadHighlights());

  // Close modals when clicking outside
  window.addEventListener('click', (e) => {
   if (e.target.classList.contains('fixed')) {
    e.target.classList.add('hidden');
   }
  });
 }

 checkAuth() {
  if (!this.token) {
   this.showLoginModal();
  } else {
   this.hideLoginModal();
   this.updateUserInterface();
  }
 }

 showLoginModal() {
  document.getElementById('login-modal').classList.remove('hidden');
 }

 hideLoginModal() {
  document.getElementById('login-modal').classList.add('hidden');
 }

 showLoginForm() {
  document.getElementById('login-tab').className = 'flex-1 py-2 px-4 bg-blue-500 text-white rounded-l-md';
  document.getElementById('register-tab').className = 'flex-1 py-2 px-4 bg-gray-200 text-gray-700 rounded-r-md';
  document.getElementById('login-form').classList.remove('hidden');
  document.getElementById('register-form').classList.add('hidden');
 }

 showRegisterForm() {
  document.getElementById('login-tab').className = 'flex-1 py-2 px-4 bg-gray-200 text-gray-700 rounded-l-md';
  document.getElementById('register-tab').className = 'flex-1 py-2 px-4 bg-blue-500 text-white rounded-r-md';
  document.getElementById('login-form').classList.add('hidden');
  document.getElementById('register-form').classList.remove('hidden');
 }

 async handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
   const response = await this.apiCall('/login', 'POST', { email, password });

   this.token = response.access_token;
   this.user = response.user;

   localStorage.setItem('token', this.token);
   localStorage.setItem('user', JSON.stringify(this.user));

   this.hideLoginModal();
   this.updateUserInterface();
   this.showToast('Login successful!', 'success');

  } catch (error) {
   this.showToast('Login failed: ' + error.message, 'error');
  }
 }

 async handleRegister(e) {
  e.preventDefault();

  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;
  const role = document.getElementById('register-role').value;

  try {
   const response = await this.apiCall('/register', 'POST', {
    username, email, password, role
   });

   this.token = response.access_token;
   this.user = response.user;

   localStorage.setItem('token', this.token);
   localStorage.setItem('user', JSON.stringify(this.user));

   this.hideLoginModal();
   this.updateUserInterface();
   this.showToast('Registration successful!', 'success');

  } catch (error) {
   this.showToast('Registration failed: ' + error.message, 'error');
  }
 }

 logout() {
  this.token = null;
  this.user = {};
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  this.showLoginModal();
  this.showToast('Logged out successfully', 'info');
 }

 updateUserInterface() {
  document.getElementById('user-name').textContent = this.user.username || 'User';

  // Show/hide features based on role
  if (this.user.role === 'turf_owner' || this.user.role === 'admin') {
   document.getElementById('add-turf-btn').classList.remove('hidden');
   document.getElementById('manage-turfs-btn').classList.remove('hidden');
  }
 }

 showSection(section) {
  // Hide all sections
  document.querySelectorAll('[id$="-section"]').forEach(el => {
   el.classList.add('hidden');
  });

  // Show selected section
  document.getElementById(section + '-section').classList.remove('hidden');
  this.currentSection = section;

  // Load section data
  switch (section) {
   case 'dashboard':
    this.loadDashboard();
    break;
   case 'turfs':
    this.loadTurfs();
    break;
   case 'highlights':
    this.loadHighlights();
    break;
   case 'social':
    this.loadSocialFeed();
    break;
  }
 }

 async loadDashboard() {
  try {
   // Load dashboard statistics
   const [turfs, sessions, highlights] = await Promise.all([
    this.apiCall('/turfs'),
    this.apiCall('/sessions'),
    this.apiCall('/highlights')
   ]);

   // Update stats
   document.getElementById('active-cameras').textContent =
    turfs.filter(t => t.camera_status === 'online').length;
   document.getElementById('recording-sessions').textContent =
    sessions.filter(s => s.status === 'recording').length;
   document.getElementById('total-highlights').textContent = highlights.total || 0;
   document.getElementById('active-players').textContent =
    sessions.reduce((acc, s) => acc + (s.players || 0), 0);

  } catch (error) {
   console.error('Failed to load dashboard:', error);
  }
 }

 async loadTurfs() {
  try {
   const turfs = await this.apiCall('/turfs');
   this.renderTurfs(turfs);
  } catch (error) {
   this.showToast('Failed to load turfs: ' + error.message, 'error');
  }
 }

 renderTurfs(turfs) {
  const grid = document.getElementById('turfs-grid');
  grid.innerHTML = '';

  turfs.forEach(turf => {
   const card = document.createElement('div');
   card.className = 'bg-white border rounded-lg p-6 card-hover';

   const statusColor = turf.camera_status === 'online' ? 'green' : 'red';

   card.innerHTML = `
                <div class="flex justify-between items-start mb-4">
                    <h4 class="text-lg font-semibold">${turf.name}</h4>
                    <span class="px-2 py-1 text-xs rounded-full bg-${statusColor}-100 text-${statusColor}-800">
                        ${turf.camera_status}
                    </span>
                </div>
                <p class="text-gray-600 mb-4">${turf.address}</p>
                <div class="flex space-x-2">
                    <button onclick="app.controlCamera(${turf.id}, 'start')" 
                            class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600">
                        <i class="fas fa-play mr-1"></i>Start
                    </button>
                    <button onclick="app.controlCamera(${turf.id}, 'stop')" 
                            class="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600">
                        <i class="fas fa-stop mr-1"></i>Stop
                    </button>
                    <button onclick="app.viewTurfDetails(${turf.id})" 
                            class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                        <i class="fas fa-eye mr-1"></i>Details
                    </button>
                </div>
            `;

   grid.appendChild(card);
  });
 }

 async loadHighlights() {
  try {
   const response = await this.apiCall('/highlights');
   this.renderHighlights(response.highlights);
  } catch (error) {
   this.showToast('Failed to load highlights: ' + error.message, 'error');
  }
 }

 renderHighlights(highlights) {
  const grid = document.getElementById('highlights-grid');
  grid.innerHTML = '';

  highlights.forEach(highlight => {
   const card = document.createElement('div');
   card.className = 'bg-white border rounded-lg overflow-hidden card-hover';

   card.innerHTML = `
                <div class="video-container">
                    <video controls poster="${highlight.thumbnail_path}">
                        <source src="${highlight.video_path}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="p-4">
                    <h4 class="font-semibold mb-2">${highlight.title}</h4>
                    <p class="text-gray-600 text-sm mb-2">${highlight.description}</p>
                    <div class="flex justify-between items-center">
                        <div class="flex space-x-4 text-sm text-gray-500">
                            <span><i class="fas fa-heart mr-1"></i>${highlight.likes}</span>
                            <span><i class="fas fa-eye mr-1"></i>${highlight.views}</span>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="app.likeHighlight(${highlight.id})" 
                                    class="text-red-500 hover:text-red-600">
                                <i class="fas fa-heart"></i>
                            </button>
                            <button onclick="app.shareHighlight(${highlight.id})" 
                                    class="text-blue-500 hover:text-blue-600">
                                <i class="fas fa-share"></i>
                            </button>
                        </div>
                    </div>
                    <div class="mt-2">
                        ${highlight.tags ? highlight.tags.map(tag =>
    `<span class="inline-block bg-gray-200 text-gray-700 px-2 py-1 text-xs rounded mr-1">${tag}</span>`
   ).join('') : ''}
                    </div>
                </div>
            `;

   grid.appendChild(card);
  });
 }

 async loadSocialFeed() {
  try {
   const response = await this.apiCall('/social/feed');
   this.renderSocialFeed(response.feed);
  } catch (error) {
   this.showToast('Failed to load social feed: ' + error.message, 'error');
  }
 }

 renderSocialFeed(posts) {
  const feed = document.getElementById('social-feed');
  feed.innerHTML = '';

  posts.forEach(post => {
   const postElement = document.createElement('div');
   postElement.className = 'border rounded-lg p-4 bg-white';

   postElement.innerHTML = `
                <div class="flex items-center mb-3">
                    <img src="https://via.placeholder.com/40" alt="${post.user.username}" 
                         class="w-10 h-10 rounded-full mr-3">
                    <div>
                        <h5 class="font-semibold">${post.user.username}</h5>
                        <p class="text-gray-500 text-sm">${new Date(post.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
                
                ${post.caption ? `<p class="mb-3">${post.caption}</p>` : ''}
                
                <div class="video-container mb-3">
                    <video controls poster="${post.highlight.thumbnail_path}">
                        <source src="${post.highlight.video_path}" type="video/mp4">
                    </video>
                </div>
                
                <div class="flex justify-between items-center">
                    <div class="flex space-x-4">
                        <button class="flex items-center text-gray-600 hover:text-red-500">
                            <i class="fas fa-heart mr-1"></i>${post.likes}
                        </button>
                        <button class="flex items-center text-gray-600 hover:text-blue-500">
                            <i class="fas fa-comment mr-1"></i>${post.comments_count}
                        </button>
                        <button class="flex items-center text-gray-600 hover:text-green-500">
                            <i class="fas fa-share mr-1"></i>${post.shares_count}
                        </button>
                    </div>
                    <div class="text-sm text-gray-500">
                        ${post.highlight.tags ? post.highlight.tags.map(tag =>
    `#${tag}`
   ).join(' ') : ''}
                    </div>
                </div>
            `;

   feed.appendChild(postElement);
  });
 }

 showRecordingModal() {
  this.loadTurfsForRecording();
  document.getElementById('recording-modal').classList.remove('hidden');
 }

 hideRecordingModal() {
  document.getElementById('recording-modal').classList.add('hidden');
  document.getElementById('recording-status').classList.add('hidden');
  if (this.recordingTimer) {
   clearInterval(this.recordingTimer);
   this.recordingTimer = null;
  }
 }

 async loadTurfsForRecording() {
  try {
   const turfs = await this.apiCall('/turfs');
   const select = document.getElementById('recording-turf-select');
   select.innerHTML = '';

   turfs.filter(t => t.camera_status === 'online').forEach(turf => {
    const option = document.createElement('option');
    option.value = turf.id;
    option.textContent = turf.name;
    select.appendChild(option);
   });

  } catch (error) {
   this.showToast('Failed to load turfs: ' + error.message, 'error');
  }
 }

 async startRecording() {
  const turfId = document.getElementById('recording-turf-select').value;
  const sessionName = document.getElementById('session-name').value;
  const duration = document.getElementById('session-duration').value;

  if (!turfId) {
   this.showToast('Please select a turf', 'error');
   return;
  }

  try {
   const response = await this.apiCall(`/camera/${turfId}/start`, 'POST', {
    session_name: sessionName || 'Game Session',
    duration: parseInt(duration)
   });

   // Show recording status
   document.getElementById('recording-status').classList.remove('hidden');
   this.recordingStartTime = Date.now();

   // Start timer
   this.recordingTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;

    document.getElementById('recording-timer').textContent =
     `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
   }, 1000);

   this.showToast('Recording started successfully!', 'success');

  } catch (error) {
   this.showToast('Failed to start recording: ' + error.message, 'error');
  }
 }

 async stopRecording() {
  const turfId = document.getElementById('recording-turf-select').value;

  try {
   await this.apiCall(`/camera/${turfId}/stop`, 'POST');

   this.hideRecordingModal();
   this.showToast('Recording stopped. Processing highlights...', 'info');

  } catch (error) {
   this.showToast('Failed to stop recording: ' + error.message, 'error');
  }
 }

 async controlCamera(turfId, action) {
  try {
   if (action === 'start') {
    // Use the recording modal for better UX
    document.getElementById('recording-turf-select').value = turfId;
    this.showRecordingModal();
   } else if (action === 'stop') {
    await this.apiCall(`/camera/${turfId}/stop`, 'POST');
    this.showToast('Recording stopped', 'info');
   }
  } catch (error) {
   this.showToast(`Failed to ${action} camera: ${error.message}`, 'error');
  }
 }

 async likeHighlight(highlightId) {
  try {
   await this.apiCall(`/highlights/${highlightId}/like`, 'POST');
   this.loadHighlights(); // Refresh to show updated likes
  } catch (error) {
   this.showToast('Failed to like highlight: ' + error.message, 'error');
  }
 }

 async shareHighlight(highlightId) {
  // Simple share functionality - in production, integrate with social media APIs
  const url = `${window.location.origin}/highlight/${highlightId}`;

  if (navigator.share) {
   try {
    await navigator.share({
     title: 'Check out this football highlight!',
     url: url
    });
   } catch (error) {
    console.log('Share cancelled');
   }
  } else {
   // Fallback: copy to clipboard
   navigator.clipboard.writeText(url);
   this.showToast('Link copied to clipboard!', 'success');
  }
 }

 async apiCall(endpoint, method = 'GET', data = null) {
  const url = this.apiUrl + endpoint;
  const options = {
   method,
   headers: {
    'Content-Type': 'application/json'
   }
  };

  if (this.token) {
   options.headers['Authorization'] = `Bearer ${this.token}`;
  }

  if (data) {
   options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
   const error = await response.json();
   throw new Error(error.error || 'API request failed');
  }

  return await response.json();
 }

 showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');

  const colors = {
   success: 'bg-green-500',
   error: 'bg-red-500',
   warning: 'bg-yellow-500',
   info: 'bg-blue-500'
  };

  toast.className = `${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg transform transition-transform duration-300 translate-x-full`;
  toast.textContent = message;

  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
   toast.classList.remove('translate-x-full');
  }, 100);

  // Remove after 5 seconds
  setTimeout(() => {
   toast.classList.add('translate-x-full');
   setTimeout(() => {
    container.removeChild(toast);
   }, 300);
  }, 5000);
 }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
 window.app = new SportsCamApp();
});
