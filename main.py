from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import chromadb
import os
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.utilities import SerpAPIWrapper
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, HumanMessage
import re
import flask
from openai import OpenAI

app = Flask(__name__)
CORS(app)


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


def read_files_from_folder(folder_path):
    file_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            with open(os.path.join(folder_path, file_name), 'r') as file:
                content = file.read()
                print(file_name)
                file_data.append({"file_name": file_name, "content": content})

    return file_data


def inicializenpcs():
    npc_path = "npc"
    npc_data = read_files_from_folder(npc_path)
    documents = []
    metadatas = []
    ids = []

    for index, data in enumerate(npc_data):
        documents.append(data['content'])
        metadatas.append({'source': data['file_name'][:-5]})
        ids.append(data['file_name'][:-5])

    stalker_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )


def inicializemap():
    map_path = "map"
    map_data = read_files_from_folder(map_path)
    documents = []
    metadatas = []
    ids = []

    for index, data in enumerate(map_data):
        documents.append(data['content'])
        metadatas.append({'source': data['file_name'][:-5]})
        ids.append(data['file_name'][:-5])

    stalker_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )


def inicializeequipment():
    equipment_path = "equipment"
    equipment_data = read_files_from_folder(equipment_path)
    documents = []
    metadatas = []
    ids = []

    for index, data in enumerate(equipment_data):
        documents.append(data['content'])
        metadatas.append({'source': data['file_name'][:-5]})
        ids.append(data['file_name'][:-5])

    stalker_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )


def inicializemission():
    mission_path = "mission"
    mission_data = read_files_from_folder(mission_path)
    documents = []
    metadatas = []
    ids = []

    for index, data in enumerate(mission_data):
        documents.append(data['content'])
        metadatas.append({'source': data['file_name'][:-5]})
        ids.append(data['file_name'][:-5])

    stalker_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )


def inicializethegame():
    inicializeequipment()
    inicializemission()
    inicializemap()
    inicializenpcs()


def characterIsATrader(character):
    npcFromCollection = stalker_collection.get(character)
    npc = json.loads((npcFromCollection['documents'][0]))
    shopItems = []
    for item in npc["Shop"]:
        itemFromCollection = stalker_collection.get(item)
        itemm = json.loads(itemFromCollection['documents'][0])
        shopItems.append(itemm)

    if len(shopItems) > 0:
        trader = character
        itemsToTrade = shopItems
        return character + " is a trader."
    else:
        return character + " is not a trader."


tools = [
    Tool(
        name="Trading with a character",
        func=characterIsATrader,
        description="Useful when the input text is about to start trade, shop or buying something. The input is the name of the character the with whom the player is talking."
    )
]

template = """Analyze the following sentences as best you can. You have access to the following tools:

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


prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=["input", "intermediate_steps"]
)


class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:

        # Check if agent should finish
        print("llm output: ", llm_output)
        if "Final Answer:" in llm_output:
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
        #return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


@app.route('/chatbot', methods=['POST'])
def chatbot_api():
    data = request.get_json()

    # Extract input data from the request
    messages = data.get('messages', "")
    print("ezt kaptam meg: ", messages)
    answer = agent_executor.run(messages)
    '''
    shopItems = []

    for item in npc["Shop"]:
        itemFromCollection = stalker_collection.get(item)
        itemm = json.loads(itemFromCollection['documents'][0])
        shopItems.append(itemm)

    if "can buy" in answer:
        print("trader")
        return json.dumps(shopItems)
    else:
        return "The character is not a trader."
    '''
    if "can buy" in answer or "who is a trader" or "is a trader" in answer:
        print("trader")
        return json.dumps(itemsToTrade)
    else:
        return "The character is not a trader."
    #return messages


if __name__ == '__main__':
    OPENAI_API_KEY = open_file('key_openai.txt')
    client = chromadb.Client()
    stalker_collection = client.create_collection("stalker_collection")
    inicializethegame()

    output_parser = CustomOutputParser()

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

    # LLM chain consisting of the LLM and a prompt
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # Using tools, the LLM chain and output_parser to make an agent
    tool_names = [tool.name for tool in tools]

    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        # We use "Observation" as our stop sequence so it will stop when it receives Tool output
        # If you change your prompt template you'll need to adjust this as well
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

    trader = ""
    itemsToTrade = []

    app.run(debug=True)  # Run the Flask app