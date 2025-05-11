from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from dotenv import load_dotenv
import os


class GameState(MessagesState):
    summary: str


class GameMaster:
    def __init__(self, game_name: str, mongo_client: MongoClient, game_master_name: str):
        load_dotenv()
        self.model = ChatOllama(
            model=os.environ.get("GAME_MASTER_MODEL", "llama3.1:8b-instruct-q8_0"),
            temprature=0.6,
            disable_streaming=True,
            num_predict=500
        )
        self.workflow = self._build_workflow()
        self.checkpointer = MongoDBSaver(mongo_client)
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        self.config = {"configurable": {"thread_id": game_name + game_master_name}}

    def _build_workflow(self):
        workflow = StateGraph(GameState)

        def call_game_master(state: GameState):
            summary = state.get("summary", "")
            system_prompt = """"You are the Game Master of a text-based role-playing game set in the S.T.A.L.K.E.R. universe.
                Describe the scene in vivid detail, incorporating sights, sounds, smells, and sensations. Present the characters’ reactions and dialogue in a natural and immersive way, considering their motivations and the player’s reputation. Introduce potential dangers, opportunities, or unexpected events to create tension and suspense.
                Allow the player to freely interact with the world, and respond to their actions in a way that feels natural and impactful. Continue the story based on their input, adjusting the narrative dynamically to create a rich, engaging experience.
                Dont give the player options what to do next and dont act behalf of the player.
                Dont explain everyone's reaction, just the main characters of focus."""

            if summary:
                system_prompt += f"\n\n---\nSummary of events so far:\n{summary}\n---"

            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = self.model.invoke(messages)

            return {"messages": [response]}

        def summarize_conversation(state: GameState):
            current_summary = state.get("summary", "")
            summary_prompt = (
                f"This is a story summary capturing key characters, actions, and tensions so far:\n{current_summary}\n\n"
                "Update the summary with the new developments, keeping it concise but preserving all important details like character interactions, conflicts, warnings, and atmosphere."
                if current_summary else
                "Summarize the conversation as story context, focusing on key characters, their actions, conflicts, warnings, and the general atmosphere. Be concise but preserve critical details."
            )
            messages = state["messages"] + [HumanMessage(content=summary_prompt)]
            response = self.model.invoke(messages)
            delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
            return {"summary": response.content, "messages": delete_messages}

        def should_continue(state: GameState) -> Literal["summarize_conversation", END]:
            return "summarize_conversation" if len(state["messages"]) > 6 else END

        workflow.add_node("game", call_game_master)
        workflow.add_node("summarize_conversation", summarize_conversation)
        workflow.add_edge(START, "game")
        workflow.add_conditional_edges("game", should_continue)
        workflow.add_edge("summarize_conversation", END)

        return workflow

    def start_game(self, location_description) -> str:
        prompt = SystemMessage(
            content=f"""You are the Game Master of a text-based role-playing game set in the S.T.A.L.K.E.R. universe. 

            Begin the game. Describe the world in vivid sensory detail and react to the player naturally. 
            Do not list options or decide for the player.
            The player will provide the location information.
            """
        )
        message = HumanMessage(content=location_description)
        event_stream = self.app.stream({"messages": [prompt, message]}, self.config, stream_mode="updates")
        return self._extract_response(event_stream)

    def continue_game(self, input_message: str) -> str:
        combined_message = HumanMessage(
            content=input_message
        )
        event_stream = self.app.stream({"messages": [combined_message]}, self.config, stream_mode="updates")
        return self._extract_response(event_stream)

    def _extract_response(self, event_stream) -> str:
        final_output = ""
        for update in event_stream:
            if "messages" in update.get("game", {}):
                for m in update["game"]["messages"]:
                    final_output += m.content + "\n\n"
            if "summary" in update.get("summarize_conversation", {}):
                # optional: log or store updated summary
                pass
        return final_output.strip()

    def get_summary(self) -> str:
        state = self.app.get_state(self.config).values
        return state.get("summary", "")


def print_update(update):
    for k, v in update.items():
        for m in v["messages"]:
            m.pretty_print()
        if "summary" in v:
            print(v["summary"])


if __name__ == '__main__':
    proba = GameMaster()
    first_response = proba.start_game("Clear sky base")
    print(f"first_response: {first_response}")
    while True:
        player_input = input("What will u do: ")
        response = proba.continue_game(player_input)
        print("\n" + response)
        print(f"\n get_summary: {proba.get_summary()}")