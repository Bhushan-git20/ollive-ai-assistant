## Proposed Roadmap

**4 phases** | **16 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Bug Fixes | Fix all critical and medium bugs in models and tools | BUG-01 to BUG-08 | 3 |
| 2 | Streaming & Search | Implement real-time streaming and DuckDuckGo search | UX-01, UX-03 | 2 |
| 3 | Eval Runner & Ratings | Build the in-app Eval Runner and SQLite Rating system | UX-02, UX-04 | 3 |
| 4 | UI Polish | Add Prompt Templates, Recharts, Copy, and Prompt Editor | POL-01 to POL-04 | 4 |

### Phase Details

**Phase 1: Bug Fixes**
Goal: Fix all critical and medium bugs in models and tools
Requirements: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, BUG-06, BUG-07, BUG-08
Success criteria:
1. Qwen model no longer duplicates user messages.
2. Gemini client is cached and model name is accurate.
3. Tool router false positives are eliminated.

**Phase 2: Streaming & Search**
Goal: Implement real-time streaming and DuckDuckGo search
Requirements: UX-01, UX-03
Success criteria:
1. Messages from Gemini and Qwen stream in chunks in the UI.
2. DuckDuckGo tool successfully searches the web and returns results to the assistant.

**Phase 3: Eval Runner & Ratings**
Goal: Build the in-app Eval Runner and SQLite Rating system
Requirements: UX-02, UX-04
Success criteria:
1. "Run Eval" button on Eval tab triggers python script and shows live progress/results.
2. Users can click 👍/👎 on messages, which updates the memory SQLite DB.

**Phase 4: UI Polish**
Goal: Add Prompt Templates, Recharts, Copy, and Prompt Editor
Requirements: POL-01, POL-02, POL-03, POL-04
Success criteria:
1. Clicking a starter prompt populates the chat input.
2. Observability dashboard shows charts instead of plain text metrics.
3. Users can one-click copy any assistant response.
4. System prompt can be customized from the sidebar.
