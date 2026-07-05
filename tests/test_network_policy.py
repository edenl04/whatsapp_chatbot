from dataclasses import dataclass

from graph.network_policy import (
    AgentRuntimeContext,
    filter_network_tools,
    filter_tools_for_army_preserved,
    is_army_preserved_confirmed,
    is_network_diagnostic_request,
)
from graph.tools.tools import all_tools, base_tools, network_diagnostic_tools


@dataclass
class FakeMessage:
    content: str


@dataclass
class FakeTool:
    name: str


@dataclass
class FakeRuntime:
    context: AgentRuntimeContext


class FakeRequest:
    def __init__(self, tools, context):
        self.tools = tools
        self.runtime = FakeRuntime(context)

    def override(self, tools):
        return FakeRequest(tools, self.runtime.context)


def test_army_preserved_confirmed_from_translated_input():
    state = {"translated_input": "check ping on army.preserved for host1"}

    assert is_army_preserved_confirmed(state) is True


def test_army_preserved_confirmed_from_chat_history():
    state = {
        "translated_input": "ping host1",
        "chat_history": [FakeMessage(content="the network is army.preserved")],
    }

    assert is_army_preserved_confirmed(state) is True


def test_army_preserved_not_confirmed_for_other_networks():
    assert is_army_preserved_confirmed({"translated_input": "ping host on army.civil"}) is False
    assert is_army_preserved_confirmed({"translated_input": "ping host on army.S_idf"}) is False
    assert is_army_preserved_confirmed({"translated_input": "ping host on army.TS_idf"}) is False
    assert is_army_preserved_confirmed({"translated_input": "ping host"}) is False


def test_diagnostic_request_detection():
    assert is_network_diagnostic_request({"translated_input": "ping 10.0.0.1"}) is True
    assert is_network_diagnostic_request({"translated_input": "create zoom tomorrow"}) is False


def test_filter_tools_hides_network_tools_without_army_preserved():
    tools = [FakeTool("zoom_meeting_creator"), FakeTool("ping_host"), FakeTool("show_device_command")]

    filtered = filter_tools_for_army_preserved(tools, army_preserved_confirmed=False)

    assert [tool.name for tool in filtered] == ["zoom_meeting_creator"]


def test_filter_tools_keeps_network_tools_with_army_preserved():
    tools = [FakeTool("zoom_meeting_creator"), FakeTool("ping_host"), FakeTool("show_device_command")]

    filtered = filter_tools_for_army_preserved(tools, army_preserved_confirmed=True)

    assert [tool.name for tool in filtered] == [
        "zoom_meeting_creator",
        "ping_host",
        "show_device_command",
    ]


def test_middleware_hides_network_tools_without_army_preserved():
    request = FakeRequest(
        [FakeTool("zoom_meeting_creator"), FakeTool("ping_host")],
        AgentRuntimeContext(army_preserved_confirmed=False),
    )

    response_tools = filter_network_tools.wrap_model_call(
        request,
        lambda filtered_request: filtered_request.tools,
    )

    assert [tool.name for tool in response_tools] == ["zoom_meeting_creator"]


def test_middleware_keeps_network_tools_with_army_preserved():
    request = FakeRequest(
        [FakeTool("zoom_meeting_creator"), FakeTool("ping_host")],
        AgentRuntimeContext(army_preserved_confirmed=True),
    )

    response_tools = filter_network_tools.wrap_model_call(
        request,
        lambda filtered_request: filtered_request.tools,
    )

    assert [tool.name for tool in response_tools] == [
        "zoom_meeting_creator",
        "ping_host",
    ]


def test_tool_registry_splits_network_tools_from_base_tools():
    network_tool_names = {tool.name for tool in network_diagnostic_tools}
    base_tool_names = {tool.name for tool in base_tools}
    all_tool_names = {tool.name for tool in all_tools}

    assert network_tool_names == {
        "ping_host",
        "trace_route",
        "dns_lookup",
        "show_device_command",
        "parse_show_output",
    }
    assert network_tool_names.isdisjoint(base_tool_names)
    assert network_tool_names.issubset(all_tool_names)


def test_agent_runtime_context_defaults():
    context = AgentRuntimeContext(army_preserved_confirmed=True)

    assert context.army_preserved_confirmed is True
    assert context.client_name is None
    assert context.network_context is None
