import '@testing-library/jest-dom';

// Mock scrollIntoView
Object.defineProperty(HTMLDivElement.prototype, 'scrollIntoView', {
  writable: true,
  value: jest.fn(),
});
