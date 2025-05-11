from langchain.prompts import PromptTemplate
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os


class CharacterCreator:
    def __init__(self):
        load_dotenv()
        self.llm = ChatOllama(
            model=os.environ.get("CHARACTER_CREATOR_MODEL", "llama3.1:8b-instruct-q8_0"),
            temprature=0.6,
            disable_streaming=True,
        )
        self.chain = self.create_prompt() | self.llm

    def create_prompt(self):
        prompt_template = """<|eot_id|><|start_header_id|>user<|end_header_id|>
        Write a brief character background in the S.T.A.L.K.E.R. universe style for a character named "{name}".

        The description should:
        - Be 1-2 sentences long.
        - Include at least one memorable personal trait, belief, or habit.
        - Fit within a slightly dystopian, post-apocalyptic Eastern European setting.
        - Maintain a grounded tone — avoid fantasy clichés or exaggerated drama.

        Format the result in the third person, as if from a game character description.
        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        return PromptTemplate(
            input_variables=["name"],
            template=prompt_template
        )

    def create_character(self, character_name: str) -> BaseMessage:
        chain_output = self.chain.invoke({
            "name": character_name
        })
        return chain_output
