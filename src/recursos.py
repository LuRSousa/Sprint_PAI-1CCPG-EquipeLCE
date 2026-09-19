from pathlib import Path
import json

def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo prompts/system_prompt.md."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "prompts" / "system_prompts" / "system_prompt_v1.md", "r", encoding="utf-8") as f:
        return f.read()

def _carregar_router_system_prompt() -> str:
    """Carrega o router system prompt do arquivo prompts/router_system_prompt.md."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "prompts" / "router_system_prompts" / "router_system_prompt_v2.md", "r", encoding="utf-8") as f:
        return f.read()
    
    return 
    
    
def _carregar_dados_mock() -> str:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
        
    return json.dumps(dados, ensure_ascii=False, indent=2)