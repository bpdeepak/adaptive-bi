// Development utility to set a valid token for testing
// Run this in the browser console after navigating to the frontend

console.log('Setting up test authentication...');

// Create a mock token that the frontend will recognize
const mockToken = 'mock-jwt-token-' + Date.now();
localStorage.setItem('token', mockToken);

console.log('Mock token set:', mockToken);
console.log('Reloading page to trigger authentication...');

window.location.reload();
