from pathlib import Path
import json

def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo prompts/system_prompt.md."""
    
    base = Path(__file__).resolve().parent.parent.parent
    with open(base / "prompts" / "system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()
    
    
def _carregar_dados_mock() -> str:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    
    base = Path(__file__).resolve().parent.parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
        
    return json.dumps(dados, ensure_ascii=False, indent=2)