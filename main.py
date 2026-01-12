import asyncio
from pathlib import Path
from pyvis.network import Network

from scanners.phone_scanner import scan_phone_real
from scanners.social_scanner import scan_social_real
from scanners.email_scanner import scan_email_real

class SentinelMain:
    def __init__(self):
        self.net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black", cdn_resources="remote")
        self.net.force_atlas_2based()
        self.nodes = set()

    def add_entity_to_graph(self, label, group, title=""):
        if label not in self.nodes:
            colors = {
                "Email": "#e09336", "Domain": "#4f8bc9", "Telefone": "#56a858",
                "Rede Social": "#d64e4e", "Metadata": "#7f8c8d"
            }
            self.net.add_node(label, label=label, color=colors.get(group, "#97c2fc"), size=30, shape="dot", title=title)
            self.nodes.add(label)

    def add_link_to_graph(self, src, dst, label):
        self.net.add_edge(src, dst, label=label, arrows="to")

    async def run_pipeline(self, target, target_type):
        print(f"\n[*] Iniciando busca para: {target}")
        if target_type == "1":  # EMAIL
            print(f"[*] Escaneando contas vinculadas ao email: {target}...")
            email_hits = await scan_email_real(target)
            self.add_entity_to_graph(target, "Email")
            if not email_hits:
                print("[-] Nenhuma conta encontrada para este email.")
            else:
                for hit in email_hits:
                    site_label = hit.get('site', 'Desconhecido')
                    self.add_entity_to_graph(site_label, "Rede Social")
                    self.add_link_to_graph(target, site_label, "vinculado")
                    print(f"[+] Encontrado: {site_label}")

        elif target_type == "2":  # TELEFONE
            # 1. Metadados da Operadora
            phone_data = await scan_phone_real(target)
            self.add_entity_to_graph(target, "Telefone")
            for info in phone_data:
                meta = f"{info.get('operator')} ({info.get('location')})"
                self.add_entity_to_graph(meta, "Metadata")
                self.add_link_to_graph(target, meta, "operadora")

            # 2. Busca em Redes Sociais
            clean_id = target.replace("+", "").strip()
            print(f"[*] Escaneando redes sociais para o ID: {clean_id}...")
            social_hits = await scan_social_real(clean_id)
            
            if not social_hits:
                print("[-] Nenhuma rede social encontrada com este ID exato.")
            else:
                for hit in social_hits:
                    node_label = f"{hit['platform']}: {hit['profile_name']}"
                    self.add_entity_to_graph(node_label, "Rede Social", title=hit['url'])
                    self.add_link_to_graph(target, node_label, "perfil_identificado")
                    print(f"[+] Sucesso: {node_label}")

        elif target_type == "3":  # REDE SOCIAL
            print(f"[*] Escaneando rede social/handle: {target}...")
            social_hits = await scan_social_real(target)
            self.add_entity_to_graph(target, "Rede Social")
            if not social_hits:
                print("[-] Nenhuma conta/plataforma encontrada para este handle.")
            else:
                for hit in social_hits:
                    node_label = f"{hit['platform']}: {hit['profile_name']}"
                    self.add_entity_to_graph(node_label, "Rede Social", title=hit['url'])
                    self.add_link_to_graph(target, node_label, "perfil_identificado")
                    print(f"[+] Sucesso: {node_label}")

        # Salvar Resultado
        output_path = Path("outputs") / "relatorio_final.html"
        output_path.parent.mkdir(exist_ok=True)
        self.net.save_graph(str(output_path))
        print(f"\n[+] Pronto! Gráfico gerado em: {output_path.absolute()}")

async def main():
    print("=== SENTINEL RED OSINT ===")
    print("1. Email")
    print("2. Telefone")
    print("3. Rede Social")
    choice = input("\nEscolha : ").strip()
    valor = input("Alvo: ")
    scanner = SentinelMain()
    await scanner.run_pipeline(valor, choice)

if __name__ == "__main__":
    asyncio.run(main())