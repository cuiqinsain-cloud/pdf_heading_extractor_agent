import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

api_key = os.getenv("LLM_API_KEY")
print(f"API Key: {api_key[:20]}...")

llm = ChatOpenAI(
    model="glm-4.7",
    api_key=api_key,
    base_url="https://aiapi.chaitin.net/v1",
    temperature=0.1,
)

print("测试API调用...")
response = llm.invoke([HumanMessage(content="你好，请回复'测试成功'")])
print(f"响应: {response.content}")
