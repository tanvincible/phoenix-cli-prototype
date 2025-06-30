import grpc
import time
import os
from concurrent import futures
from common.gemini_wrapper import GeminiClient

# Import generated gRPC files
import generated.main_ai_service_pb2 as main_pb2
import generated.main_ai_service_pb2_grpc as main_pb2_grpc
import generated.dep_ai_service_pb2_grpc as dep_pb2_grpc
import generated.task_protocol_pb2 as task_pb2

class MainAIService(main_pb2_grpc.MainAIServiceServicer):
    def __init__(self, gemini_client: GeminiClient, files_dir: str):
        self.gemini_client = gemini_client
        self.files_dir = files_dir
        self.main_py_path = os.path.join(files_dir, "main.py")
        self.dep_ai_stub = None # Will be set up later

    def _get_dep_ai_stub(self):
        if self.dep_ai_stub is None:
            # Assume DepAI is running on localhost:50052
            channel = grpc.insecure_channel('localhost:50052')
            self.dep_ai_stub = dep_pb2_grpc.DepAIServiceStub(channel)
        return self.dep_ai_stub

    def _read_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, 'r') as f:
            return f.read()

    def _write_file(self, file_path: str, content: str):
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"MainAI: Updated {os.path.basename(file_path)}")

    def HandleUserPrompt(self, request: task_pb2.TaskRequest, context) -> task_pb2.TaskResponse:
        user_prompt = request.proposed_change
        print(f"MainAI: Received user prompt: '{user_prompt}'")

        # 1. Ask Gemini to generate code for main.py
        current_main_py_content = self._read_file(self.main_py_path)
        gemini_prompt_code = (
            f"The user wants to '{user_prompt}'. "
            f"Current content of main.py:\n```python\n{current_main_py_content}\n```\n"
            "Please provide the *full* updated content of main.py, including the new function. "
            "If a new dependency is likely needed (e.g., 'requests' for API calls), "
            "just generate the code for main.py, I will infer dependencies separately. "
            "Output only the Python code, nothing else."
        )
        new_main_py_content = self.gemini_client.generate_content(gemini_prompt_code)
        if new_main_py_content.startswith("Error:"):
            return task_pb2.TaskResponse(status=task_pb2.TaskResponse.ERROR, message=new_main_py_content)

        # Basic parsing for code block if Gemini adds markdown
        if "```python" in new_main_py_content:
            new_main_py_content = new_main_py_content.split("```python")[1].split("```")[0].strip()

        self._write_file(self.main_py_path, new_main_py_content)

        # 2. Ask Gemini to infer dependencies
        gemini_prompt_deps = (
            f"I have updated main.py with the following content:\n```python\n{new_main_py_content}\n```\n"
            "Based on this code, identify any new Python package dependencies that would typically be required "
            "and should be added to `requirements.txt`. "
            "List them as comma-separated values (e.g., 'requests, numpy, pandas'). "
            "If no new dependencies are needed, simply output 'none'."
        )
        dependencies_str = self.gemini_client.generate_content(gemini_prompt_deps)
        if dependencies_str.startswith("Error:"):
            return task_pb2.TaskResponse(status=task_pb2.TaskResponse.ERROR, message=dependencies_str)

        dependencies = [d.strip() for d in dependencies_str.split(',') if d.strip() and d.strip().lower() != 'none']

        if dependencies:
            print(f"MainAI: Inferred dependencies: {dependencies}. Notifying DepAI...")
            # 3. Notify DepAI
            dep_ai_stub = self._get_dep_ai_stub()
            dep_request = task_pb2.TaskRequest(
                file_target="requirements.txt",
                proposed_change=",".join(dependencies), # Send as comma-separated for DepAI to parse
                explanation=f"New dependencies required for main.py changes due to '{user_prompt}'."
            )
            try:
                dep_response = dep_ai_stub.HandleDependencyRequest(dep_request)
                if dep_response.status == task_pb2.TaskResponse.DONE:
                    print("MainAI: DepAI confirmed dependency update.")
                    return task_pb2.TaskResponse(status=task_pb2.TaskResponse.DONE, message="Code and dependencies updated.")
                else:
                    return task_pb2.TaskResponse(status=task_pb2.TaskResponse.ERROR, message=f"DepAI error: {dep_response.message}")
            except grpc.RpcError as e:
                return task_pb2.TaskResponse(status=task_pb2.TaskResponse.ERROR, message=f"gRPC error communicating with DepAI: {e}")
        else:
            print("MainAI: No new dependencies inferred.")
            return task_pb2.TaskResponse(status=task_pb2.TaskResponse.DONE, message="Code updated; no new dependencies.")

    def HandleDependencyNotification(self, request: task_pb2.TaskResponse, context) -> task_pb2.TaskResponse:
        # This method is primarily for DepAI to acknowledge it's done.
        # For this prototype, MainAI doesn't need to do much here, it already gets response from DepAI's HandleDependencyRequest.
        # This could be used for more complex workflows where DepAI initiates a confirmation.
        print(f"MainAI: Received confirmation from DepAI: {request.message}")
        return task_pb2.TaskResponse(status=task_pb2.TaskResponse.DONE, message="Acknowledgement received by MainAI.")


def serve_main_ai(gemini_client: GeminiClient, files_dir: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    main_pb2_grpc.add_MainAIServiceServicer_to_server(MainAIService(gemini_client, files_dir), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("MainAI Server started on port 50051.")
    try:
        while True:
            time.sleep(86400) # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)
        print("MainAI Server stopped.")

if __name__ == '__main__':
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        exit(1)

    files_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'files'))
    os.makedirs(files_directory, exist_ok=True) # Ensure files directory exists

    gemini_client_instance = GeminiClient(GEMINI_API_KEY)
    serve_main_ai(gemini_client_instance, files_directory)