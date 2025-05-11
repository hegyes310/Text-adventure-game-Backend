from langchain.prompts import PromptTemplate
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os


class CharacterExtractor:
    def __init__(self):
        load_dotenv()
        self.llm = ChatOllama(
            model=os.environ.get("CHARACTER_EXTRACTOR_MODEL", "llama3.1:8b-instruct-q8_0"),
            temprature=0.4,
            disable_streaming=True,
            format="json"
        )
        self.chain = self.create_prompt() | self.llm
        self.json_format = """Please return the result as a JSON object with the following format:
        {
          "characters": [
            {
              "name": "Character Name 1",
              "should_react": "Yes or No",
              "quest": "Yes or No"
            },
            {
              "name": "Character Name 2",
              "should_react": "Yes or No",
              "quest": "Yes or No"
            }
          ]
        }"""

    def create_prompt(self) -> PromptTemplate:
        prompt_template = """You are an expert language model trained to analyze narrative text from text-based games. Your task is to extract all character names mentioned in the following narrative, which includes both Game Master (GM) narration and player input.

        {json_format}

        Instructions:
        - Only include proper names of persons and if they should react or not.
        - A character "should_react" if the player message clearly addresses or implies interaction with them.
        - If the player is going to another place or location, DO NOT consider reactivity at all; all "should_react" values must be "No".
        - If a character dies, "should_react" must be "No".
        - Do not include roles or generic nouns unless they are clearly used as character names.
        - Do not include the player’s own character name, unless it is referenced as a third person.
        - If no characters are mentioned, return an empty array.
        
        Quest detection:
        - Set "quest" to "Yes" **only if ALL** of the following are true:
          - The player message explicitly uses the word "quest" or "mission".
          - The player expresses intent to **get** or **ask for** a quest.
          - The player refers to or addresses a specific character in this context.
        - If any of the above is missing, "quest" must be "No".
        - If the player refuses a quest or says the quest is done, "quest" must be "No".
        - The word "job", "task", or other synonyms do not count unless "quest" or "mission" is also clearly mentioned.
        
        Examples:
        
        1. Player input: "I ask Eldric if he has a quest for me."
           → quest: Yes for Eldric, should_react: Yes
        
        2. Player input: "Does anyone in town have a mission?"
           → quest: No (no character referenced)
        
        3. Player input: "Thanks for the help, Aria. I’m going to the blacksmith now."
           → quest: No, should_react: No (player is leaving)
        
        4. Player input: "Yes, I’m up for the job! I’m going to the main building."
           → quest: No, should_react: No (movement involved, no quest requested)
        
        5. Player input: "Tell Marcus the quest is completed."
           → quest: No for Marcus, should_react: Yes

        Game Master narrative:
        {narrative}

        Player input:
        {player_input}
        """

        return PromptTemplate(
            input_variables=["json_format", "narrative", "player_input"],
            template=prompt_template
        )

    def extract_characters(self, game_master_response: str, player_message: str) -> BaseMessage:
        chain_output = self.chain.invoke({
            "json_format": self.json_format,
            "narrative": game_master_response,
            "player_input": player_message
        })
        return chain_output
