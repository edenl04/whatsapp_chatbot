from langchain_core.messages import HumanMessage, AIMessage
from pyppeteer import launch
import asyncio
import time

from graph.constant import WHATSAPP_LINK, CHROME_PATH, SELENIUM_PROFILE_PATH

class WhatsAppScraper:
    def __init__(self, browser, page):
        self.browser = browser
        self.page = page

    @classmethod
    async def create(cls, initial_link: str):
        browser = await launch(
            executablePath=CHROME_PATH,
            headless=False,
            args=[f'--user-data-dir={SELENIUM_PROFILE_PATH}']
        )
        page = await browser.newPage()
        await page.goto(initial_link)
        return cls(browser, page)

    async def __wait_for_button_and_click(self, xpath_before_click: str, xpath_after_click: str):
        # Wait for the element to appear
        print("Waiting for button with nested <div> containing 'Unread'...")
        button_element = await self.page.waitForXPath(xpath_before_click)

        await self.page.evaluate('(el) => el.click()', button_element)
        print("Button clicked!")

        # Wait for the button to be clicked
        await self.page.waitForXPath(xpath_after_click)

    async def __get_elements_by_xpath(self, xpath: str):
        elements = await self.page.xpath(xpath)
        print(f'Found {len(elements)} unread chats')
        return elements

    async def __extract_messages(self):
        print("Waiting for messages to load...")

        try:
            await self.page.waitForSelector('div.focusable-list-item', {'timeout': 15000})

            messages_list = []

            message_elements = await self.page.querySelectorAll('div.focusable-list-item')
            print(f"Found {len(message_elements)} message elements")

            max_elements = 30
            elements_to_process = min(len(message_elements), max_elements)

            for i in range(elements_to_process):
                element = message_elements[i]

                class_list = await self.page.evaluate('(el) => el.className', element)
                print(f"class_list : {class_list}")
                is_outgoing = 'message-out' in class_list

                text = await self.__extract_message_text(element)
                if text and text.strip():
                    if is_outgoing:
                        messages_list.append(AIMessage(content=text.strip()))
                    else:
                        messages_list.append(HumanMessage(content=text.strip()))

            print(f"Processed {len(messages_list)} messages")
            print(f"list : {messages_list}")

            return messages_list

        except Exception as e:
            print(f"Error extracting messages: {e}")
            return []

    async def __extract_message_text(self, element):
        """Extract text from a message element using multiple strategies."""
        text = ""

        # Strategy 1: Try to find copyable-text with selectable-text span
        try:
            copyable_text = await element.querySelector('div.copyable-text')
            if copyable_text:
                selectable_text = await copyable_text.querySelector('span.selectable-text')
                if selectable_text:
                    text = await self.page.evaluate('(el) => el.textContent', selectable_text)
        except Exception:
            pass

        # Strategy 2: Try alternative selectors if no text found
        if not text:
            try:
                for selector in ['span.selectable-text', 'div._amlr', 'div.xjb2p0i']:
                    content_el = await element.querySelector(selector)
                    if content_el:
                        text = await self.page.evaluate('(el) => el.textContent', content_el)
                        if text:
                            break
            except Exception:
                pass

        # Strategy 3: Last resort - get all text content from the element
        if not text:
            try:
                text = await self.page.evaluate('(el) => el.textContent', element)
            except Exception:
                pass

        return text


    async def get_unread_chats(self):
        # Go to unread
        unread_button_xpath = '//button[.//div[text()="Unread"]]'
        unread_button_clicked_xpath = '//button[@aria-selected="true"][.//div[text()="Unread"]]'
        await self.__wait_for_button_and_click(
            xpath_before_click=unread_button_xpath,
            xpath_after_click=unread_button_clicked_xpath
        )

        # Get a list of all the unread chats
        list_items_xpath = '//div[@aria-label="Chat list"]//div[contains(@style, "z-index") and @role="listitem"]'
        unread_chats = await self.__get_elements_by_xpath(xpath=list_items_xpath)

        chat_dict = {}

        for chat in unread_chats:
            try:
                await chat.click()
                name_element = await chat.querySelector('div._ak8q')
                if name_element:
                    name_text = await (await name_element.getProperty('innerText')).jsonValue()
                    print("Chat name:", name_text)

                    # Extract messages after clicking on a chat
                    messages = await self.__extract_messages()
                    print(f"Found {len(messages)} messages in this chat")
                    print(f"list : {messages}")
                    chat_dict[name_text] = messages
                else:
                    print("can't retrieve chat name")

                await asyncio.sleep(1)

            except Exception as e:
                print(f"Failed to click chat: {e}")

        return chat_dict


class Send_WhatsApp_Message:
    def __init__(self, browser, page, send_to, msg_to_send=None, file_path=None):
        self.browser = browser
        self.page = page
        self.send_to = send_to
        self.msg_to_send = msg_to_send
        self.file_path = file_path

    @classmethod
    async def create(cls, initial_link: str, send_to: str, msg_to_send: str,file_path: str = None):
        browser = await launch(
            executablePath=CHROME_PATH,
            headless=False,
            args=[f'--user-data-dir={SELENIUM_PROFILE_PATH}']
        )
        page = await browser.newPage()
        await page.goto(initial_link)
        return cls(browser, page, send_to, msg_to_send, file_path)


    async def __open_chat(self):
        print("Opening chat...")
        try:
            await self.page.waitForSelector("p.selectable-text.copyable-text.x15bjb6t.x1n2onr6", {'timeout': 10000})
            await self.page.click("p.selectable-text.copyable-text.x15bjb6t.x1n2onr6")
            
            await self.page.type("p.selectable-text.copyable-text.x15bjb6t.x1n2onr6", self.send_to)

            await asyncio.sleep(1)
            
            await self.page.keyboard.press("Enter")
            
            print("Chat opened successfully")
        except Exception as e:
            print(f"Error opening chat: {e}")
            raise

    async def clear_chat_search(self):
        print("clearing chat search")
        try:
            await self.page.waitForSelector("p.selectable-text.copyable-text.x15bjb6t.x1n2onr6", {'timeout': 10000})
            await self.page.click("p.selectable-text.copyable-text.x15bjb6t.x1n2onr6")

            await self.page.keyboard.down('Control')
            await self.page.keyboard.press('A')
            await self.page.keyboard.up('Control')
            await self.page.keyboard.press('Backspace')

        except Exception as e:
            print(f"Error clearing chat: {e}")


    async def send_message_to_user(self, send_to=None, msg_to_send=None):
        # Update instance variables with new values if provided
        if send_to is not None:
            self.send_to = send_to
        if msg_to_send is not None:
            self.msg_to_send = msg_to_send

        await self.__open_chat()

        await self.page.waitForSelector('div._ak1r p.selectable-text.copyable-text.x15bjb6t.x1n2onr6',
                                        {'timeout': 10000})

        # Type and send the message
        await self.page.type('div._ak1r p.selectable-text.copyable-text.x15bjb6t.x1n2onr6', self.msg_to_send)
        await asyncio.sleep(2)

        await self.page.keyboard.press("Enter")
        print("message was sent ")

    async def send_one_bubble_message(self):
        await self.__open_chat()

        await self.page.waitForSelector('div._ak1r p.selectable-text.copyable-text.x15bjb6t.x1n2onr6',
                                        {'timeout': 10000})

        lines = self.msg_to_send.split('\n')

        for i, line in enumerate(lines):
            await self.page.type('div._ak1r p.selectable-text.copyable-text.x15bjb6t.x1n2onr6', line)
            if i < len(lines) - 1:
                await self.page.keyboard.down('Shift')
                await self.page.keyboard.press('Enter')
                await self.page.keyboard.up('Shift')

        await self.page.keyboard.press('Enter')

    async def send_to_admins_and_client(self):



        await asyncio.sleep(1)
        await self.page.keyboard.press('Enter')

        print("message was sent ")

    async def send_file_to_user(self):
        if self.file_path is not None:
            await self.__open_chat()

            # Wait for and click the attachment button (clip icon)
            attachment_button = 'div.x100vrsf.x1vqgdyp.x78zum5.x6s0dn4 button[title="Attach"]'
            try:
                await self.page.waitForSelector(attachment_button, {'timeout': 10000})
                await self.page.click(attachment_button)
                print("Clicked attachment button successfully")

                file_input = await self.page.waitForSelector('input[type="file"]', {'timeout': 10000})

                # Upload the file
                await file_input.uploadFile(self.file_path)
                print(f"Uploaded file: {self.file_path}")

                # Wait for the send button and click it
                send_button = 'span[data-icon="send"]'
                await self.page.waitForSelector(send_button, {'timeout': 10000})
                await self.page.click(send_button)
                print("File sent successfully")

                await self.send_message_to_user()

            except Exception as e:
                print(f"Error during file upload process: {e}")
                raise
        else:
            raise print("there is no file path provided")







async def main():
    scraper = await WhatsAppScraper.create(initial_link=WHATSAPP_LINK)
    # sender = await Send_WhatsApp_Message.create(initial_link=WHATSAPP_LINK, send_to="aviv", msg_to_send="test")
    
    x = await scraper.get_unread_chats()
    print(x)
    
    # Send the message
    # await sender.send_message_to_user()
    
    time.sleep(3)
    await scraper.browser.close()


if __name__ == '__main__':
    asyncio.run(main())