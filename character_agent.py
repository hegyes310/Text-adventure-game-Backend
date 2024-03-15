from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import BaseChatPromptTemplate
import re
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from typing import List, Union
from langchain_openai import ChatOpenAI
from langchain.chains.llm import LLMChain
from templates import default_message, default_npc


class Character_Agent:
    def __init__(self, repository):
        self.OPENAI_API_KEY = self.open_file('key_openai.txt')
        self.repository = repository
        self.personified_character = repository.getCharacterWithWhomThePlayerisInteracting()
        self.template = """Personify a character in a text-based RPG inspired by the Stalker games who's name is """+ repository.getCharacterNameWithWhomThePlayerisInteracting() + """. Answer the player's input sentence as your personified character, based on your relationship with the player. Utilize the following tools:

            {tools}

            Follow this format:

            Sentence: the given sentence that requires a response
            Consideration: your character's internal contemplation about what to do
            Action: the action to be taken, choose from [{tool_names}]
            Action Input: the input necessary for the action
            Observation: the outcome of the action
            ... (repeat this Consideration/Action/Action Input/Observation sequence as needed, but limit to once per tool)
            Consideration: I have gathered all the information needed
            Final Answer: The conclusive response to the initial sentence as embodied by the character.


            Sentence: {input}
            {agent_scratchpad}"""
        self.template_mentes = """Personify a character in a text-based game based on Stalker games. You have access to the following tools:

            {tools}

            Use the following format:

            Sentence: the input sentence you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times, but only once per tool)
            Thought: I now know the final answer
            Final Answer: The ultimate response to the input as the personified character.


            Sentence: {input}
            {agent_scratchpad}"""

        self.tools = [
            Tool(
                name="Get the personified character's background",
                func=self.get_character_background,
                description="Useful when the personified character's background needed to properly answer the input sentence. No action input needed."
            ),
            Tool(
                name="Get the personified character's relationship to the player",
                func=self.get_character_relation_to_the_player,
                description="Useful to determite the personified character's relationship to the player. No action input needed."
            ),
            Tool(
                name="Change the personified character's relationship to the player",
                func=self.set_character_relation_to_the_player,
                description="Useful to change the relationship character's relation to the player based on on the player's input. The input is the new relationship to the player."
            ),
            Tool(
                name="Get the personified character's missions which can be given to the player",
                func=self.get_character_missions,
                #description="Useful when the personified character's missions needed to properly answer the input sentence. No action input needed."
                description="Useful when the input text is asking about the personified character's missions which can be given to the player. No action input needed."
            ),
            Tool(
                name="Get the personified character's shop",
                func=self.get_character_shop,
                #description="Useful to determite the personified character is a trader. No action input needed."
                description="Useful to determite the personified character is a trader if the input text is about buying something. No action input needed."
            ),
            Tool(
                name="Get the personified character's location",
                func=self.get_character_location,
                description="Useful when the personified character's location needed to properly answer the input sentence. No action input needed."
            ),
            Tool(
                name="Get the personified character's memories",
                func=self.get_character_memories,
                description="Useful to get the personified character's memories. No action input needed."
            ),
            Tool(
                name="Player accept the personified character's mission",
                func=self.player_accept_a_mission,
                description="Useful when the player's accepted a mission. No action input needed."
            ),
            Tool(
                name="Add memories to the personified character's memories",
                func=self.set_character_memory,
                description="Always use it to save a shortened version of the conversation or what happend between the personified character and the player. The input is the memory or memories."
            ),

            Tool(
                name="Player's mission condition",
                func=self.get_player_mission,
                description="Always use this tool to get the player's mission. No action input needed."
            ),
            Tool(
                name="Player is finished the mission",
                func=self.player_is_finished_the_mission,
                description="Useful if the player is finished the mission. No action input needed."
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

    def get_character_background(self, none):
        return "The personified character background: " + self.personified_character['Background']

    def get_character_relation_to_the_player(self, none):
        return "The personified character relation to the player: " + self.personified_character['Relation']

    def set_character_relation_to_the_player(self, relation):
        self.repository.changeCharaterRelationToThePlayer(relation)

    def get_character_missions(self, none):
        character_missions = self.personified_character['Missions']
        #print("character_missions: " + character_missions)
        if len(character_missions) > 0:
            missions_str = ", ".join(character_missions)
            print("missions: " + missions_str)
            return "The personified character missions: " + missions_str
        else:
            return "The personified character don't have missions."

    def get_character_shop(self, none):
        character_shop = self.personified_character['Shop']
        if len(character_shop) > 0:
            shop_str = ", ".join(character_shop)
            return "The personified character shop: " + shop_str
        else:
            return "The personified character don't any equipment to sell."

    def get_character_location(self, none):
        print("self.personified_character: ", self.personified_character)
        print("self.personified_character['Location']: ", self.personified_character['Location'])
        return "The personified character location: " + self.personified_character['Location']

    def get_character_memories(self, none):
        memories = self.personified_character['Memories']
        if len(memories) == 0:
            return "The personified character dont have any memories."
        else:
            memories_str = ", ".join(memories)
            return "The personified character memories: " + memories_str


    def set_character_memory(self, memories):
        self.repository.add_character_memory(memories)

    def get_character_name(self):
        return self.personified_character['Name']

    def get_character_picture(self):
        return self.personified_character['Picture']

    def player_accept_a_mission(self, mission=""):
        character_missions = self.personified_character['Missions']
        print("mission: ", character_missions)
        self.repository.setPlayerMission(character_missions)

    def get_player_mission(self, mission=""):
        character_missions = self.repository.getPlayerMission()
        return character_missions

    def player_is_finished_the_mission(self):
        print("player finisshed the mission")

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
