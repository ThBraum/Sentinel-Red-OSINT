import phonenumbers
from phonenumbers import carrier, geocoder


async def scan_phone_real(phone_number: str):
    """
    Analisa metadados do telefone e simula busca em fontes públicas.
    """
    print(f"[*] [PhoneScanner] Analisando: {phone_number}")
    results = []

    try:
        # Garante que o número está no formato internacional (ex: +55...)
        parsed_num = phonenumbers.parse(phone_number)

        if not phonenumbers.is_valid_number(parsed_num):
            return {"error": "Número inválido"}

        # Coleta metadados reais
        operator = carrier.name_for_number(parsed_num, "pt")
        location = geocoder.description_for_number(parsed_num, "pt")

        results.append(
            {
                "id": f"phone_meta_{phone_number}",
                "type": "Metadata",
                "operator": operator,
                "location": location,
                "formatted": phonenumbers.format_number(
                    parsed_num, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ),
            }
        )

    except Exception as e:
        print(f"[-] Erro no PhoneScanner: {e}")

    return results
