from whatsapp_scraper import WhatsAppScraper, Send_WhatsApp_Message
from graph.constant import ADMIN_GROUP_NAME

from langchain_core.messages import HumanMessage, AIMessage
from graph.graph import graph
import asyncio

WHATSAPP_LINK = 'https://web.whatsapp.com/'

async def main(need_to_wait):

    scraper = await WhatsAppScraper.create(initial_link=WHATSAPP_LINK)
    if need_to_wait:
        await asyncio.sleep(10)

    today_chat_messages = await scraper.get_unread_chats()

    await scraper.browser.close()

    for chat_name, chat_messages in today_chat_messages.items():
        print(f"from : {chat_name}")
        chat_history = chat_messages[:-1]
        user_last_msg = chat_messages[-1]

        response = graph.invoke({
            "user_input": user_last_msg,
            "chat_history": chat_history,
            "client_name": chat_name,
            })

        # print(response)
        send_msg_to = response["send_answer_to"]
        client_name = response.get("client_name")
        agent_output = response.get("main_node_output", None)
        file_path = response.get("file_path", None)
        print(f"agent_output: {agent_output}")

        if agent_output is not None:
            sender = await Send_WhatsApp_Message.create(initial_link=WHATSAPP_LINK,
                                                        send_to=send_msg_to,
                                                        msg_to_send=agent_output,
                                                        file_path=file_path)

            if file_path is None:
                if "tinyurl.com" in agent_output:
                    await sender.send_one_bubble_message()

                elif response["send_answer_to"] == ADMIN_GROUP_NAME:
                    print("sending message to admin")
                    await sender.send_one_bubble_message()
                    await sender.clear_chat_search()
                    await sender.send_message_to_user(send_to=client_name,
                                                      msg_to_send="מה שביקשתה יושלם בהקדם האפשרי, בהתאם לסדרי העדיפויות ולמהלך התקין של התהליך." )
                else:
                    await sender.send_message_to_user()
            else:
                await sender.send_file_to_user()
            await asyncio.sleep(1)

            await sender.browser.close()
        else:
            continue




async def test():
    response = {'user_input': HumanMessage(content='היי, אשמח לזום למחר מ08:15-09:15', additional_kwargs={}, response_metadata={}), 'user_query_language': 'hebrew', 'translated_input': 'Hi, I would like to have a Zoom meeting tomorrow from 08:15-09:15.', 'condition': 'need_to', 'main_node_output': 'הפגישה "פגישת תקשוב" נוצרה בהצלחה עם מזהה פגישה 78698995041.\n\n*   **קישור הצטרפות:** tinyurl.com/yurxs4lz\n*   **סיסמה:** 892jrM\n*   **זמן התחלה:** 2025-05-17 בשעה 08:15\n*   **משך:** 60 דקות', 'client_name': 'משוב קיריה', 'send_answer_to': 'משוב קיריה'}


    send_msg_to = response["send_answer_to"]
    agent_output = response.get("main_node_output", None)
    file_path = response.get("file_path", None)
    print(f"agent_output: {agent_output}")

    if agent_output is not None:
        sender = await Send_WhatsApp_Message.create(initial_link=WHATSAPP_LINK,
                                                    send_to=send_msg_to,
                                                    msg_to_send=agent_output,
                                                    file_path=file_path)

        if file_path is None:
            if "tinyurl.com" in agent_output or response["client_name"] == ADMIN_GROUP_NAME:
                await sender.send_one_bubble_message()
            else:
                await sender.send_message_to_user()
        else:
            await sender.send_file_to_user()

        await asyncio.sleep(1)

        await sender.browser.close()


if __name__ == '__main__':
    need_to_wait = True
    while True:
        asyncio.run(main(need_to_wait))

        need_to_wait = False




