## Milestone v1.0 Requirements

### Bug Fixes
- [ ] **BUG-01**: Fix Qwen model duplicate user message loop (`qwen_model.py`)
- [ ] **BUG-02**: Cache Gemini client to prevent recreation every call (`gemini_model.py`)
- [ ] **BUG-03**: Delete `temp_test.py` with hardcoded Windows path
- [ ] **BUG-04**: Fix false positive triggers in `tool_router.py` (datetime/calculator)
- [ ] **BUG-05**: Update `safety_filter.py` pattern to catch "how do I"
- [ ] **BUG-06**: Fix `node.n` deprecation warning in `calculator.py`
- [ ] **BUG-07**: Update model string name in `gemini_model.py` to verified version
- [ ] **BUG-08**: Remove old `qwen_loaded` flag logic if irrelevant in new stack

### Core UX Upgrades (High Value)
- [ ] **UX-01**: Implement Streaming responses for both Gemini and Qwen
- [ ] **UX-02**: Build in-app Eval Runner tab with inline execution
- [ ] **UX-03**: Add DuckDuckGo Web Search as Tool #3
- [ ] **UX-04**: Add Response Rating (👍 👎) stored in SQLite

### Polish Upgrades (Medium Value)
- [ ] **POL-01**: Add Prompt Templates dropdown for starter prompts
- [ ] **POL-02**: Replace text observability stats with Recharts visualizations
- [ ] **POL-03**: Add Copy response button to assistant messages
- [ ] **POL-04**: Build System prompt editor in the sidebar

## Future Requirements
None

## Out of Scope
None

## Traceability
*(To be populated by Roadmap)*
