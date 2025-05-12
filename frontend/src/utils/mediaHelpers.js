/**
 * Utility functions for handling media URLs
 */

/**
 * Converts a relative media URL to an absolute URL pointing to the backend server
 * @param {string} url - The relative URL from the backend
 * @returns {string} - The absolute URL
 */
export const getMediaUrl = (url) => {
  if (!url) return '/default-property.jpg';
  
  // If URL is already absolute (starts with http:// or https://), return as is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  
  // For Django media URLs that start with /media/
  if (url.startsWith('/media/')) {
    return `http://127.0.0.1:8000${url}`;
  }
  
  // If it's already a media path but without the leading slash
  if (url.startsWith('media/')) {
    return `http://127.0.0.1:8000/${url}`;
  }
  
  // For direct paths to the file (property_images/*)
  if (url.includes('property_images/')) {
    return `http://127.0.0.1:8000/media/${url}`;
  }
  
  // Remove leading slash if present for any other case
  const cleanUrl = url.startsWith('/') ? url.substring(1) : url;
  
  // Default case: use the proxy configured in package.json
  return `http://127.0.0.1:8000/media/${cleanUrl}`;
};

/**
 * Handles image loading errors by replacing with default image
 * @param {Event} event - The error event
 */
export const handleImageError = (event) => {
  console.log('Image failed to load, using default', event.target.src);
  event.target.src = '/default-property.jpg';
}; 