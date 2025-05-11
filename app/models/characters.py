from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import Literal
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from dotenv import load_dotenv
import os


class GameState(MessagesState):
    summary: str


class Character:
    def __init__(self, character_name: str, background: str, mongo_client: MongoClient, game_name: str):
        load_dotenv()
        self.model = ChatOllama(
            model=os.environ.get("CHARACTER_MODEL", "llama3.2:3b-instruct-q8_0"),
            temprature=0.6,
            disable_streaming=True,
        )
        self.workflow = self._build_workflow()
        self.checkpointer = MongoDBSaver(mongo_client)
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        self.config = {"configurable": {"thread_id": character_name+game_name}}
        self.background = background
        self.character_name = character_name
        self.was_the_quest_given: bool = False
        self.quest_json: dict | None = None

    def _build_workflow(self):
        workflow = StateGraph(GameState)

        def get_character_response(state: GameState):
            summary = state.get("summary", "")

            if self.was_the_quest_given:
                system_prompt = f"""
                You are {self.character_name}, a character in a S.T.A.L.K.E.R.-themed role-playing game.
                Your background: {self.background}
    
                Write a brief memory note (1–2 sentences) describing how you gave the following quest to the PLAYER.
    
                Quest details:
                - Name: {self.quest_json['quest_name']}
                - Objective: {self.quest_json['quest_objective']}
                - Description: {self.quest_json['quest_description']}
    
                Instructions:
                - Use third person and start with your name (e.g., "{self.character_name} instructed the player to...")
                - Refer to the PLAYER explicitly as "the player"
                - Clearly state what task the player must complete based on the Description
                - Do NOT include: dialogue, invented scenes, reflections, emotions, or character actions
                - Do NOT include extra context
                - Only include factual, mission-relevant information
                - This will be stored as a memory for future reference
                """
            else:
                system_prompt = """You are helping a Game Master run a role-playing game set in the S.T.A.L.K.E.R. universe.""" + f" Your character's name: {self.character_name} and your character background: {self.background}." + """You will be provided with your character's name, character's background,game master response and the player's message. 
    
                 Based on those, describe in 20 words or less what {character_name}'s natural reaction would be. This can include:
                - Their emotional or mental response
                - What they might do next
                - Whether they would say something (but don't write full dialogue)
    
                Keep the description short and grounded in the character’s personality and background, and suitable for the Game Master to incorporate into the narrative. Do not invent major plot points — react only to what is described. Always start with your character's name."""

                if summary:
                    system_prompt += f"\n\n---\nSummary of events so far:\n{summary}\n---"

            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            character_response = self.model.invoke(messages)

            self.was_the_quest_given = False
            self.quest_json = None

            return {"messages": [character_response]}

        def summarize_conversation(state: GameState):
            current_summary = state.get("summary", "")

            summary_prompt = (
                f"This is a summary of the conversations with the player so far:\n{current_summary}\n\n"
                "Update the summary based on the new developments above:"
                if current_summary else
                "Summarize the conversation above as story context:"
            )
            messages = state["messages"] + [HumanMessage(content=summary_prompt)]
            summarize_response = self.model.invoke(messages)
            delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][1:-2]]
            return {"summary": summarize_response.content, "messages": delete_messages}

        def should_continue(state: GameState) -> Literal["summarize_conversation", END]:
            return "summarize_conversation" if len(state["messages"]) > 4 else END

        workflow.add_node("game", get_character_response)
        workflow.add_node("summarize_conversation", summarize_conversation)
        workflow.add_edge(START, "game")
        workflow.add_conditional_edges("game", should_continue)
        workflow.add_edge("summarize_conversation", END)

        return workflow

    def generate_character_reaction(self, player_message: str, game_master_message: str):
        formatted_input = f"Player's message: {player_message}, the game master message: {game_master_message}"
        message = HumanMessage(content=formatted_input)
        event_stream = self.app.stream({"messages": [message]}, self.config, stream_mode="updates")
        return self._extract_response(event_stream)

    def generate_quest_description(self, quest_json: dict):
        system_prompt = f"""
        You are {self.character_name}, a character in a S.T.A.L.K.E.R.-themed role-playing game.
        Your background: {self.background}

        Write a brief memory note (1–2 sentences) describing how you are giving the following quest to the PLAYER.

        Quest details:
        - Name: {quest_json['quest_name']}
        - Objective: {quest_json['quest_objective']}
        - Description: {quest_json['quest_description']}

        Instructions:
        - Use third person and start with your name (e.g., "{self.character_name} instructed the player to...")
        - Refer to the PLAYER explicitly as "the player"
        - Clearly state what task the player must complete based on the Description
        - Do NOT include: extra context, dialogue, invented scenes, reflections, emotions, or character actions
        - Only include factual, mission-relevant information
        - This will be stored as a memory for future reference
        """
        generated_quest_memory = self.model.invoke(system_prompt)
        return generated_quest_memory.content

    def generate_character_reaction_with_quest(self, player_message: str, game_master_message: str, quest_json: dict):
        self.was_the_quest_given = True
        self.quest_json = quest_json
        generated_respond = self.generate_quest_description(quest_json=quest_json)

        formatted_input = f"Player's message: {player_message}, the game master message: {game_master_message}. This is the respond you MUST return: {generated_respond}"
        message = HumanMessage(content=formatted_input)

        event_stream = self.app.stream({"messages": [message]}, self.config, stream_mode="updates")
        return self._extract_response(event_stream)

    def _extract_response(self, event_stream):
        final_output = ""
        for update in event_stream:
            if "messages" in update.get("game", {}):
                for m in update["game"]["messages"]:
                    final_output += m.content + "\n\n"
            if "summary" in update.get("summarize_conversation", {}):
                pass

        return final_output.strip()

    def get_summary(self):
        state = self.app.get_state(self.config).values
        return state.get("summary", "")
