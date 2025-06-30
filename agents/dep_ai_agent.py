import grpc
import time
import os
from concurrent import futures
from common.gemini_wrapper import GeminiClient

# Import generated gRPC files
import generated.dep_ai_service_pb2_grpc as dep_pb2_grpc
import generated.main_ai_service_pb2_grpc as main_pb2_grpc
import generated.task_protocol_pb2 as task_pb2

class DepAIService(dep_pb2_grpc.DepAIServiceServicer):
    def __init__(self, gemini_client: GeminiClient, files_dir: str):
        self.gemini_client = gemini_client
        self.files_dir = files_dir
        self.requirements_txt_path = os.path.join(files_dir, "requirements.txt")
        self.main_ai_stub = None # Will be set up later

    def _get_main_ai_stub(self):
        if self.main_ai_stub is None:
            # Assume MainAI is running on localhost:50051
            channel = grpc.insecure_channel('localhost:50051')
            self.main_ai_stub = main_pb2_grpc.MainAIServiceStub(channel)
        return self.main_ai_stub

    def _read_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, 'r') as f:
            return f.read()

    def _write_file(self, file_path: str, content: str):
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"DepAI: Updated {os.path.basename(file_path)}")

    def HandleDependencyRequest(self, request: task_pb2.TaskRequest, context) -> task_pb2.TaskResponse:
        dependencies_to_add_str = request.proposed_change
        explanation = request.explanation
        print(f"DepAI: Received dependency request for '{dependencies_to_add_str}' due to: {explanation}")

        new_dependencies = [d.strip() for d in dependencies_to_add_str.split(',') if d.strip()]

        current_requirements = self._read_file(self.requirements_txt_path).splitlines()
        updated_requirements = list(current_requirements) # Make a copy

        added_any = False
        for dep in new_dependencies:
            if dep not in updated_requirements:
                updated_requirements.append(dep)
                added_any = True
                print(f"DepAI: Added '{dep}' to requirements.txt")

        if added_any:
            self._write_file(self.requirements_txt_path, "\n".join(updated_requirements) + "\n")
            # Optionally, ask Gemini to confirm the update or reformat
            gemini_prompt_confirm = (
                f"I've added the following dependencies to requirements.txt: {', '.join(new_dependencies)}. "
                "Confirm this action and provide a brief confirmation message (e.g., 'Requirements updated.')."
            )
            gemini_response = self.gemini_client.generate_content(gemini_prompt_confirm)
            if gemini_response.startswith("Error:"):
                return task_pb2.TaskResponse(status=task_pb2.TaskResponse.ERROR, message=gemini_response)
            else:
                return task_pb2.TaskResponse(status=task_pb2.TaskResponse.DONE, message=gemini_response)
        else:
            print("DepAI: No new dependencies to add or all were already present.")
            return task_pb2.TaskResponse(status=task_pb2.TaskResponse.DONE, message="No new dependencies added or already present.")


def serve_dep_ai(gemini_client: GeminiClient, files_dir: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dep_pb2_grpc.add_DepAIServiceServicer_to_server(DepAIService(gemini_client, files_dir), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("DepAI Server started on port 50052.")
    try:
        while True:
            time.sleep(86400) # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)
        print("DepAI Server stopped.")

if __name__ == '__main__':
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        exit(1)

    files_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'files'))
    os.makedirs(files_directory, exist_ok=True) # Ensure files directory exists

    gemini_client_instance = GeminiClient(GEMINI_API_KEY)
    serve_dep_ai(gemini_client_instance, files_directory)