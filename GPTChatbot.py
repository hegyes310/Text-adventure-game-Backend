from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from templates import default_message

class Chatbot:
    def __init__(self, template):
        self.OPENAI_API_KEY = self.open_file('key_openai.txt')
        self.template = template
        self.prompt = PromptTemplate(template=self.template, input_variables=["playerMessage"])
        self.llm = OpenAI(openai_api_key=self.OPENAI_API_KEY)
        self.llm_chain = LLMChain(prompt=self.prompt, llm=self.llm)
        self.response_strategy = self.get_response
        self.character_info = None
        self.player_message = None
        self.location_info = None

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            return infile.read()

    def get_response(self, characterMessage=""):
        if self.character_info is not None:
            answer = self.llm_chain.run({'playerMessage': characterMessage, 'characterInfo': self.character_info})
            #print("karakterként player_message: " + characterMessage + 'characterInfo: ', self.character_info)
            return answer
        else:
            #answer = self.llm_chain.run(self.player_message, self.location_info)
            answer = self.llm_chain.run({'playerMessage': self.player_message, 'locationInfo': self.location_info})
            return answer

    def get_start_response(self):
        answer = self.llm_chain.run(self.player_message)
        return answer


    def interactingWithACharacter(self, template, character_info):
        #ezt a 2 {}-re akarom megcsinálni, valahogy az agent válaszát is bele kell rakni a stringbe
        self.template = template
        self.character_info = character_info
        self.prompt = PromptTemplate(template=self.template, input_variables=["characterInfo", "playerMessage"])
        self.llm = OpenAI(openai_api_key=self.OPENAI_API_KEY)
        self.llm_chain = LLMChain(prompt=self.prompt, llm=self.llm)
        print("GPTChatbotban template: " + self.template + " character_info: ", self.character_info + " self.player_message: " + self.player_message)


    def set_template(self, template):
        self.template = template

        self.prompt = PromptTemplate(template=self.template, input_variables=["playerMessage"])
        self.llm_chain = LLMChain(prompt=self.prompt, llm=self.llm)

    def set_default(self, locationInfo):
        self.template = default_message
        self.character_info = None
        self.location_info = locationInfo

        self.prompt = PromptTemplate(template=self.template, input_variables=["playerMessage", "locationInfo"])
        self.llm = OpenAI(openai_api_key=self.OPENAI_API_KEY)
        self.llm_chain = LLMChain(prompt=self.prompt, llm=self.llm)

    def set_player_message(self, playerMessage):
        self.player_message = playerMessage
        #print("self.player_message: ", self.player_message)
