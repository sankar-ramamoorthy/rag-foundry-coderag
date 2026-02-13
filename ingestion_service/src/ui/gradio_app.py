# src/ingestion_service/ui/gradio_app.py
import os
import json
import requests
import gradio as gr  # type: ignore

# Base URLs for services (Docker-friendly)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
RAG_API_BASE_URL = os.getenv("RAG_API_BASE_URL", "http://localhost:8004")


# ----------------------------
# Ingestion functions
# ----------------------------
def submit_ingest(source_type: str, file_obj):
    """Submit an ingestion request to the API."""
    try:
        if source_type == "file":
            if file_obj is None:
                return "No file selected."
            metadata = json.dumps({"filename": os.path.basename(file_obj.name)})
            with open(file_obj.name, "rb") as f:
                response = requests.post(
                    f"{API_BASE_URL}/v1/ingest/file",
                    files={"file": f},
                    data={"metadata": metadata},
                    timeout=500,
                )
        else:
            response = requests.post(
                f"{API_BASE_URL}/v1/ingest",
                json={"source_type": source_type, "metadata": {}},
                timeout=120,
            )

        if response.status_code != 202:
            return f"Error submitting ingestion: {response.text}"

        data = response.json()
        return f"Ingestion accepted.\nID: {data['ingestion_id']}\nStatus: {data.get('status', '-')}"
    except Exception as exc:
        return f"Error submitting ingestion: {exc}"


def check_status(ingestion_id: str):
    """Check the status of an ingestion request."""
    try:
        if not ingestion_id:
            return "Please enter an ingestion ID."

        response = requests.get(
            f"{API_BASE_URL}/v1/ingest/{ingestion_id}",
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "-")
            return f"Status: {status}"

        # Any non-200 → show error cleanly
        try:
            error = response.json()
            message = error.get("message", "Unknown error")
        except Exception:
            message = response.text

        return f"Error checking status: {message}"

    except Exception as exc:
        return f"Error checking status: {exc}"


# ----------------------------
# RAG query function
# ----------------------------
def submit_rag_query(query: str, top_k: int, provider: str | None, model: str | None):
    """Submit a RAG query to the orchestrator."""
    try:
        if not query.strip():
            return "Please enter a query."

        payload = {
            "query": query,
            "top_k": top_k,
        }

        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        response = requests.post(
            f"{RAG_API_BASE_URL}/v1/rag",
            json=payload,
             timeout=300,
        )
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        formatted_sources = "\n".join(f"- {s}" for s in sources)

        return f"Answer:\n{answer}\n\nSources:\n{formatted_sources if formatted_sources else '-'}"

    except Exception as exc:
        return f"Error querying RAG: {exc}"


# ----------------------------
# Build Gradio UI
# ----------------------------
def build_ui():
    """Build the Gradio UI with ingestion + RAG query."""
    with gr.Blocks(title="Agentic RAG") as demo:  # type: ignore
        gr.Markdown("# Agentic RAG Ingestion UI")  # type: ignore

        # ----------------------------
        # Ingestion section
        # ----------------------------
        with gr.Row():  # type: ignore
            source_type = gr.Dropdown(  # type: ignore
                choices=["file", "bytes", "uri"],
                value="file",
                label="Source Type",
            )
            file_input = gr.File(label="Upload File")  # type: ignore
            submit_btn = gr.Button("Submit Ingestion")  # type: ignore

        submission_output = gr.Textbox(label="Submission Result")  # type: ignore

        submit_btn.click(
            fn=submit_ingest,
            inputs=[source_type, file_input],
            outputs=submission_output,
        )

        gr.Markdown("## Check Status")  # type: ignore
        ingestion_id_input = gr.Textbox(label="Ingestion ID")  # type: ignore
        status_btn = gr.Button("Check Status")  # type: ignore
        status_output = gr.Textbox(label="Status")  # type: ignore

        status_btn.click(
            fn=check_status,
            inputs=ingestion_id_input,
            outputs=status_output,
        )

        # ----------------------------
        # RAG query section
        # ----------------------------
        gr.Markdown("## Ask the RAG")  # type: ignore
        rag_query = gr.Textbox(  # type: ignore
            label="Question",
            placeholder="Ask a question about your ingested data...",
            lines=3,
        )

        with gr.Row():  # type: ignore
            top_k = gr.Number(  # type: ignore
                label="Top K",
                value=5,
                precision=0,
            )
            provider = gr.Textbox(  # type: ignore
                label="LLM Provider (optional)",
                placeholder="ollama | openai | lmstudio",
            )
            model = gr.Textbox(  # type: ignore
                label="Model (optional)",
                placeholder="e.g. Qwen3:1.7b",
            )

        rag_btn = gr.Button("Ask")  # type: ignore
        rag_output = gr.Textbox(  # type: ignore
            label="RAG Response",
            lines=12,
        )

        rag_btn.click(
            fn=submit_rag_query,
            inputs=[rag_query, top_k, provider, model],
            outputs=rag_output,
        )

    return demo


# ----------------------------
# Launch the app
# ----------------------------
if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_port=7860, server_name="0.0.0.0")
