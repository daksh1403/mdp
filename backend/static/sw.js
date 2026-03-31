// PaintBot Service Worker - Enables offline functionality and PWA features

const CACHE_NAME = 'paintbot-v1';
const ASSETS_TO_CACHE = [
  '/mobile.html',
  '/manifest.json'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip ESP32 and video stream requests (real-time data)
  const url = new URL(event.request.url);
  if (url.pathname.includes('/stream') || 
      url.pathname.includes('/video') ||
      url.pathname.includes('/capture') ||
      url.pathname.includes('/spray') ||
      url.pathname.includes('/ping')) {
    return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone and cache successful responses
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(event.request);
      })
  );
});

// Handle background sync for spray commands
self.addEventListener('sync', (event) => {
  if (event.tag === 'spray-sync') {
    event.waitUntil(
      // Retry failed spray commands
      self.registration.showNotification('PaintBot', {
        body: 'Spray command synced',
        icon: '/manifest.json#icons[0].src'
      })
    );
  }
});

// Handle push notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'PaintBot';
  const options = {
    body: data.body || 'Spray sequence complete!',
    icon: data.icon || '/manifest.json#icons[0].src',
    badge: '/manifest.json#icons[1].src',
    vibrate: [200, 100, 200],
    tag: 'paintbot-notification',
    renotify: true
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/mobile.html')
  );
});
