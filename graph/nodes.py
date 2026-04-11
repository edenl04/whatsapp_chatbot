from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage


from .constant import LLM, TIME_PHRASES_LIST, ADMIN_GROUP_NAME
from .state_and_schamas import *
from .tools.tools import all_tools
load_dotenv()

str_parser = StrOutputParser()

# only returns "need_to","don't_need_to"
def need_to_translate_to_eng_node(state):
    print("**entering need_to_translate_to_eng_node**")
    user_input = state["user_input"]
    translate_prompt = ChatPromptTemplate(
        [
            ("system",
             """your task is to figer out when the user query is whiten in english or not, when its not you need to translate to english.
             when you have to translate to english write need_to and when you don't write don't_need_to 
             """,),
            ("human", "{user_message}"),
        ])

    chain = translate_prompt | LLM.with_structured_output(Need_translation_schama)
    result = chain.invoke({"user_message": user_input})
    return {"condition": result.translate,"user_query_language": result.language, "send_answer_to": state["client_name"] }

def translation_to_english_node(state):
    print("**entering translation_node**")
    user_input = state["user_input"]

    translate_prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
                """You are expert translater.
                your task it to translate human massage to english.
                1) check if the following is present and change it if necessary:
                    if the user writing one of  (סדב,סודי ביותר ,סד"ב) translate it to army.TS_idf,
                    if the user writing one of  (צהלנט,סודי) translate it to army.S_idf,
                    if the user writing one of  (רשת אזרחי, אזרחי) translate it to army.civil,
                    if the user writing one of  (אבן, תפש, תפ"ש, רשת אבן) translate it to army.preserved,
                    if the user writing one of  (הלבנה) translate it to Halavana,
                    if the user writing one of  (השחרה) translate it to HaShkharah ,
                    if the user writing one of  (יובל, מערכת יובל) translate it to yuval.system ,
                    if the user writing one of  (שביט, מערכת שביט) translate it to comet.system ,
                    if the user writing one of  (שבתאי, מערכת שבתאי) translate it to saturn.system ,
                    if the user writes (אבן החכמים) translate it to smart.even,
                    if the user writes (אקטיב) translate it to active directory, 
                    if the user writes (עץ התמר) translate it to tamar.tree, 
                    
                2) translate the user query as best as you can
                """,),
            ("human", "{user_message}"),
        ])
    translate_chain = translate_prompt | LLM | str_parser
    result = translate_chain.invoke({"user_message":user_input})
    return {"translated_input": result}


# only returns "need_to","don't_need_to", "don't_interact"
def router_node(state):
    #  will return yes or no (need to create a schama for that)
    print("**entering router_node**")
    user_input = state.get("translated_input") or state["user_input"]
    chat_history = state.get("chat_history") or []

    router_prompt = ChatPromptTemplate(
        [
            ("system",
             """You are an expert IT network administrator and routing assistant.
                Your task is to analyze the client's query and route it to exactly one of the four categories below. 

                Analyze the user's message and select the most appropriate routing option based on these prioritized rules:

                1. need_to_send_form
                   - The user requests, returns, or needs new hardware/peripherals.
                   - The user needs to create or open a user account (regardless of the network).

                2. don't_interact
                   - The query is just thanking you.
                   - The user only provides a PC name that begins with 'tsng0467', 'ac0467', or 'aytpsh' without a specific request.
                   - The user specifically requests to print something.

                3. don't_need_to
                   - The user mentions specific systems: 'tamar.tree', 'active directory', 'smart.even', 'saturn.system', or 'comet.system'.
                   - The user requests a meeting/Zoom and provides ALL required details: a specific start and end time (e.g., 11:00-12:00) AND a date (e.g., tomorrow, 14.5).
                   - The user requests a file transfer ('Halavana' or 'HaShkharah') and has already provided ALL necessary details (both source and destination networks).
                   - The client has provided all the necessary information for you to fully resolve their issue without asking follow-up questions.

                4. need_to (Use this when information is missing)
                   - The user request is too general or implies a problem but does not specify exactly what it is.
                   - The user mentions a PC or phone but DOES NOT specify which network they are on (one of: 'army.TS_idf', 'army.S_idf', 'army.civil', 'army.preserved').
                   - The user requests a file transfer ('Halavana' or 'HaShkharah') but is MISSING details (e.g., missing the source or destination network, or recipient).
                   - The user requests a meeting but is MISSING the start/end time or the date.

                Always evaluate the rules in the order above. If the input matches multiple categories, select the most specific matching category.
             """,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}"),
        )])

    chain = router_prompt | LLM.with_structured_output(Router_schama)
    result = chain.invoke({"user_message": user_input, "chat_history": chat_history})
    return {"condition": result.router}


def send_form_node(state):
    print("**entering send_form_node**")


    user_input = state.get("translated_input") or state["user_input"]
    chat_history = state.get("chat_history") or []

    form_prompt = ChatPromptTemplate(
        [
            ("system",
             """ you have one test and that is to Determine what form the user 
             when the user need to open or create a user write user_form.
             when the user asking for Peripherals and Hardware write hardware_form
             
             """,),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}"),
        ])

    chain = form_prompt | LLM.with_structured_output(What_form_to_send_schama)
    result = chain.invoke({"user_message": user_input, "chat_history": chat_history})

    import os
    form = result.form
    # Calculate the root directory ('new_files') dynamically relative to the current file ('nodes.py')
    main_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if form == "user_form":
        file_path = os.path.join(main_root, "forms", "users form.docx")
        where_to_give = "after you fill out the form you need to come to tikshove office"

    else:
        file_path = os.path.join(main_root, "forms", "Hardware form.docx")
        where_to_give = "after you fill out the send to my whatsapp "


    return {"main_node_output": where_to_give, "file_path": file_path}


def ask_for_more_info_node(state):
    #  ask the user for more info
    print("**entering ask_for_more_info_node**")
    user_input = state.get("translated_input") or state["user_input"]

    info_prompt = ChatPromptTemplate(
        [
            ("system",
             """ you are a network administrator and yor name is note relevant  
             your job is to ask the client for more information for for helping them solve Any problem they have:
             core information that is needed:
             1) check if the client mentioned one of the network (one of army.TS_idf, army.S_idf, army.civil, army.preserved).
             2) when the client is mentioning Halavana and HaShkharah he most provide wrote 2 network names that are not the same and to whom or where to send the file.
             3) think if the client gave you sufficient information 
             4) when the user didn't spiffy start and end time, a for the for a meeting ask when for that info 
             
            Ask only the relevant questions based on the user's query. If any required information is missing, prompt the user to provide it.
            when the user to smell talk with you DON'T ask for more information
            
            note: when the user ask for a meeting only ask about point 4 


             """,),
            ("human", "{user_message}"),
        ]).partial()
    chain = info_prompt | LLM | str_parser
    result = chain.invoke({"user_message":user_input})
    return {"main_node_output": result}


# only returns "need_to","don't_need_to"
def has_admin_privileges_node(state):
    #  will return yes or no (need to create a schama for that)
    print("**entering has_admin_privileges_node**")
    user_input = state.get("translated_input") or state["user_input"]
    client_name = state.get("client_name")

    if "admin" in client_name:
        have_privileges = "need_to"

    else:
        has_privileges_prompt = ChatPromptTemplate(
            [
                ("system",
                 """ you are a network administrator 
                 your job is to figure out if the client have the right privileges to solve the problem he have.
                 when does he have the right privileges:
                 1) when the client is working on army.civil
                 2) when the client is asking for help with any thing related to android or apple phones
                 3) when the client when to create a meeting but there us not a spiffy start and end time 
                 
                 when he doesn't have:
                 1) when he need to put a username and passwork to bypass admin privileges when its not on army.civil network 
                 2) when he wants to be add to a security group (it's allways in the active directory)
                 3) when the client is mentioning Halavana and HaShkharah he doesn't have privileges fo it 
                 4) when the user is asking for partitions for comet.system, saturn.system, smart.even, active directory, tamar.tree
                 """,),
                ("human", "{user_message}"),
            ]).partial(user_message=user_input,client_name=client_name)
        chain = has_privileges_prompt | LLM.with_structured_output(Have_admin_privileges)
        result = chain.invoke({})
        have_privileges = result.have_admin

    return {"condition": have_privileges}


def format_problem_to_admins_node(state):
    # organize all the in formation to the admins
    print("**entering send_to_admin_group_code**")
    user_input = state.get("translated_input") or state["user_input"]
    chat_history = state.get("chat_history") or []
    client_name = state["client_name"]

    msg_to_prompt = ChatPromptTemplate(
        [
            ("system",
             """you are an expert Editor,
             Your task is to write all the information that the user provided in in one organize text massage,
             name of the client {client_name} 
             write it like:
             client: the name of the client
             client problem : describe in details the problem the user have

             Don't write the name of the user before client:

             """,),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}"),
        ])
    chain = msg_to_prompt | LLM
    result = chain.invoke({"user_message": user_input, "client_name": client_name, "chat_history": chat_history})
    return {"main_node_output": result.content, "send_answer_to": ADMIN_GROUP_NAME}


def react_agent_node(state):
    print("**entering react_agent_node**")
    user_input = state.get("translated_input") or state["user_input"]

    chat_history_list = []
    chat_history = state.get("chat_history") or []
    for msg in chat_history:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        chat_history_list.append(f"{role}: {msg.content}")

    chat_history_str = "\n".join(chat_history_list)

    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    template = f'''Today's date is {today_date}.

    You have access to the following tools:

    1. Meeting Creator: Create Zoom meetings by converting natural language requests into exact ISO 8601 date/time and meeting details.
    2. Web Search: Search the internet for any additional information needed to answer questions or clarify user requests.

    Always use the Web Search tool whenever you need more information beyond what is provided.

    When the user requests a meeting using natural phrases like:
    {', '.join(TIME_PHRASES_LIST)}

    — automatically convert these into an exact date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS), using today's date as the reference point.

    Decide carefully which tool to call based on the user's input. If no tool is needed, respond directly.
    Chat history:
    {{chat_history}}
    
    Answer the following questions as best you can. You have access to the following tools:

    {{tools}}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{{tool_names}}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {{input}}
    Thought:{{agent_scratchpad}}

    note: when the user ask for a meeting and somthing like 13-14 he means 13:00-14:00
    '''

    react_prompt = PromptTemplate.from_template(template)

    print(react_prompt)
    agent = create_react_agent(
        LLM, tools=all_tools,
        prompt=react_prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, handle_parsing_errors=True, verbose=True,
                                   max_iterations=5)
    response = agent_executor.invoke({"input": user_input, "chat_history": chat_history_str})
    print(f"response = {response}")
    return {"main_node_output": str(response["output"])}

def organize_answer_node(state):
    # its organize the output of the React agent node
    print("**entering organize_answer_node**")
    agent_answer = state["main_node_output"]
    print(f"react output : {agent_answer}")
    organize_prompt = ChatPromptTemplate(
        [
            ("system",
             """you are an expert Editor,
             Your task is to rewrite and organize the user's query into clear and simple human language.
             when there is an information the user don't need cut it from your answer when:
             - there is a statues True or False  
             - Don't add or ask additional information
             """,),
            ("human", "{user_message}"),
        ])
    chain = organize_prompt | LLM
    result = chain.invoke({"user_message": agent_answer})
    return {"main_node_output": result.content}


def translate_back_conditional_node(state):
    print("**entering translate_back_conditional_node**")

    agent_response = state.get("main_node_output")
    original_lang_output = state.get("user_query_language")

    translate_back_prompt = ChatPromptTemplate(
        [
            ("system",
             """ 
             your tesk is to fond if the user query in the same language as {original_lang}
             """,),
            ("human", "{agent_response}"),
        ]).partial(agent_response=agent_response, original_lang= original_lang_output)
    chain = translate_back_prompt | LLM.with_structured_output(Need_translate_back)
    result = chain.invoke({})
    return {"condition": result.translate}



def translate_to_original_language_node(state):
    # translate the response of the llm to its original language
    print("**entering translate_to_original_language_node**")
    agent_output = state.get("main_node_output")
    translate_prompt = ChatPromptTemplate(
        [
            ("system",
                """You are an expert, professional translator.
                Your task is to accurately translate the provided message into {original_language}.
                
                You must strictly follow this terminology glossary when translating network and system names. Do NOT use literal translations for these terms:
                
                - army.TS_idf -> סד"ב
                - army.S_idf -> סודי
                - army.civil -> רשת אזרחי
                - army.preserved -> תפ"ש
                - Halavana -> הלבנה
                - HaShkharah -> השחרה
                - comet.system -> מערכת שביט
                - saturn.system -> מערכת שבתאי
                - smart.even -> אבן החכמים
                - active directory -> אקטיב
                - tamar.tree -> עץ התמר

                Constraints:
                1. Translate the message fluidly and naturally while preserving the exact technical terms from the glossary above.
                2. Output ONLY the translated text. Do NOT include any conversational filler, explanations, formatting, or comments.
                """,),
            ("human", "{user_message}"),
        ])
    translate_chain = translate_prompt | LLM | str_parser
    result = translate_chain.invoke({"user_message":agent_output,"original_language": state["user_query_language"]})
    return {"main_node_output": result}


if __name__ == "__main__":
    system_message = AIMessage(content="You are a helpful IT support assistant.")
    human_message = HumanMessage(content="My computer won't let me install new software. What should I do?")
    ai_msg = AIMessage(content="on what pc network do you have the problem")

    history_chat = [system_message, human_message, ai_msg ]



    state = {"user_input": """היי יש לי בעיה  שלי משהו יכול לבוא לעזור לי  """,
             "translated_input":"hi how are you ",
             "user_query_language": "english",
             "chat_history":history_chat,
             "client_name": "Adam",
             "send_answer_to": ADMIN_GROUP_NAME,
#              "main_node_output":["""The meeting 'tikshov meeting' was successfully created. Here are the details:
#
# *   **Meeting ID:** 78369691759
# *   **Password:** r2Xq89
# *   **Join URL:**
# *   **App URL:** zoommtg://zoom.us/join?confno=78369691759&pwd=r2Xq89
# *   **Start Time:** 2025-05-05T13:00:00
# *   **Duration:** 30 minutes
             # """]

             }
    node_output = ask_for_more_info_node(state)
    print(node_output)
    print(type(node_output))