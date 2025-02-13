import gradio as gr
import autogen
from autogen import AssistantAgent, UserProxyAgent
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

# Windows configuration
OUTPUT_DIR = Path(r"L:\Projects\LazyCodder\output")
SCRIPTS_DIR = OUTPUT_DIR / "generated_scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# AutoGen configuration
config_list = [
    {
        "model": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.3,
    "timeout": 120
}

# Enhanced Assistant Agent
assistant = AssistantAgent(
    name="code_assistant",
    llm_config=llm_config,
    system_message="""Return ONLY raw Python code with:
- Python 3.12 syntax with type hints
- Error handling (try/except)
- # REQUIREMENTS: packages comment
- Load data from internet (no local files)
- Use requests/pandas for data fetching
- pathlib.WindowsPath for output paths
- Windows compatibility
- Generate synthetic data if external source fails
- NO MARKDOWN/EXPLANATIONS"""
)

# Execution Proxy with enhanced capabilities
user_proxy = UserProxyAgent(
    name="execution_agent",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=3,
    code_execution_config={
        "work_dir": str(SCRIPTS_DIR),
        "use_docker": False,
    }
)


def process_task(task: str) -> Tuple[str, Optional[str], Optional[list]]:
    """Process user tasks with Windows-specific handling"""
    try:
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=f"{task}\nOutput directory: {OUTPUT_DIR}",
            clear_history=True
        )

        # Extract generated code
        code = next(
            m["content"] for m in reversed(chat_result.chat_history)
            if m["role"] == "assistant"
        )

        # Windows path normalization
        code = code.replace('/', '\\').replace('posix', 'nt')

        # Install requirements
        requirements = []
        for match in re.finditer(r'# REQUIREMENTS: (.*)', code):
            requirements.extend([pkg.strip() for pkg in match.group(1).split(',')])

        if requirements:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + requirements,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )

        # Save script
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_path = SCRIPTS_DIR / f"script_{timestamp}.py"
        script_path.write_text(code, encoding="utf-8")

        # Execute in Windows environment
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(OUTPUT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Collect outputs
        output_files = [str(f) for f in OUTPUT_DIR.glob("*.*") if f.is_file()]

        log_output = f"""✅ Task Completed
        Exit Code: {result.returncode}
        Output: {result.stdout or 'No output'}
        Errors: {result.stderr or 'No errors'}"""

        return log_output, str(script_path), output_files

    except Exception as e:
        error_log = f"""❌ Task Failed
        Error: {str(e)}"""
        return error_log, None, None
# Gradio Interface with Custom Styling
with gr.Blocks(
        theme=gr.themes.Soft(),
        title="Lazy Codder",
        css="""
    .gradio-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .dark .gradio-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }
    .main-panel {
        border-radius: 12px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .dark .main-panel {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .output-code {
        border-radius: 8px;
        padding: 16px;
        background: rgba(248, 250, 252, 0.9);
        border: 1px solid rgba(226, 232, 240, 0.2);
    }
    .dark .output-code {
        background: rgba(17, 24, 39, 0.9);
        border: 1px solid rgba(55, 65, 81, 0.2);
    }
    .task-input textarea {
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #E2E8F0;
        background: rgba(255, 255, 255, 0.9);
        transition: all 0.3s ease;
    }
    .dark .task-input textarea {
        border-color: #374151;
        background: rgba(17, 24, 39, 0.9);
    }
    .task-input textarea:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    .custom-button {
        transition: all 0.3s ease;
        border-radius: 8px;
        background: rgba(79, 70, 229, 0.9);
    }
    .custom-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
    }
    .tips-section {
        background: rgba(248, 250, 252, 0.9);
        border-radius: 8px;
        padding: 16px;
        margin-top: 16px;
        border: 1px solid rgba(226, 232, 240, 0.2);
        backdrop-filter: blur(10px);
    }
    .dark .tips-section {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(55, 65, 81, 0.2);
    }
    .examples-section {
        margin-top: 16px;
        padding: 16px;
        background: rgba(248, 250, 252, 0.9);
        border-radius: 8px;
        border: 1px solid rgba(226, 232, 240, 0.2);
        backdrop-filter: blur(10px);
    }
    .dark .examples-section {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(55, 65, 81, 0.2);
    }
    .tabs {
        border-radius: 8px;
        overflow: hidden;
    }
    .tab-selected {
        background: rgba(79, 70, 229, 0.1);
        border-bottom: 2px solid #4F46E5;
    }
    """
) as ui:
    with gr.Row(equal_height=True):
        # Input Column
        with gr.Column(scale=4, elem_classes="main-panel"):
            gr.Markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 2.5em; color: #4F46E5;">🦥 Lazy Codder</h1>
                <p style="color: #6B7280; font-size: 1.1em;">Your AI Coding Assistant</p>
            </div>
            """)

            task_input = gr.Textbox(
                label="Describe Your Task",
                placeholder="Example: 'Create a data visualization for COVID-19 trends'",
                lines=4,
                max_lines=6,
                elem_classes="task-input"
            )

            with gr.Row(equal_height=True):
                submit_btn = gr.Button(
                    "✨ Generate Code",
                    variant="primary",
                    elem_classes="custom-button",
                    min_width=140
                )
                clear_btn = gr.Button(
                    "🔄 Reset",
                    variant="secondary",
                    elem_classes="custom-button",
                    min_width=140
                )

            with gr.Column(elem_classes="tips-section"):
                gr.Markdown("### 💡 Quick Tips")
                gr.Markdown("""
                • Specify input/output formats clearly
                • Include desired visualization types
                • Mention any specific libraries needed
                """)

        # Output Column
        with gr.Column(scale=6, elem_classes="main-panel"):
            with gr.Tabs(selected=0):
                with gr.TabItem("📋 Execution Log"):
                    log_output = gr.Code(
                        label="Process Output",
                        language="shell",
                        interactive=False,
                        lines=16,
                        elem_classes="output-code"
                    )

                with gr.TabItem("📂 Generated Files"):
                    with gr.Row():
                        script_output = gr.File(
                            label="Generated Script",
                            file_count="single",
                            height=350,
                            interactive=False
                        )
                        file_output = gr.File(
                            label="Output Files",
                            file_count="multiple",
                            height=350,
                            interactive=False
                        )

    # Enhanced Examples Section
    with gr.Column(elem_classes="examples-section"):
        gr.Examples(
            examples=[
                ["Generate a CSV with 100 random temperature readings"],
                ["Create a matplotlib plot of sine and cosine waves"],
                ["Batch convert PNG images to JPG format"]
            ],
            inputs=task_input,
            label="🎯 Example Tasks",
            examples_per_page=3
        )

    # Event handlers
    submit_btn.click(
        fn=process_task,
        inputs=task_input,
        outputs=[log_output, script_output, file_output]
    )

    clear_btn.click(
        fn=lambda: [None, None, None],
        outputs=[task_input, log_output, script_output, file_output]
    )

if __name__ == "__main__":
    ui.launch()
