
import importlib

# Lista de pacotes para verificar
packages = [
    "langchain",
    "langchain_community",
    "faiss",
    "sentence_transformers",
    "sklearn",
    "fastapi",
    "uvicorn",
    "sqlalchemy"
]

print("Verificando pacotes instalados e suas versões:\n")

for pkg in packages:
    try:
        module = importlib.import_module(pkg)
        version = getattr(module, "__version__", "(versão não encontrada)")
        print(f"{pkg}: INSTALADO - versão {version}")
    except ModuleNotFoundError:
        print(f"{pkg}: NÃO INSTALADO")
