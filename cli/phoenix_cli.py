import grpc
import os
import sys

# Add the parent directory to the Python path to import generated gRPC files and common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import generated.main_ai_service_pb2_grpc as main_pb2_grpc
import generated.task_protocol_pb2 as task_pb2


def run_cli():
    print(
        "Phoenix CLI: Enter your code editing command (type 'exit' to quit):"
    )
    main_ai_channel = grpc.insecure_channel("localhost:50051")
    main_ai_stub = main_pb2_grpc.MainAIServiceStub(main_ai_channel)

    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "exit":
            break

        print(f"\nPhoenix CLI: Sending command to MainAI: '{user_input}'...")
        try:
            request = task_pb2.TaskRequest(
                file_target="main.py",
                proposed_change=user_input,
                explanation="User's natural language code editing command.",
            )
            response = main_ai_stub.HandleUserPrompt(request)

            if response.status == task_pb2.TaskResponse.DONE:
                print(
                    f"Phoenix CLI: Operation completed successfully: {response.message}"
                )
            else:
                print(f"Phoenix CLI: Operation failed: {response.message}")
        except grpc.RpcError as e:
            print(f"Phoenix CLI: Error communicating with MainAI: {e.details}")
        except Exception as e:
            print(f"Phoenix CLI: An unexpected error occurred: {e}")
        print("\n---")


if __name__ == "__main__":
    run_cli()
