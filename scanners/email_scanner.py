import asyncio
from holehe.core import import_submodules

async def scan_email_real(email: str):
    """
    Realiza busca real de contas vinculadas ao email usando a API moderna do Holehe.
    """
    print(f"[*] [Holehe] Iniciando varredura de contas para: {email}")

    results = []
    
    # Importa os módulos dinamicamente
    modules = import_submodules("holehe.modules")
    
    # Filtramos apenas os módulos que possuem o método 'check'
    tasks = []
    for module in modules:
        # Nas versões novas, cada módulo é uma instância com o método check
        try:
            tasks.append(module.check(email))
        except AttributeError:
            continue

    # Executa as buscas em paralelo
    # return_exceptions=True evita que o programa trave se um site cair
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for response in responses:
        # Ignora erros de rede ou módulos desatualizados
        if isinstance(response, Exception) or response is None:
            continue
            
        # Se 'exists' for True, a conta foi encontrada
        if response.get("exists"):
            results.append({
                "site": response.get("name", "Desconhecido"),
                "category": "Rede Social",
                "risk": "Baixo"
            })

    return results