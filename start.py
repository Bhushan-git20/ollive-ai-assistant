import subprocess
import os
import sys
import platform

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("Starting FastAPI Backend...")
    # Start backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "server:app", "--reload"]
    backend_process = subprocess.Popen(backend_cmd, cwd=root_dir)

    print("Starting Next.js Frontend...")
    # Start frontend
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    frontend_process = subprocess.Popen(frontend_cmd, cwd=frontend_dir)

    try:
        print("\n🚀 Ollive AI Assistant is running! Press Ctrl+C to stop.\n")
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
