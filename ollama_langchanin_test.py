from langchain_ollama import OllamaLLM

llm = OllamaLLM(base_url='http://localhost:11434', model='qwen2.5:1.5b')

output = llm.invoke("Hello, world!")
print(output)