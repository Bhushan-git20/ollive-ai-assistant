import os
import uuid
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Internal modules
from memory.sqlite_memory import init_db, save_message, get_history, clear_history
from observability.logger import init_logs_db, log_request, get_stats
from guardrails.safety_filter import check_input, check_output
from tools.tool_router import route_tool

# ── Init DBs ──────────────────────────────────────────────────────────────────
init_db()
init_logs_db()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ollive AI Assistant",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Background and global theme */
    .stApp {
        background: #0f111a;
        color: #e2e8f0;
    }
    
    /* Hide Streamlit header and footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(20, 24, 36, 0.7) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem !important;
        color: #00f2fe !important;
    }
    
    /* Chat inputs */
    .stChatInputContainer {
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        background: rgba(20, 24, 36, 0.9) !important;
    }
    
    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Model headers in compare */
    h3 {
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(20, 24, 36, 0.7);
        border-radius: 8px;
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "qwen_loaded" not in st.session_state:
    st.session_state.qwen_loaded = False

SESSION_ID = st.session_state.session_id

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption(f"Session: `{SESSION_ID}`")

    model_choice = st.radio(
        "Model",
        options=["gemini-flash-lite-latest", "qwen2.5-0.5B"],
        index=0,
        help="Gemini = frontier model (Google AI). Qwen = open-source (local).",
    )

    st.divider()

    if st.button("🗑️ Clear chat history"):
        clear_history(SESSION_ID, model_choice)
        st.success("History cleared.")
        st.rerun()

    st.divider()
    st.subheader("📊 Observability")

    stats = get_stats()
    if stats:
        for row in stats:
            st.markdown(f"**{row['model']}**")
            cols = st.columns(2)
            cols[0].metric("Requests", row["requests"])
            cols[0].metric("Avg Latency", f"{row['avg_latency_ms']} ms")
            cols[1].metric("Prompt tokens", row["total_prompt_tokens"])
            cols[1].metric("Guardrail hits", row["guardrail_hits"])
    else:
        st.caption("No requests yet.")

    st.divider()
    st.markdown("**Tools available**")
    st.markdown("🔢 Calculator · 🕐 Datetime")
    st.markdown("**Guardrails** · **SQLite memory**")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🤖 Ollive AI Personal Assistant")
st.caption(
    f"Active model: **{model_choice}** · "
    "Compare OSS vs Frontier AI responses side-by-side."
)

tab_chat, tab_compare, tab_eval = st.tabs(["💬 Chat", "⚖️ Compare", "📋 Eval"])

# ─────────────────────────────────────────────────────────────────────────────
# CHAT TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    history = get_history(SESSION_ID, model_choice)

    # Render history
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me anything...")

    if user_input:
        # Guardrail check on input
        is_safe, reason = check_input(user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        if not is_safe:
            with st.chat_message("assistant"):
                st.error(f"🚫 {reason}")
            log_request(SESSION_ID, model_choice, len(user_input.split()), 0, 0.0, guardrail_triggered=True)
        else:
            save_message(SESSION_ID, model_choice, "user", user_input)

            # Tool routing
            tool_name, tool_result = route_tool(user_input)

            # Load model and generate
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    fresh_history = get_history(SESSION_ID, model_choice)
                    try:
                        if model_choice == "gemini-flash-lite-latest":
                            from models.gemini_model import generate
                        else:
                            if not st.session_state.qwen_loaded:
                                st.info("Loading Qwen model (first time only, ~30 seconds)...")
                            from models.qwen_model import generate

                        response, p_tok, c_tok, latency = generate(
                            user_input, fresh_history, tool_context=tool_result or ""
                        )
                        if model_choice != "gemini-flash-lite-latest":
                            st.session_state.qwen_loaded = True
                    except Exception as e:
                        response = f"⚠️ Model error: {e}"
                        p_tok, c_tok, latency = 0, 0, 0.0

                    # Output guardrail
                    out_safe, out_reason = check_output(response)
                    if not out_safe:
                        response = out_reason
                        log_request(SESSION_ID, model_choice, p_tok, c_tok, latency, guardrail_triggered=True, tool_used=tool_name)
                    else:
                        log_request(SESSION_ID, model_choice, p_tok, c_tok, latency, tool_used=tool_name)

                    if tool_result:
                        st.info(f"🔧 Tool used: `{tool_name}` → `{tool_result}`")

                    st.markdown(response)
                    st.caption(f"⏱ {latency:.0f} ms · ~{c_tok} tokens")

            save_message(SESSION_ID, model_choice, "assistant", response)

# ─────────────────────────────────────────────────────────────────────────────
# COMPARE TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("Side-by-side comparison")
    st.caption("Ask one question and see both models respond.")

    compare_input = st.text_input("Enter your question:", key="compare_input")
    run_compare = st.button("Run comparison", key="compare_btn")

    if run_compare and compare_input.strip():
        is_safe, reason = check_input(compare_input)
        if not is_safe:
            st.error(f"🚫 {reason}")
        else:
            tool_name, tool_result = route_tool(compare_input)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🔵 Gemini Flash Lite")
                with st.spinner("Gemini thinking..."):
                    try:
                        from models.gemini_model import generate as gemini_gen
                        g_resp, g_pt, g_ct, g_lat = gemini_gen(
                            compare_input, [], tool_context=tool_result or ""
                        )
                        out_safe, out_reason = check_output(g_resp)
                        g_resp = g_resp if out_safe else out_reason
                    except Exception as e:
                        g_resp, g_pt, g_ct, g_lat = f"Error: {e}", 0, 0, 0
                st.markdown(g_resp)
                st.caption(f"⏱ {g_lat:.0f} ms · ~{g_ct} tokens · Cost: ~$0.00 (free tier)")

            with col2:
                st.markdown("### 🟢 Qwen 2.5 0.5B")
                with st.spinner("Qwen thinking..."):
                    try:
                        from models.qwen_model import generate as qwen_gen
                        q_resp, q_pt, q_ct, q_lat = qwen_gen(
                            compare_input, [], tool_context=tool_result or ""
                        )
                        out_safe, out_reason = check_output(q_resp)
                        q_resp = q_resp if out_safe else out_reason
                    except Exception as e:
                        q_resp, q_pt, q_ct, q_lat = f"Error: {e}", 0, 0, 0
                st.markdown(q_resp)
                st.caption(f"⏱ {q_lat:.0f} ms · ~{q_ct} tokens · Cost: $0.00 (OSS)")

            if tool_result:
                st.info(f"🔧 Both used tool: `{tool_name}` → `{tool_result}`")

# ─────────────────────────────────────────────────────────────────────────────
# EVAL TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_eval:
    st.subheader("📋 Evaluation Suite")
    st.caption("Run structured eval on hallucination, bias, and safety. Export PDF report.")
    st.info("Run the eval from terminal: `python eval/eval_runner.py` → generates `eval_report.pdf`")

    stats = get_stats()
    if stats:
        st.subheader("Cost & Latency Summary")
        import pandas as pd
        df = pd.DataFrame(stats)
        df.columns = ["Model", "Requests", "Avg Latency (ms)", "Prompt Tokens", "Completion Tokens", "Guardrail Hits"]
        st.dataframe(df, use_container_width=True)
    else:
        st.caption("No data yet. Start chatting to populate metrics.")
