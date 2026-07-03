import asyncio

WHATSAPP_LINK = "https://web.whatsapp.com/"
MAX_PARALLEL_AGENTS = 3
ADMIN_ACK_MESSAGE = (
    "\u05de\u05d4 \u05e9\u05d1\u05d9\u05e7\u05e9\u05ea "
    "\u05d9\u05d5\u05e9\u05dc\u05dd \u05d1\u05d4\u05e7\u05d3\u05dd "
    "\u05d4\u05d0\u05e4\u05e9\u05e8\u05d9, \u05d1\u05d4\u05ea\u05d0\u05dd "
    "\u05dc\u05e1\u05d3\u05e8\u05d9 \u05d4\u05e2\u05d3\u05d9\u05e4\u05d5\u05d9\u05d5\u05ea "
    "\u05d5\u05dc\u05de\u05d4\u05dc\u05da \u05d4\u05ea\u05e7\u05d9\u05df "
    "\u05e9\u05dc \u05d4\u05ea\u05d4\u05dc\u05d9\u05da."
)


def get_default_graph():
    from graph.graph import graph

    return graph


def get_admin_group_name():
    from graph.constant import ADMIN_GROUP_NAME

    return ADMIN_GROUP_NAME


def get_whatsapp_classes():
    from whatsapp_scraper import Send_WhatsApp_Message, WhatsAppScraper

    return Send_WhatsApp_Message, WhatsAppScraper


async def process_chat(chat_name, chat_messages, agent_graph=None, semaphore=None):
    print(f"from : {chat_name}")

    if not chat_messages:
        return {
            "chat_name": chat_name,
            "response": None,
            "error": "No messages found for chat",
        }

    state = {
        "user_input": chat_messages[-1],
        "chat_history": chat_messages[:-1],
        "client_name": chat_name,
    }

    try:
        if agent_graph is None:
            agent_graph = get_default_graph()

        if semaphore is None:
            response = await asyncio.to_thread(agent_graph.invoke, state)
        else:
            async with semaphore:
                response = await asyncio.to_thread(agent_graph.invoke, state)

        return {
            "chat_name": chat_name,
            "response": response,
            "error": None,
        }
    except Exception as error:
        print(f"Failed to process chat {chat_name}: {error}")
        return {
            "chat_name": chat_name,
            "response": None,
            "error": str(error),
        }


async def send_response(response, sender_cls=None, admin_group_name=None):
    if sender_cls is None:
        sender_cls, _ = get_whatsapp_classes()
    if admin_group_name is None:
        admin_group_name = get_admin_group_name()

    agent_output = response.get("main_node_output")
    file_path = response.get("file_path")
    print(f"agent_output: {agent_output}")

    if agent_output is None:
        return

    sender = await sender_cls.create(
        initial_link=WHATSAPP_LINK,
        send_to=response["send_answer_to"],
        msg_to_send=agent_output,
        file_path=file_path,
    )

    try:
        if file_path is not None:
            await sender.send_file_to_user()
        elif "tinyurl.com" in agent_output:
            await sender.send_one_bubble_message()
        elif response["send_answer_to"] == admin_group_name:
            print("sending message to admin")
            await sender.send_one_bubble_message()
            await sender.clear_chat_search()
            await sender.send_message_to_user(
                send_to=response.get("client_name"),
                msg_to_send=ADMIN_ACK_MESSAGE,
            )
        else:
            await sender.send_message_to_user()

        await asyncio.sleep(1)
    finally:
        await sender.browser.close()


async def main(need_to_wait):
    _, scraper_cls = get_whatsapp_classes()

    scraper = await scraper_cls.create(initial_link=WHATSAPP_LINK)
    if need_to_wait:
        await asyncio.sleep(10)

    today_chat_messages = await scraper.get_unread_chats()
    await scraper.browser.close()

    agent_semaphore = asyncio.Semaphore(MAX_PARALLEL_AGENTS)
    chat_results = await asyncio.gather(
        *[
            process_chat(chat_name, chat_messages, semaphore=agent_semaphore)
            for chat_name, chat_messages in today_chat_messages.items()
        ]
    )

    for chat_result in chat_results:
        if chat_result["error"] is not None:
            continue
        await send_response(chat_result["response"])


if __name__ == "__main__":
    need_to_wait = True
    while True:
        asyncio.run(main(need_to_wait))
        need_to_wait = False
