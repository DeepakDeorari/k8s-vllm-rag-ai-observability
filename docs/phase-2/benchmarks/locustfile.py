from locust import HttpUser, task

class VLLMUser(HttpUser):
    wait_time = lambda self: 0

    @task
    def chat_completion(self):
        with self.client.post(
            "/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-1.5B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain Kubernetes in five concise bullet points."
                    }
                ],
                "max_tokens": 128
            },
            catch_response=True
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"Status code: {response.status_code}"
                )
