/**
 * SportsCam Mobile App
 * Instagram-like interface for football highlights
 */

class MobileSportsCamApp {
 constructor() {
  this.apiUrl = 'http://localhost:5000/api';
  this.token = localStorage.getItem('token');
  this.user = JSON.parse(localStorage.getItem('user') || '{}');
  this.currentSection = 'feed';
  this.currentVideoIndex = 0;
  this.videos = [];
  this.isRecording = false;
  this.recordingTimer = null;
  this.recordingStartTime = null;

  this.init();
 }

 init() {
  this.setupEventListeners();
  this.setupSwipeGestures();
  this.checkAuth();
  this.loadContent();

  // Hide loading screen
  setTimeout(() => {
   document.getElementById('loading-screen').classList.add('hidden');
   document.getElementById('main-content').classList.remove('hidden');
  }, 1500);
 }

 setupEventListeners() {
  // Bottom navigation
  document.querySelectorAll('.nav-item').forEach(item => {
   item.addEventListener('click', (e) => {
    const section = e.currentTarget.dataset.section;
    this.showSection(section);
   });
  });

  // Floating record button
  document.getElementById('floating-record-btn').addEventListener('click', () => {
   this.showSection('record');
  });

  // Recording buttons
  document.getElementById('quick-record-btn').addEventListener('click', () => {
   this.startQuickRecord();
  });

  document.getElementById('custom-record-btn').addEventListener('click', () => {
   this.startCustomRecord();
  });

  document.getElementById('mobile-stop-recording').addEventListener('click', () => {
   this.stopRecording();
  });

  // Profile navigation
  document.getElementById('back-to-feed').addEventListener('click', () => {
   this.showSection('feed');
  });

  // Share modal
  document.getElementById('close-share-modal').addEventListener('click', () => {
   this.hideShareModal();
  });

  // Search
  document.getElementById('search-input').addEventListener('input', (e) => {
   this.handleSearch(e.target.value);
  });

  // Video interactions
  document.addEventListener('click', (e) => {
   if (e.target.classList.contains('like-btn')) {
    this.likeVideo(e.target.dataset.videoId);
   } else if (e.target.classList.contains('share-btn')) {
    this.showShareModal(e.target.dataset.videoId);
   } else if (e.target.classList.contains('comment-btn')) {
    this.showComments(e.target.dataset.videoId);
   }
  });
 }

 setupSwipeGestures() {
  let startY = 0;
  let startX = 0;

  document.addEventListener('touchstart', (e) => {
   startY = e.touches[0].clientY;
   startX = e.touches[0].clientX;
  });

  document.addEventListener('touchend', (e) => {
   if (!e.changedTouches[0]) return;

   const endY = e.changedTouches[0].clientY;
   const endX = e.changedTouches[0].clientX;
   const diffY = startY - endY;
   const diffX = startX - endX;

   // Vertical swipe for video navigation
   if (Math.abs(diffY) > Math.abs(diffX) && Math.abs(diffY) > 50) {
    if (this.currentSection === 'feed') {
     if (diffY > 0) {
      // Swipe up - next video
      this.nextVideo();
     } else {
      // Swipe down - previous video
      this.previousVideo();
     }
    }
   }

   // Horizontal swipe for section navigation
   if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 100) {
    if (diffX > 0) {
     // Swipe left
     this.swipeLeft();
    } else {
     // Swipe right
     this.swipeRight();
    }
   }
  });
 }

 checkAuth() {
  if (!this.token) {
   // Redirect to login or show login modal
   this.showLoginPrompt();
  } else {
   this.updateUserInterface();
  }
 }

 showLoginPrompt() {
  // Simple login prompt for mobile
  const username = prompt('Enter your username:');
  const password = prompt('Enter your password:');

  if (username && password) {
   this.login(username, password);
  }
 }

 async login(email, password) {
  try {
   const response = await this.apiCall('/login', 'POST', { email, password });

   this.token = response.access_token;
   this.user = response.user;

   localStorage.setItem('token', this.token);
   localStorage.setItem('user', JSON.stringify(this.user));

   this.updateUserInterface();
   this.showToast('Login successful!', 'success');

  } catch (error) {
   this.showToast('Login failed: ' + error.message, 'error');
  }
 }

 updateUserInterface() {
  document.getElementById('profile-username').textContent = this.user.username || 'User';
  document.getElementById('profile-avatar').src = this.user.avatar || 'https://via.placeholder.com/100';
 }

 showSection(section) {
  // Update navigation
  document.querySelectorAll('.nav-item').forEach(item => {
   item.classList.remove('active');
  });
  document.querySelector(`[data-section="${section}"]`).classList.add('active');

  // Hide all sections
  document.querySelectorAll('[id$="-section"]').forEach(el => {
   el.classList.add('hidden');
  });

  // Show selected section
  this.currentSection = section;

  switch (section) {
   case 'feed':
    document.getElementById('stories-section').classList.remove('hidden');
    document.getElementById('video-feed').classList.remove('hidden');
    this.loadVideoFeed();
    break;
   case 'search':
    document.getElementById('search-section').classList.remove('hidden');
    break;
   case 'record':
    document.getElementById('recording-section').classList.remove('hidden');
    this.loadRecordingOptions();
    break;
   case 'profile':
    document.getElementById('profile-section').classList.remove('hidden');
    this.loadProfile();
    break;
   case 'notifications':
    this.showToast('Notifications coming soon!', 'info');
    break;
  }
 }

 async loadContent() {
  await this.loadVideoFeed();
  await this.loadStories();
 }

 async loadVideoFeed() {
  try {
   const response = await this.apiCall('/highlights?per_page=20');
   this.videos = response.highlights || [];
   this.renderVideoFeed();
  } catch (error) {
   console.error('Failed to load video feed:', error);
   this.showToast('Failed to load videos', 'error');
  }
 }

 renderVideoFeed() {
  const feed = document.getElementById('video-feed');
  feed.innerHTML = '';

  this.videos.forEach((video, index) => {
   const videoElement = this.createVideoElement(video, index);
   feed.appendChild(videoElement);
  });

  // Show first video
  if (this.videos.length > 0) {
   this.showVideo(0);
  }
 }

 createVideoElement(video, index) {
  const videoPost = document.createElement('div');
  videoPost.className = 'video-post';
  videoPost.style.display = index === 0 ? 'block' : 'none';

  videoPost.innerHTML = `
            <video 
                id="video-${index}"
                loop 
                muted 
                playsinline
                poster="${video.thumbnail_path}"
                ${index === 0 ? 'autoplay' : ''}
            >
                <source src="${video.video_path}" type="video/mp4">
            </video>
            
            <div class="video-overlay">
                <div class="flex items-center mb-2">
                    <img src="https://via.placeholder.com/40" class="w-8 h-8 rounded-full mr-3">
                    <span class="font-semibold">${video.creator || 'Player'}</span>
                </div>
                <p class="text-sm mb-2">${video.title}</p>
                <p class="text-xs text-gray-300">${video.description}</p>
                
                <div class="flex flex-wrap gap-1 mt-2">
                    ${video.tags ? video.tags.map(tag =>
   `<span class="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">#${tag}</span>`
  ).join('') : ''}
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="action-btn like-btn" data-video-id="${video.id}">
                    <i class="fas fa-heart"></i>
                    <div class="text-xs mt-1">${video.likes || 0}</div>
                </button>
                
                <button class="action-btn comment-btn" data-video-id="${video.id}">
                    <i class="fas fa-comment"></i>
                    <div class="text-xs mt-1">${video.comments || 0}</div>
                </button>
                
                <button class="action-btn share-btn" data-video-id="${video.id}">
                    <i class="fas fa-share"></i>
                    <div class="text-xs mt-1">Share</div>
                </button>
                
                <button class="action-btn">
                    <i class="fas fa-bookmark"></i>
                    <div class="text-xs mt-1">Save</div>
                </button>
            </div>
            
            ${index === 0 ? '<div class="swipe-indicator"><i class="fas fa-chevron-up"></i></div>' : ''}
        `;

  return videoPost;
 }

 showVideo(index) {
  // Hide all videos
  document.querySelectorAll('.video-post').forEach(post => {
   post.style.display = 'none';
   const video = post.querySelector('video');
   if (video) video.pause();
  });

  // Show current video
  const currentPost = document.querySelectorAll('.video-post')[index];
  if (currentPost) {
   currentPost.style.display = 'block';
   const video = currentPost.querySelector('video');
   if (video) {
    video.currentTime = 0;
    video.play().catch(e => console.log('Video play failed:', e));
   }
  }

  this.currentVideoIndex = index;
 }

 nextVideo() {
  if (this.currentVideoIndex < this.videos.length - 1) {
   this.showVideo(this.currentVideoIndex + 1);
  }
 }

 previousVideo() {
  if (this.currentVideoIndex > 0) {
   this.showVideo(this.currentVideoIndex - 1);
  }
 }

 swipeLeft() {
  // Could be used for additional features
  console.log('Swiped left');
 }

 swipeRight() {
  // Could be used for additional features
  console.log('Swiped right');
 }

 async loadStories() {
  // Load user stories (recent highlights as stories)
  try {
   const response = await this.apiCall('/highlights?per_page=10&recent=true');
   this.renderStories(response.highlights || []);
  } catch (error) {
   console.error('Failed to load stories:', error);
  }
 }

 renderStories(stories) {
  const container = document.getElementById('stories-container');
  container.innerHTML = '';

  stories.forEach(story => {
   const storyElement = document.createElement('div');
   storyElement.className = 'story-item mr-3';

   storyElement.innerHTML = `
                <div class="w-16 h-16 rounded-full bg-gradient-to-br from-pink-500 to-yellow-500 p-0.5">
                    <img src="${story.thumbnail_path}" class="w-full h-full rounded-full object-cover">
                </div>
                <p class="text-white text-xs text-center mt-1 truncate">${story.creator || 'Player'}</p>
            `;

   storyElement.addEventListener('click', () => {
    this.viewStory(story);
   });

   container.appendChild(storyElement);
  });
 }

 viewStory(story) {
  // Simple story viewer - could be enhanced with full-screen experience
  this.showToast(`Viewing ${story.title}`, 'info');
 }

 async loadProfile() {
  try {
   // Load user's highlights
   const response = await this.apiCall(`/highlights?user_id=${this.user.id}`);
   this.renderProfileHighlights(response.highlights || []);

   // Update profile stats
   document.getElementById('profile-highlights-count').textContent = response.total || 0;

  } catch (error) {
   console.error('Failed to load profile:', error);
  }
 }

 renderProfileHighlights(highlights) {
  const grid = document.getElementById('profile-highlights');
  grid.innerHTML = '';

  highlights.forEach(highlight => {
   const item = document.createElement('div');
   item.className = 'aspect-square bg-gray-800 rounded';

   item.innerHTML = `
                <img src="${highlight.thumbnail_path}" class="w-full h-full object-cover rounded">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 hover:opacity-100 transition-opacity">
                    <i class="fas fa-play text-white text-xl"></i>
                </div>
            `;

   item.addEventListener('click', () => {
    this.viewHighlight(highlight);
   });

   grid.appendChild(item);
  });
 }

 viewHighlight(highlight) {
  // Switch to feed and show this highlight
  this.showSection('feed');
  const index = this.videos.findIndex(v => v.id === highlight.id);
  if (index !== -1) {
   this.showVideo(index);
  }
 }

 async loadRecordingOptions() {
  try {
   // Load available turfs
   const turfs = await this.apiCall('/turfs');
   const onlineTurfs = turfs.filter(t => t.camera_status === 'online');

   if (onlineTurfs.length === 0) {
    this.showToast('No cameras available for recording', 'warning');
   }

  } catch (error) {
   console.error('Failed to load recording options:', error);
  }
 }

 async startQuickRecord() {
  try {
   // Start a quick 1-hour recording
   const response = await this.apiCall('/camera/1/start', 'POST', {
    session_name: 'Quick Game Session',
    duration: 60
   });

   this.isRecording = true;
   this.recordingStartTime = Date.now();
   this.showRecordingStatus();
   this.startRecordingTimer();

   this.showToast('Recording started!', 'success');

  } catch (error) {
   this.showToast('Failed to start recording: ' + error.message, 'error');
  }
 }

 async startCustomRecord() {
  const sessionName = document.getElementById('mobile-session-name').value;
  const duration = document.getElementById('mobile-duration').value;

  try {
   const response = await this.apiCall('/camera/1/start', 'POST', {
    session_name: sessionName || 'Game Session',
    duration: parseInt(duration)
   });

   this.isRecording = true;
   this.recordingStartTime = Date.now();
   this.showRecordingStatus();
   this.startRecordingTimer();

   this.showToast('Recording started!', 'success');

  } catch (error) {
   this.showToast('Failed to start recording: ' + error.message, 'error');
  }
 }

 showRecordingStatus() {
  document.getElementById('active-recordings').classList.remove('hidden');
  document.getElementById('quick-record-btn').classList.add('hidden');
  document.getElementById('custom-record-btn').classList.add('hidden');
 }

 startRecordingTimer() {
  this.recordingTimer = setInterval(() => {
   if (!this.isRecording) return;

   const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
   const hours = Math.floor(elapsed / 3600);
   const minutes = Math.floor((elapsed % 3600) / 60);
   const seconds = elapsed % 60;

   document.getElementById('mobile-recording-timer').textContent =
    `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }, 1000);
 }

 async stopRecording() {
  try {
   await this.apiCall('/camera/1/stop', 'POST');

   this.isRecording = false;
   if (this.recordingTimer) {
    clearInterval(this.recordingTimer);
    this.recordingTimer = null;
   }

   document.getElementById('active-recordings').classList.add('hidden');
   document.getElementById('quick-record-btn').classList.remove('hidden');
   document.getElementById('custom-record-btn').classList.remove('hidden');

   this.showToast('Recording stopped. Processing highlights...', 'info');

  } catch (error) {
   this.showToast('Failed to stop recording: ' + error.message, 'error');
  }
 }

 async likeVideo(videoId) {
  try {
   await this.apiCall(`/highlights/${videoId}/like`, 'POST');

   // Update UI
   const likeBtn = document.querySelector(`[data-video-id="${videoId}"].like-btn`);
   if (likeBtn) {
    const countElement = likeBtn.querySelector('.text-xs');
    const currentCount = parseInt(countElement.textContent) || 0;
    countElement.textContent = currentCount + 1;

    // Add animation
    likeBtn.classList.add('text-red-500');
    setTimeout(() => likeBtn.classList.remove('text-red-500'), 300);
   }

  } catch (error) {
   this.showToast('Failed to like video', 'error');
  }
 }

 showShareModal(videoId) {
  document.getElementById('share-modal').classList.remove('hidden');

  // Handle share options
  document.querySelectorAll('.share-option').forEach(option => {
   option.onclick = () => {
    this.shareVideo(videoId, option.textContent.trim());
   };
  });
 }

 hideShareModal() {
  document.getElementById('share-modal').classList.add('hidden');
 }

 async shareVideo(videoId, platform) {
  const video = this.videos.find(v => v.id === videoId);
  if (!video) return;

  const url = `${window.location.origin}/highlight/${videoId}`;
  const text = `Check out this amazing football highlight: ${video.title}`;

  switch (platform) {
   case 'Instagram':
    // Instagram sharing would require their API
    this.showToast('Instagram sharing coming soon!', 'info');
    break;

   case 'TikTok':
    // TikTok sharing would require their API
    this.showToast('TikTok sharing coming soon!', 'info');
    break;

   case 'WhatsApp':
    window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`);
    break;

   case 'Copy Link':
    if (navigator.clipboard) {
     await navigator.clipboard.writeText(url);
     this.showToast('Link copied to clipboard!', 'success');
    }
    break;
  }

  this.hideShareModal();
 }

 showComments(videoId) {
  // Simple comments implementation
  this.showToast('Comments coming soon!', 'info');
 }

 handleSearch(query) {
  if (query.length < 2) return;

  // Simple search implementation
  const filteredVideos = this.videos.filter(video =>
   video.title.toLowerCase().includes(query.toLowerCase()) ||
   video.description.toLowerCase().includes(query.toLowerCase()) ||
   (video.tags && video.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase())))
  );

  this.renderSearchResults(filteredVideos);
 }

 renderSearchResults(results) {
  const container = document.getElementById('search-results');
  container.innerHTML = '';

  if (results.length === 0) {
   container.innerHTML = '<p class="text-gray-400 text-center py-8">No results found</p>';
   return;
  }

  results.forEach(video => {
   const item = document.createElement('div');
   item.className = 'flex items-center p-3 border-b border-gray-800';

   item.innerHTML = `
                <img src="${video.thumbnail_path}" class="w-16 h-16 rounded object-cover mr-3">
                <div class="flex-1">
                    <h4 class="font-semibold">${video.title}</h4>
                    <p class="text-gray-400 text-sm">${video.description}</p>
                    <div class="flex space-x-4 text-xs text-gray-500 mt-1">
                        <span><i class="fas fa-heart mr-1"></i>${video.likes || 0}</span>
                        <span><i class="fas fa-eye mr-1"></i>${video.views || 0}</span>
                    </div>
                </div>
            `;

   item.addEventListener('click', () => {
    this.viewHighlight(video);
   });

   container.appendChild(item);
  });
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
  const container = document.getElementById('mobile-toast-container');
  const toast = document.createElement('div');

  const colors = {
   success: 'bg-green-500',
   error: 'bg-red-500',
   warning: 'bg-yellow-500',
   info: 'bg-blue-500'
  };

  toast.className = `${colors[type]} text-white px-4 py-2 rounded-lg shadow-lg transform transition-transform duration-300 -translate-y-full`;
  toast.textContent = message;

  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
   toast.classList.remove('-translate-y-full');
  }, 100);

  // Remove after 3 seconds
  setTimeout(() => {
   toast.classList.add('-translate-y-full');
   setTimeout(() => {
    if (container.contains(toast)) {
     container.removeChild(toast);
    }
   }, 300);
  }, 3000);
 }
}

// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
 window.addEventListener('load', () => {
  navigator.serviceWorker.register('/sw.js')
   .then(registration => {
    console.log('SW registered: ', registration);
   })
   .catch(registrationError => {
    console.log('SW registration failed: ', registrationError);
   });
 });
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
 window.mobileApp = new MobileSportsCamApp();
});

// Handle app installation prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
 e.preventDefault();
 deferredPrompt = e;

 // Show install button or prompt
 console.log('App can be installed');
});

// Handle app installation
window.addEventListener('appinstalled', (evt) => {
 console.log('App was installed');
});
