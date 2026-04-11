from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import TypedDict, Literal, List, Optional,Optional, Annotated
from langchain_core.messages.base import BaseMessage
import operator


load_dotenv()

class State(TypedDict):
    user_input: str
    chat_history: Optional[List[BaseMessage]]
    user_query_language: Optional[str]
    translated_input: Optional[str]
    condition: Optional[Literal["need_to", "don't_need_to","need_to_send_form", "don't_interact"]]
    main_node_output: Optional[List[str]]
    client_name: Optional[str]
    send_answer_to: Optional[str]
    file_path: Optional[str]


# for need_translation_to_eng_conditional func
class Need_translation_schama(BaseModel):
    translate: Literal["need_to","don't_need_to"] = Field(description="Determine if translation to English is needed")
    language: str = Field(description="Detected language of the user input")


class Router_schama(BaseModel):
    router:Literal["need_to","don't_need_to","need_to_send_form","don't_interact"] = Field(
        description="check if the you have enough information to help the user write"
                    " need_to if there isn't sufficient information and don't_need_to if it is"
                    " and don't_interact when there is no need to interact with the user ")

class What_form_to_send_schama(BaseModel):
    form:  Literal["user_form","hardware_form"] = Field(description="Determine what form the user needs")

# for check_if_there_enough_info func or
class Need_more_info_schama(BaseModel):
    more_info:  Literal["need_to","don't_need_to"] = Field(description="Determine if the you have enough information to help the user write need_to if there sufficient information and don't_need_to if it isn't ")


# for checking the user have the right promotion to solve the problem
class Have_admin_privileges(BaseModel):
    have_admin: Literal["need_to", "don't_need_to"] = Field(description="""Determine if the user have the right privileges to solve the problem by himself.
                                                                         write don't_need_to if he doesn't have the privileges and need_to if he have them""")

class Need_translate_back(BaseModel):
    translate: Literal["need_to", "don't_need_to"] = Field(description="write need_to if it is don't_need_to and if it isn't")

if __name__ == "__main__":
    pass