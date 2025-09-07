/**
 * Service Worker for SportsCam PWA
 * Handles caching, offline functionality, and background sync
 */

const CACHE_NAME = 'sportscam-v1.0.0';
const STATIC_CACHE = 'sportscam-static-v1.0.0';
const DYNAMIC_CACHE = 'sportscam-dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
 '/mobile.html',
 '/index.html',
 '/js/mobile-app.js',
 '/js/app.js',
 '/manifest.json',
 '/icons/icon-192x192.png',
 '/icons/icon-512x512.png',
 'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
 /\/api\/highlights/,
 /\/api\/turfs/,
 /\/api\/sessions/
];

// Install event - cache static files
self.addEventListener('install', (event) => {
 console.log('Service Worker: Installing...');

 event.waitUntil(
  caches.open(STATIC_CACHE)
   .then(cache => {
    console.log('Service Worker: Caching static files');
    return cache.addAll(STATIC_FILES);
   })
   .then(() => {
    console.log('Service Worker: Static files cached');
    return self.skipWaiting();
   })
   .catch(error => {
    console.error('Service Worker: Error caching static files', error);
   })
 );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
 console.log('Service Worker: Activating...');

 event.waitUntil(
  caches.keys()
   .then(cacheNames => {
    return Promise.all(
     cacheNames.map(cacheName => {
      if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
       console.log('Service Worker: Deleting old cache', cacheName);
       return caches.delete(cacheName);
      }
     })
    );
   })
   .then(() => {
    console.log('Service Worker: Activated');
    return self.clients.claim();
   })
 );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
 const { request } = event;
 const url = new URL(request.url);

 // Handle different types of requests
 if (request.method === 'GET') {
  if (isStaticFile(request.url)) {
   // Static files - cache first strategy
   event.respondWith(cacheFirst(request));
  } else if (isAPIRequest(request.url)) {
   // API requests - network first with cache fallback
   event.respondWith(networkFirstWithCache(request));
  } else if (isVideoRequest(request.url)) {
   // Video files - cache with range support
   event.respondWith(handleVideoRequest(request));
  } else {
   // Other requests - network first
   event.respondWith(networkFirst(request));
  }
 }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
 console.log('Service Worker: Background sync', event.tag);

 if (event.tag === 'like-highlight') {
  event.waitUntil(syncLikes());
 } else if (event.tag === 'upload-highlight') {
  event.waitUntil(syncUploads());
 }
});

// Push notifications
self.addEventListener('push', (event) => {
 console.log('Service Worker: Push notification received');

 const options = {
  body: event.data ? event.data.text() : 'New highlight available!',
  icon: '/icons/icon-192x192.png',
  badge: '/icons/badge-72x72.png',
  vibrate: [200, 100, 200],
  data: {
   url: '/mobile.html'
  },
  actions: [
   {
    action: 'view',
    title: 'View Highlight',
    icon: '/icons/view-action.png'
   },
   {
    action: 'dismiss',
    title: 'Dismiss',
    icon: '/icons/dismiss-action.png'
   }
  ]
 };

 event.waitUntil(
  self.registration.showNotification('SportsCam', options)
 );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
 console.log('Service Worker: Notification clicked');

 event.notification.close();

 if (event.action === 'view') {
  event.waitUntil(
   clients.openWindow(event.notification.data.url || '/mobile.html')
  );
 }
});

// Helper functions
function isStaticFile(url) {
 return STATIC_FILES.some(file => url.includes(file)) ||
  url.includes('.css') ||
  url.includes('.js') ||
  url.includes('.png') ||
  url.includes('.jpg') ||
  url.includes('.ico');
}

function isAPIRequest(url) {
 return url.includes('/api/') ||
  API_CACHE_PATTERNS.some(pattern => pattern.test(url));
}

function isVideoRequest(url) {
 return url.includes('.mp4') ||
  url.includes('.webm') ||
  url.includes('/video/') ||
  url.includes('/highlights/');
}

// Cache strategies
async function cacheFirst(request) {
 try {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
   return cachedResponse;
  }

  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
   const cache = await caches.open(STATIC_CACHE);
   cache.put(request, networkResponse.clone());
  }

  return networkResponse;
 } catch (error) {
  console.error('Cache first strategy failed:', error);
  return new Response('Offline - content not available', {
   status: 503,
   statusText: 'Service Unavailable'
  });
 }
}

async function networkFirst(request) {
 try {
  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
   const cache = await caches.open(DYNAMIC_CACHE);
   cache.put(request, networkResponse.clone());
  }

  return networkResponse;
 } catch (error) {
  console.log('Network first fallback to cache:', error);

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
   return cachedResponse;
  }

  return new Response('Offline - content not available', {
   status: 503,
   statusText: 'Service Unavailable'
  });
 }
}

async function networkFirstWithCache(request) {
 try {
  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
   const cache = await caches.open(DYNAMIC_CACHE);
   // Only cache successful API responses
   if (request.url.includes('/api/')) {
    cache.put(request, networkResponse.clone());
   }
  }

  return networkResponse;
 } catch (error) {
  console.log('API request failed, trying cache:', error);

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
   // Add offline indicator to cached API responses
   const response = cachedResponse.clone();
   if (request.url.includes('/api/')) {
    const data = await response.json();
    data._offline = true;
    return new Response(JSON.stringify(data), {
     headers: { 'Content-Type': 'application/json' }
    });
   }
   return cachedResponse;
  }

  // Return offline response for API requests
  if (request.url.includes('/api/')) {
   return new Response(JSON.stringify({
    error: 'Offline - please check your connection',
    _offline: true
   }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
   });
  }

  return new Response('Offline', { status: 503 });
 }
}

async function handleVideoRequest(request) {
 try {
  // Check if it's a range request
  const range = request.headers.get('Range');

  if (range) {
   // Handle range requests for video streaming
   return fetch(request);
  }

  // For non-range video requests, try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
   return cachedResponse;
  }

  // Fetch from network
  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
   // Cache video files in dynamic cache
   const cache = await caches.open(DYNAMIC_CACHE);
   cache.put(request, networkResponse.clone());
  }

  return networkResponse;
 } catch (error) {
  console.error('Video request failed:', error);

  // Try to serve from cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
   return cachedResponse;
  }

  return new Response('Video not available offline', {
   status: 503,
   statusText: 'Service Unavailable'
  });
 }
}

// Background sync functions
async function syncLikes() {
 try {
  // Get pending likes from IndexedDB
  const pendingLikes = await getPendingLikes();

  for (const like of pendingLikes) {
   try {
    await fetch(`/api/highlights/${like.highlightId}/like`, {
     method: 'POST',
     headers: {
      'Authorization': `Bearer ${like.token}`,
      'Content-Type': 'application/json'
     }
    });

    // Remove from pending likes
    await removePendingLike(like.id);
   } catch (error) {
    console.error('Failed to sync like:', error);
   }
  }
 } catch (error) {
  console.error('Sync likes failed:', error);
 }
}

async function syncUploads() {
 try {
  // Get pending uploads from IndexedDB
  const pendingUploads = await getPendingUploads();

  for (const upload of pendingUploads) {
   try {
    // Upload highlight
    const formData = new FormData();
    formData.append('video', upload.videoBlob);
    formData.append('title', upload.title);
    formData.append('description', upload.description);

    await fetch('/api/highlights/upload', {
     method: 'POST',
     headers: {
      'Authorization': `Bearer ${upload.token}`
     },
     body: formData
    });

    // Remove from pending uploads
    await removePendingUpload(upload.id);
   } catch (error) {
    console.error('Failed to sync upload:', error);
   }
  }
 } catch (error) {
  console.error('Sync uploads failed:', error);
 }
}

// IndexedDB helpers (simplified - would need full implementation)
async function getPendingLikes() {
 // Implementation would use IndexedDB to store offline actions
 return [];
}

async function removePendingLike(id) {
 // Remove like from IndexedDB
}

async function getPendingUploads() {
 // Get pending uploads from IndexedDB
 return [];
}

async function removePendingUpload(id) {
 // Remove upload from IndexedDB
}

// Message handling for communication with main app
self.addEventListener('message', (event) => {
 console.log('Service Worker: Message received', event.data);

 if (event.data.type === 'SKIP_WAITING') {
  self.skipWaiting();
 } else if (event.data.type === 'CACHE_HIGHLIGHT') {
  // Cache a specific highlight for offline viewing
  cacheHighlight(event.data.url);
 }
});

async function cacheHighlight(url) {
 try {
  const cache = await caches.open(DYNAMIC_CACHE);
  await cache.add(url);
  console.log('Highlight cached for offline viewing');
 } catch (error) {
  console.error('Failed to cache highlight:', error);
 }
}
