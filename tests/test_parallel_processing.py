import asyncio
import threading
import time
from dataclasses import dataclass

from main import process_chat


@dataclass
class FakeMessage:
    content: str


class FakeGraph:
    def __init__(self):
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()
        self.states = []

    def invoke(self, state):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.states.append(state)

        time.sleep(0.05)

        with self.lock:
            self.active -= 1

        return {
            "send_answer_to": state["client_name"],
            "client_name": state["client_name"],
            "main_node_output": f"answer for {state['client_name']}",
        }


def test_process_chat_uses_independent_state():
    async def run_test():
        fake_graph = FakeGraph()
        result = await process_chat(
            "client_a",
            [FakeMessage(content="old"), FakeMessage(content="new")],
            agent_graph=fake_graph,
        )

        assert result["error"] is None
        assert result["chat_name"] == "client_a"
        assert fake_graph.states[0]["client_name"] == "client_a"
        assert fake_graph.states[0]["chat_history"][0].content == "old"
        assert fake_graph.states[0]["user_input"].content == "new"

    asyncio.run(run_test())


def test_process_chat_can_run_with_parallel_agent_limit():
    async def run_test():
        fake_graph = FakeGraph()
        semaphore = asyncio.Semaphore(2)
        tasks = [
            process_chat(
                f"client_{index}",
                [FakeMessage(content=f"message {index}")],
                agent_graph=fake_graph,
                semaphore=semaphore,
            )
            for index in range(4)
        ]

        results = await asyncio.gather(*tasks)

        assert all(result["error"] is None for result in results)
        assert fake_graph.max_active == 2
        assert sorted(result["chat_name"] for result in results) == [
            "client_0",
            "client_1",
            "client_2",
            "client_3",
        ]

    asyncio.run(run_test())


def test_process_chat_returns_error_for_empty_messages():
    async def run_test():
        result = await process_chat("client_a", [], agent_graph=FakeGraph())

        assert result["response"] is None
        assert result["error"] == "No messages found for chat"

    asyncio.run(run_test())
