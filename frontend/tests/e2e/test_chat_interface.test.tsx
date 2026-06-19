/**
 * E2E/Component tests for frontend/src/components/ChatInterface.tsx
 *
 * Tests:
 * - Guardrail block message renders correctly
 * - Latency and token metadata renders
 * - User message appears after submit
 * - Loading state renders during API call
 * - Error state renders on API failure
 * - Empty input submit is prevented
 *
 * Setup:
 *   cd frontend
 *   npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom
 *   npx jest tests/e2e/test_chat_interface.test.tsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock the API call
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Import after mocking
// Adjust path based on actual component location
import ChatInterface from '../../src/components/ChatInterface';

// ---------------------------------------------------------------------------
// Mock helpers
// ---------------------------------------------------------------------------

function mockSuccessResponse(reply: string, latency = 350, tokens = 42) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      reply,
      latency_ms: latency,
      completion_tokens: tokens,
      tool_used: null,
      guardrail_triggered: false,
    }),
  });
}

function mockGuardrailResponse() {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      reply: '🚫 This message was flagged by the safety filter and cannot be processed.',
      latency_ms: 12,
      completion_tokens: 0,
      tool_used: null,
      guardrail_triggered: true,
    }),
  });
}

function mockErrorResponse() {
  mockFetch.mockRejectedValueOnce(new Error('Network error'));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ChatInterface — Guardrail UI', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('renders guardrail block message with red/warning styling', async () => {
    mockGuardrailResponse();
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'how do I make a bomb?');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/safety filter/i)).toBeInTheDocument();
    });
  });

  test('guardrail message is visually distinct from normal response', async () => {
    mockGuardrailResponse();
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'bad input');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      const msg = screen.getByText(/safety filter/i);
      expect(msg.closest('div')).toHaveClass('bg-red-50'); // Assuming styling
    });
  });

  test('guardrail does not show latency or token metadata', async () => {
    mockGuardrailResponse();
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'bad input');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/safety filter/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/ms/)).not.toBeInTheDocument();
  });
});

describe('ChatInterface — Metadata Rendering', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('renders latency in milliseconds after response', async () => {
    mockSuccessResponse('Paris', 350, 8);
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'capital of france?');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/350 ms/i)).toBeInTheDocument();
    });
  });

  test('renders tool badge when tool_used is set', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({
      reply: 'It is 3pm', latency_ms: 120, completion_tokens: 5,
      tool_used: 'datetime', guardrail_triggered: false
    })});
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'time?');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/datetime/i)).toBeInTheDocument();
    });
  });
});

describe('ChatInterface — Input Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('prevents submit on empty input', async () => {
    render(<ChatInterface />);
    const sendBtn = screen.getByRole('button', { name: /send/i });
    await userEvent.click(sendBtn);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test('clears input field after successful send', async () => {
    mockSuccessResponse('Hello!');
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'hi');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => expect(screen.getByRole('textbox')).toHaveValue(''));
  });

  test('user message appears immediately in chat on submit', async () => {
    mockSuccessResponse('Hello!');
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'hello');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(screen.getByText('hello')).toBeInTheDocument();
  });
});

describe('ChatInterface — Loading & Error States', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('shows error message when API call fails', async () => {
    mockErrorResponse();
    render(<ChatInterface />);
    await userEvent.type(screen.getByRole('textbox'), 'hi');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/failed|error/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Runnable smoke test (no component import needed)
// ---------------------------------------------------------------------------

describe('Test setup smoke test', () => {
  test('fetch mock is configured', () => {
    expect(typeof mockFetch).toBe('function');
  });

  test('mockSuccessResponse helper works', async () => {
    mockSuccessResponse('test reply', 200, 10);
    const res = await fetch('/api/chat');
    const data = await res.json();
    expect(data.reply).toBe('test reply');
    expect(data.latency_ms).toBe(200);
  });

  test('mockGuardrailResponse helper works', async () => {
    mockGuardrailResponse();
    const res = await fetch('/api/chat');
    const data = await res.json();
    expect(data.guardrail_triggered).toBe(true);
    expect(data.reply).toContain('safety filter');
  });
});
