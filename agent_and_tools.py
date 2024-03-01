from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import BaseChatPromptTemplate
import re
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from typing import List, Union
from langchain_openai import ChatOpenAI
from langchain.chains.llm import LLMChain
from templates import default_message, default_npc


class AgentWithTools:
    def __init__(self, repository, chatbot):
        self.OPENAI_API_KEY = self.open_file('key_openai.txt')
        self.repository = repository
        self.chatbot = chatbot
        self.template = """Analyze the following sentences as best you can. You have access to the following tools:

            {tools}
            
            Use the following format:
            
            Sentence: the input sentence you must analyze
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times, but only once per tool)
            Thought: I now know the final answer
            Final Answer: the final answer is the tool output
            
            
            Sentence: {input}
            {agent_scratchpad}"""

        self.tools = [
            Tool(
                name="Trading with a character",
                func=self.characterIsATrader,
                description="Useful when the input text is about to start trade, shop or buying something. The input is the name of the character the with whom the player is talking."
            ),
            Tool(
                name="Fight",
                func=self.playerWantToFight,
                description="Useful when the input text is about to start a fight. The input format is the name of the character the player wants to fight."
            ),

            Tool(
                name="Set character name whom the player talking to",
                func=self.setNPCWhoThePlayerTalkingTo,
                #description="Useful only when the input text is about to initiate a conversation with a character. If the input text is about going somewhere, than dont use this tool. The input format is the name of the character the player wants to speak. This tool helps in identifying the target character for dialogue interaction and should be activated only when the player's input is explicitly focused on starting a conversation, and the character name is in the input. This tool should not be triggered when the player is introducing themselves or mentioning their own name."
                description="This is useful only when the input text explicitly mentions initiating a conversation with a character whose name is stated in the input text. This tool shouldn't be triggered when the input text is asking about the presence of people, like who is in the given location or place."
            ),
            Tool(
                name="Speaking with a character",
                func=self.speaking_with_a_character,
                description="Useful when the input text is indicates an ongoing or general conversation without specifying the character's name. It is designed for scenarios where the player is engaging in dialogue without the need to set a specific character name. This tool assists in processing and responding to player input that pertains to the ongoing narrative or general interactions within the game world, without requiring a predefined character target. This tool shouldn't be triggered when the input text is asking about the presence of people."
            ),
            Tool(
                name="Set player's location",
                func=self.set_playerlocation,
                description="Useful when the input text is indicates that the player going somewhere. It should be a place or location, and this tool shouldn't be triggered, when the the player go to a person or character. The input is the name of the location."
            ),
            Tool(
                name="Nothing above is true",
                func=self.continue_the_story,
                description="Useful when neither tool is true. Input is Nothing."
            )



        ]
        self.prompt = self.CustomPromptTemplate(
            template=self.template,
            tools=self.tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"]
        )

        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=self.OPENAI_API_KEY)

        self.output_parser = self.CustomOutputParser()

        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt)

        self.tool_names = [tool.name for tool in self.tools]

        self.agent = LLMSingleActionAgent(
            llm_chain=self.llm_chain,
            output_parser=self.output_parser,
            # We use "Observation" as our stop sequence so it will stop when it receives Tool output
            # If you change your prompt template you'll need to adjust this as well
            stop=["\nObservation:"],
            allowed_tools=self.tool_names
        )

        self.agent_executer = AgentExecutor.from_agent_and_tools(agent=self.agent, tools=self.tools, verbose=True)

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            return infile.read()

    def set_playerlocation(self, location_name):
        self.repository.setPlayerLocation(location_name)
        return "This are the informations about the location where the player went: " + self.repository.getPlayerLocationInfos()

    def continue_the_story(self, valami):
        #ide a default_template-et kell beállítani, a játékos jelenlegi tartózkodási helyével
        self.chatbot.set_default(self.repository.getPlayerLocationInfos())
        self.repository.setCharacterWithWhomThePlayerToNone()

        return "The player is continue the story. No other action or tool needed."

    def speaking_with_a_character(self, character=""):
        self.setNPCWhoThePlayerTalkingTo("Cold")
        #ide a default_npc-et kell beállítani
        self.chatbot.set_template(default_npc)
        character = self.repository.getCharacterWithWhomThePlayerisInteracting()
        #print("getCharacterWithWhomThePlayerisInteracting: ", character)
        character_infos = "Character name: " + character['Name'] + ". Relation with the player: " + character[
            'Relation'] + ". Character background: " + character['Background']
        self.chatbot.interactingWithACharacter(default_npc, character_infos)
        return "The player speaking with " + character['Name']

    def characterIsATrader(self, characterName):
        character = self.repository.getCharacterShop(characterName)

        if character:
            return characterName + " is a trader."
        else:
            return characterName + " is not a trader."

    def playerWantToFight(self, characterName):
        self.repository.playerWantToFightWithANPC(characterName)

    def setRepository(self, repository):
        self.repository = repository

    def setNPCWhoThePlayerTalkingTo(self, characterName):
        print("characterName: " + characterName)

        if characterName == "None":
            #self.speaking_with_a_character()
            character = self.repository.getCharacterWithWhomThePlayerisInteracting()
            #return "The player is want to speak with " + character["Name"]

            return "No other tool needed."
        else:
            self.repository.setCharacterWithWhomThePlayerisInteracting(characterName)
            #self.speaking_with_a_character()
            #return "The player is want to speak with " + characterName
            return "No other tool needed."



    class CustomPromptTemplate(BaseChatPromptTemplate):
        # The template to use
        template: str
        # The list of tools available
        tools: List[Tool]

        def format_messages(self, **kwargs) -> str:
            # Get the intermediate steps (AgentAction, Observation tuples)

            # Format them in a particular way
            intermediate_steps = kwargs.pop("intermediate_steps")
            thoughts = ""
            for action, observation in intermediate_steps:
                thoughts += action.log
                thoughts += f"\nObservation: {observation}\nThought: "

            # Set the agent_scratchpad variable to that value
            kwargs["agent_scratchpad"] = thoughts

            # Create a tools variable from the list of tools provided
            kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

            # Create a list of tool names for the tools provided
            kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
            formatted = self.template.format(**kwargs)
            return [HumanMessage(content=formatted)]

    class CustomOutputParser(AgentOutputParser):
        def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:

            # Check if agent should finish
            if "Final Answer:" in llm_output:
                print({"output": llm_output.split("Final Answer:")[-1].strip()}),
                # ide kell rakni, ha JSON-t akarok visszaadni
                return AgentFinish(
                    # Return values is generally always a dictionary with a single `output` key
                    # It is not recommended to try anything else at the moment :)

                    return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                    log=llm_output,
                )

            # Parse out the action and action input
            regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
            match = re.search(regex, llm_output, re.DOTALL)

            # If it can't parse the output it raises an error
            # You can add your own logic here to handle errors in a different way i.e. pass to a human, give a canned response
            if not match:
                raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            action = match.group(1).strip()
            action_input = match.group(2)

            # Return the action and action input
            # return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
            return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
