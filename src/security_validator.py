import logging

from dnslib import QTYPE

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DNSSecurityValidator:
    """
    Implementa validações de segurança para queries DNS.

    Protege contra:
    - Amplification attacks
    - Queries malformadas
    - Domínios inválidos
    """

    MAX_QUERY_SIZE = 512  # Tamanho máximo de query DNS (UDP padrão)
    MAX_LABEL_LENGTH = 63  # RFC 1035
    MAX_DOMAIN_LENGTH = 253  # RFC 1035

    BLOCKED_QTYPES = {
        QTYPE.ANY,  # Bloqueia ANY queries (usado em amplification attacks)
    }

    @staticmethod
    def validate_query_size(data: bytes) -> bool:
        """
        Valida o tamanho da query DNS.

        :param data: Payload da query
        :return: True se tamanho válido
        """

        return len(data) <= DNSSecurityValidator.MAX_QUERY_SIZE

    @staticmethod
    def validate_domain_name(domain: str) -> bool:
        """
        Valida o formato do nome de domínio conforme RFC 1035.

        :param domain: Nome do domínio
        :return: True se válido
        """
        if len(domain) > DNSSecurityValidator.MAX_DOMAIN_LENGTH:
            return False

        labels = domain.rstrip(".").split(".")
        if not labels:
            return False

        for label in labels:
            if not label or len(label) > DNSSecurityValidator.MAX_LABEL_LENGTH:
                return False

            # Verifica caracteres válidos (alfanuméricos e hífen)
            if not all(c.isalnum() or c == "-" for c in label):
                return False

            # Label não pode começar ou terminar com hífen
            if label.startswith("-") or label.endswith("-"):
                return False

        return True

    @staticmethod
    def is_suspicious_qtype(qtype: int) -> bool:
        """
        Verifica se o tipo de query é considerado suspeito.

        :param qtype: Tipo DNS
        :return: True se bloqueado
        """
        return qtype in DNSSecurityValidator.BLOCKED_QTYPES

    @staticmethod
    def validate_query(data: bytes, qname: str, qtype: int) -> tuple[bool, str]:
        """
        Executa validação completa de uma query DNS.

        :return: (is_valid, mensagem_de_erro)
        """
        if not DNSSecurityValidator.validate_query_size(data):
            return False, "Query size exceeds maximum"

        if not DNSSecurityValidator.validate_domain_name(qname):
            return False, "Invalid domain name format"

        if DNSSecurityValidator.is_suspicious_qtype(qtype):
            return False, f"Query type {qtype} is blocked"

        return True, ""
