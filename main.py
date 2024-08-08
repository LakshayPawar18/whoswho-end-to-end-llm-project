from langchain_google_genai import GoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _mysql_prompt 
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import FewShotPromptTemplate
from langchain.prompts import SemanticSimilarityExampleSelector
import os
from few_shots import few_shots
from dotenv import load_dotenv

load_dotenv() #----used to load the api key from .env file

#setting up google genai
llm = GoogleGenerativeAI(model="models/text-bison-001", google_api_key="")
# print(llm.invoke("write a poem on lion"))-----to check if the model is successfully deployed 

# defining chain for implementing few_shots
def get_few_shot_db_chain():
    #Connecting to MySQL
    db_user = "root"
    db_password= "root"
    db_host = "localhost"
    db_name= "consumer_affairs"
    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",sample_rows_in_table_info=3)
    
    #Embeddings from Hugging Face
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    
    #defining vector db
    to_vectorize = [" ".join(example.values()) for example in few_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=few_shots)

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore = vectorstore,
        k=1,
        )
    
    #Giving llm a Persona
    _mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
        Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
        Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
        Pay attention to use CURDATE() function to get the current date, if the question involves "today".

        Use the following format:

        Question: Question here
        SQLQuery: SQL Query to run
        SQLResult: Result of the SQLQuery
        Answer: Final answer here"""

    example_prompt= PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult","Answer",],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult:\nAnswer: {Answer}",
        )
    
    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix= _mysql_prompt,
        suffix=PROMPT_SUFFIX,
        input_variables=["input", "table_info", "top_k"], #These variables are used in the prefix and suffix
        )
    new_chain= SQLDatabaseChain.from_llm(llm, db, verbose=True, prompt= few_shot_prompt)
    return new_chain

#This is how you define a main function
if __name__ == "__main__":
    chain = get_few_shot_db_chain()
    print(chain.invoke("what is the designation of I s negi"))

