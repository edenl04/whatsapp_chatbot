from langchain_core.messages import  HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langchain_core.runnables.graph import MermaidDrawMethod

from .state_and_schamas import State
from .constant import *
from .nodes import *

load_dotenv()


def need_translation_to_eng_conditional(state: State):
    print("**entering need_translation_to_eng_conditional**")
    condition = state.get("condition")
    print(f"condition = {condition}")
    if condition == "need_to":
        return TRANSLATE_TO_ENG_NODE
    elif condition == "don't_need_to":
        return ROUTER_NODE
    else:
        # condition is None or unexpected value
        return TRANSLATE_TO_ENG_NODE

def router_conditional(state):
    print("**entering router_conditional**")
    condition = state["condition"]
    print(f"condition = {condition}")

    if condition == "need_to":
        return ASK_FOR_MORE_INFO_NODE
    elif condition == "don't_need_to":
        return CHECK_IF_USER_HAVE_ADMIN_NODE
    elif condition == "need_to_send_form":
        return SEND_A_FORM_NOD
    else:
        return END


def conditional_admin_privileges(state):
    # it will return yes or no and then will go to the right node it will get it from the has_admin_privileges_node
    print("**entering conditional_admin_privileges**")
    condition = state["condition"]
    print(f"condition = {condition}")

    if condition == "need_to":
        return REACT_NODE
    else:
        return FORMAT_PROBLEM_TO_ADMINS


def need_translation_to_original_language_conditional(state):
    # it will return yes or no and then will go to the right node
    print("**entering need_translation_conditional**")
    condition = state["condition"]
    print(f"condition = {condition}")

    if condition == "need_to" :
        return TRANSLATE_BACK_NODE
    else:
        return END


workflow = StateGraph(State)

workflow.add_node(CHECK_IF_NEED_TO_TRANSLATE, need_to_translate_to_eng_node)
workflow.add_node(TRANSLATE_TO_ENG_NODE,translation_to_english_node)
workflow.add_node(ROUTER_NODE, router_node)
workflow.add_node(SEND_A_FORM_NOD, send_form_node)
workflow.add_node(ASK_FOR_MORE_INFO_NODE, ask_for_more_info_node)
workflow.add_node(CHECK_IF_USER_HAVE_ADMIN_NODE, has_admin_privileges_node)
workflow.add_node(REACT_NODE, react_agent_node)
workflow.add_node(FORMAT_PROBLEM_TO_ADMINS,format_problem_to_admins_node)
workflow.add_node(ORGANIZE_ANSWER_NODE ,organize_answer_node)
workflow.add_node(TRANSLATE_BACK_CONDITIONAL, translate_back_conditional_node)
workflow.add_node(TRANSLATE_BACK_NODE, translate_to_original_language_node)
# workflow.add_node(SEND_TO_USER_OR_ADMIN, sending_output_node)


workflow.add_edge(START,CHECK_IF_NEED_TO_TRANSLATE)
workflow.add_conditional_edges(
    CHECK_IF_NEED_TO_TRANSLATE,
    need_translation_to_eng_conditional,
    {
        TRANSLATE_TO_ENG_NODE: TRANSLATE_TO_ENG_NODE,
        ROUTER_NODE: ROUTER_NODE,
    }
)

workflow.add_edge(TRANSLATE_TO_ENG_NODE, ROUTER_NODE)
workflow.add_conditional_edges(
    ROUTER_NODE,
    router_conditional,
    {
        ASK_FOR_MORE_INFO_NODE: ASK_FOR_MORE_INFO_NODE,
        CHECK_IF_USER_HAVE_ADMIN_NODE: CHECK_IF_USER_HAVE_ADMIN_NODE,
        SEND_A_FORM_NOD:SEND_A_FORM_NOD,
        END: END,
    }
)

workflow.add_conditional_edges(
    CHECK_IF_USER_HAVE_ADMIN_NODE,
    conditional_admin_privileges,
    {
        REACT_NODE: REACT_NODE,
        FORMAT_PROBLEM_TO_ADMINS: FORMAT_PROBLEM_TO_ADMINS,
    }
)

workflow.add_edge(REACT_NODE, ORGANIZE_ANSWER_NODE)

for node in [ASK_FOR_MORE_INFO_NODE, ORGANIZE_ANSWER_NODE, FORMAT_PROBLEM_TO_ADMINS, SEND_A_FORM_NOD]:
    workflow.add_edge(node, TRANSLATE_BACK_CONDITIONAL)

workflow.add_conditional_edges(TRANSLATE_BACK_CONDITIONAL,
                               need_translation_to_original_language_conditional,
                               {
                                   TRANSLATE_BACK_NODE: TRANSLATE_BACK_NODE,
                                   END: END,
                               }
                               )

workflow.add_edge(TRANSLATE_BACK_NODE,END)
# workflow.add_edge(SEND_TO_USER_OR_ADMIN, END)

graph = workflow.compile()

# graph.get_graph().draw_mermaid_png(
#     output_file_path="graph.png",
# )


if __name__ == "__main__":
    user_input = "hii"
    response = graph.invoke({
        # "condition":"need_to",
        "user_input": user_input,
        "client_name": "User",  # Add required fields from your State
        "send_answer_to": "User"})
    print(response)