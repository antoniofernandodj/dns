# src/models.py

"""
Este módulo define os MODELOS DE REGISTROS DNS utilizados pelo servidor.

Cada classe representa um tipo de Resource Record (RR) do protocolo DNS,
conforme definido principalmente nas RFCs 1034 e 1035, além de extensões
posteriores (MX, SRV, AAAA, etc.).

Esses modelos cumprem três papéis fundamentais:
1. Representar registros DNS de forma orientada a objetos
2. Servir como camada intermediária entre banco de dados e protocolo DNS
3. Converter dados persistidos em Resource Records reais (dnslib.RR)
"""

# from dnslib import (
#     # DNSRecord,
#     # DNSQuestion,
#     # DNSLabel,
# )

from dnslib import (
    AAAA,
    CNAME,
    MX,
    NS,
    QTYPE,
    RR,
    SOA,
    SRV,
    TXT,
    A,
)


class Base:
    """
    Este módulo define os MODELOS DE REGISTROS DNS utilizados pelo servidor.

    Cada classe representa um tipo de Resource Record (RR) do protocolo DNS,
    conforme definido principalmente nas RFCs 1034 e 1035, além de extensões
    posteriores (MX, SRV, AAAA, etc.).

    Esses modelos cumprem três papéis fundamentais:
    1. Representar registros DNS de forma orientada a objetos
    2. Servir como camada intermediária entre banco de dados e protocolo DNS
    3. Converter dados persistidos em Resource Records reais (dnslib.RR)
    """

    # ID interno (normalmente usado para persistência em banco)
    id: int | None

    # Nome do host ao qual o registro pertence (ex: "example.com.")
    host: str

    def set_id(self, new_id: int) -> None:
        """
        Define o ID interno do registro.

        Esse ID NÃO faz parte do protocolo DNS.
        Ele existe apenas para controle interno/persistência.
        """
        self.id = new_id

    def __repr__(self) -> str:
        """
        Representação textual do objeto, útil para debug e logs.

        Mostra todos os atributos do registro, facilitando inspeção
        durante resolução, cache ou persistência.
        """
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


class A_Register(Base):
    """
    Registro DNS tipo A (Address Record).

    FUNÇÃO NO DNS:
    - Mapeia um nome de domínio para um endereço IPv4.
    - É o registro mais básico e mais consultado do DNS.

    EXEMPLO:
    example.com.  IN  A  93.184.216.34

    INTERAÇÃO COM OUTROS REGISTROS:
    - Pode ser o alvo final de um CNAME
    - Pode ser usado como destino de um SRV ou MX
    """

    def __init__(self, _id: int | None, _host: str, _ip: str) -> None:
        self.id = _id
        self.host = _host
        self.ip = _ip

    def to_rr(self, ttl: int) -> RR:
        """
        Constrói um Resource Record (RR) DNS do tipo A a partir do modelo interno.

        CONTEXTO NO PROTOCOLO DNS
        -------------------------
        No DNS, TODA resposta enviada ao cliente é composta por uma ou mais
        estruturas chamadas Resource Records (RRs).

        Um Resource Record é a menor unidade de informação do DNS e contém:
        - O NOME ao qual a informação se refere (ex: example.com.)
        - O TIPO do registro (A, AAAA, MX, etc.)
        - O TTL (Time To Live)
        - O DADO propriamente dito (ex: endereço IP)

        Este método existe porque:
        - O banco de dados armazena registros em um formato próprio (modelo Python)
        - O cliente DNS espera receber dados no formato padrão do protocolo DNS
        - A biblioteca dnslib trabalha exclusivamente com objetos RR

        PAPEL DESTE MÉTODO NO FLUXO DE UMA QUERY
        ---------------------------------------
        1. Um cliente envia uma query:
            "Qual é o endereço IPv4 de example.com?"

        2. O servidor localiza o registro no cache ou banco:
            A_Register(host="example.com.", ip="93.184.216.34")

        3. Antes de responder ao cliente, o servidor PRECISA transformar
        esse modelo interno em um Resource Record DNS válido.

        4. Este método faz exatamente essa conversão.

        EXPLICAÇÃO DE CADA CAMPO DO RR
        ------------------------------
        RR(
            self.host,        → NAME
            QTYPE.A,          → TYPE
            ttl=ttl,          → TTL
            rdata=A(self.ip)  → RDATA
        )

        1. NAME (self.host)
        - É o nome de domínio ao qual o registro se aplica
        - Exemplo: "example.com."
        - O cliente compara esse nome com o nome perguntado na query
        - Também é usado por caches DNS para indexação

        2. TYPE (QTYPE.A)
        - Indica o tipo do registro
        - TYPE A significa: "este registro responde com um endereço IPv4"
        - O cliente só aceitará esse RR se o TYPE for compatível com a query

        3. TTL (Time To Live)
        - Define por quantos segundos este RR pode ser armazenado em cache
        - Afeta:
            • Caches do sistema operacional
            • Resolvers intermediários
            • Navegadores
        - TTL alto → menos queries, mais cache
        - TTL baixo → mais queries, respostas mais dinâmicas

        4. RDATA (A(self.ip))
        - É o dado real da resposta
        - No caso do tipo A, é um endereço IPv4
        - Exemplo: "93.184.216.34"
        - A classe A da dnslib garante que o dado seja codificado
            corretamente conforme o padrão DNS (RFC 1035)

        RESULTADO FINAL
        ---------------
        O objeto RR retornado por este método:
        - É serializável para o formato binário do DNS
        - Pode ser inserido diretamente na seção ANSWER da resposta
        - Pode ser armazenado em cache sem conversões adicionais
        - Será interpretado corretamente por qualquer resolver DNS padrão

        Em resumo:
        Este método é o ponto exato onde um registro armazenado internamente
        se transforma em uma resposta DNS real, válida e interoperável.
        """
        return RR(self.host, QTYPE.A, ttl=ttl, rdata=A(self.ip))

    @classmethod
    def from_rr(cls, rr: RR) -> "A_Register":
        """
        Constrói um modelo interno (A_Register) a partir de um Resource Record DNS.

        VISÃO GERAL
        -----------
        Enquanto o método `to_rr` converte um modelo interno em uma resposta DNS,
        este método faz o caminho oposto:

            DNS (padrão do protocolo) → Modelo interno da aplicação

        Ele existe porque o servidor NÃO vive apenas respondendo queries:
        ele também:
        - Consulta servidores DNS externos (upstream)
        - Recebe respostas já no formato DNS padrão
        - Precisa armazenar essas respostas em cache e banco de dados

        O armazenamento interno NÃO deve depender diretamente do formato
        de baixo nível do protocolo DNS, por isso fazemos essa conversão.

        QUANDO ESTE MÉTODO É USADO NA PRÁTICA
        ------------------------------------
        Este método é chamado principalmente quando:

        1. O servidor recebe uma resposta de um DNS upstream
            (ex: Google DNS, Cloudflare)
        2. A biblioteca dnslib entrega essa resposta como um objeto RR
        3. O servidor decide:
            "Este dado é válido, então vou cachear e persistir"

        Nesse momento, o dado precisa ser convertido para um formato:
        - Simples
        - Independente do protocolo
        - Fácil de persistir em banco
        - Fácil de validar e versionar

        É exatamente isso que o A_Register representa.

        O QUE É UM RR (RESOURCE RECORD)
        -------------------------------
        Um RR é uma estrutura completa do protocolo DNS contendo:
        - rname  → nome do domínio consultado
        - rtype  → tipo do registro (A, AAAA, MX, etc.)
        - ttl    → tempo de vida do cache
        - rdata  → dado específico do tipo (aqui: IPv4)

        Este método extrai APENAS o que é relevante para um registro A.

        EXPLICAÇÃO CAMPO A CAMPO
        ------------------------

        1. rr.rname
        - É o nome de domínio ao qual o registro se aplica
        - Exemplo: "example.com."
        - Pode vir como um objeto DNSLabel
        - Aqui é convertido para string para:
            • Armazenamento em banco
            • Comparações simples
            • Uso como chave de cache

        Observação:
        rr.rname pode ser None em casos atípicos ou malformados,
        por isso existe a verificação condicional.

        2. rr.rdata
        - Contém o dado específico do tipo A
        - No caso do tipo A, representa um endereço IPv4
        - Exemplo interno: A("93.184.216.34")
        - str(rr.rdata) extrai o IP em formato texto

        3. _id=None
        - O ID ainda não existe porque:
            • O registro ainda não foi persistido
            • O banco de dados é quem irá gerar o ID
        - Após salvar, o repositório pode atualizar esse ID

        RESULTADO FINAL
        ---------------
        O método retorna uma instância de A_Register que:
        - Representa semanticamente um registro A
        - Está desacoplada do protocolo DNS
        - Pode ser validada (`validate`)
        - Pode ser armazenada em cache e banco
        - Pode ser posteriormente reconvertida em RR (`to_rr`)

        CICLO COMPLETO DE VIDA DO DADO
        ------------------------------
        1. Cliente pergunta: "Qual o IP de example.com?"
        2. Servidor consulta upstream
        3. Upstream responde com um RR do tipo A
        4. from_rr converte RR → A_Register
        5. Registro é armazenado (cache / DB)
        6. Em consultas futuras:
            A_Register → to_rr → resposta ao cliente

        Em resumo:
        Este método é o elo que permite ao servidor "aprender" com
        respostas externas e reutilizá-las como se fossem dados locais.
        """
        return cls(_id=None, _host=str(rr.rname) if rr.rname else "", _ip=str(rr.rdata))

    def validate(self) -> tuple[bool, str]:
        """
        Valida semanticamente o registro A.

        No DNS, registros inválidos podem:
        - Causar falhas de resolução
        - Quebrar caches
        - Gerar respostas incorretas ou inseguras
        """
        if not self.host:
            return False, "Host cannot be empty"
        if not self.ip:
            return False, "IP cannot be empty"

        # Validação simples de IPv4 (não depende de libs externas)
        parts = self.ip.split(".")
        if len(parts) != 4:
            return False, "Invalid IPv4 format"

        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                return False, "Invalid IPv4 octets"
        except ValueError:
            return False, "Invalid IPv4 format"

        return True, ""


class AAAA_Register(Base):
    """
    Registro DNS tipo AAAA.

    FUNÇÃO NO DNS:
    - Equivalente ao A, porém para endereços IPv6.
    - Permite que o DNS funcione plenamente em redes IPv6.

    INTERAÇÃO:
    - Normalmente consultado em conjunto com A (dual-stack)
    - Pode coexistir com A para o mesmo host
    """

    def __init__(self, _id: int | None, _host: str, _ip: str) -> None:
        self.id = _id
        self.host = _host
        self.ip = _ip

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(self.host, QTYPE.AAAA, ttl=ttl, rdata=AAAA(self.ip))

    @classmethod
    def from_rr(cls, rr: RR) -> "AAAA_Register":
        """Cria instância a partir de Resource Record"""
        return cls(_id=None, _host=str(rr.rname) if rr.rname else "", _ip=str(rr.rdata))

    def validate(self) -> tuple[bool, str]:
        # Validação básica: IPv6 sempre contém ':'
        if not self.host:
            return False, "Host cannot be empty"
        if not self.ip:
            return False, "IP cannot be empty"

        # Validação básica de IPv6 (aceita formato comprimido)
        if ":" not in self.ip:
            return False, "Invalid IPv6 format"

        return True, ""


class MX_Register(Base):
    """
    Registro DNS tipo MX (Mail Exchange).

    FUNÇÃO NO DNS:
    - Define quais servidores recebem e-mails para um domínio.
    - Utilizado por servidores SMTP durante entrega de mensagens.

    EXEMPLO:
    example.com. IN MX 10 mail1.example.com.
    example.com. IN MX 20 mail2.example.com.

    INTERAÇÃO:
    - Aponta para hosts que geralmente possuem registros A/AAAA
    - O campo preference define prioridade (menor = mais preferido)
    """

    def __init__(
        self, _id: int | None, _host: str, _exchange: str, _preference: int
    ) -> None:
        self.id = _id
        self.host = _host
        self.exchange = _exchange
        self.preference = _preference

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(
            self.host,
            QTYPE.MX,
            ttl=ttl,
            rdata=MX(label=self.exchange, preference=self.preference),
        )

    @classmethod
    def from_rr(cls, rr: RR) -> "MX_Register":
        """Cria instância a partir de Resource Record"""
        return cls(
            _id=None,
            _host=str(rr.rname) if rr.rname else "",
            _exchange=str(rr.rdata.label),  # type: ignore
            _preference=int(rr.rdata.preference),  # type: ignore
        )

    def validate(self) -> tuple[bool, str]:
        """Valida os dados do registro"""
        if not self.host:
            return False, "Host cannot be empty"
        if not self.exchange:
            return False, "Exchange cannot be empty"
        if self.preference < 0 or self.preference > 65535:
            return False, "Preference must be between 0 and 65535"

        return True, ""


class CNAME_Register(Base):
    """
    Registro DNS tipo CNAME (Canonical Name).

    FUNÇÃO NO DNS:
    - Cria um alias de um nome para outro nome canônico.
    - NÃO aponta diretamente para IPs.

    EXEMPLO:
    www.example.com. IN CNAME example.com.

    REGRAS IMPORTANTES:
    - Um CNAME NÃO pode coexistir com outros registros no mesmo nome
    - A resolução continua até chegar em um registro final (A/AAAA/etc.)
    """

    def __init__(self, _id: int | None, _host: str, _canonical_name: str) -> None:
        self.id = _id
        self.host = _host
        self.canonical_name = _canonical_name

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(self.host, QTYPE.CNAME, ttl=ttl, rdata=CNAME(self.canonical_name))

    @classmethod
    def from_rr(cls, rr: RR) -> "CNAME_Register":
        """Cria instância a partir de Resource Record"""
        return cls(
            _id=None,
            _host=str(rr.rname) if rr.rname else "",
            _canonical_name=str(rr.rdata.label),  # type: ignore
        )

    def validate(self) -> tuple[bool, str]:
        """Valida os dados do registro"""
        if not self.host:
            return False, "Host cannot be empty"
        if not self.canonical_name:
            return False, "Canonical name cannot be empty"

        return True, ""


class TXT_Register(Base):
    """
    Registro DNS tipo TXT (Text Record).

    FUNÇÃO NO DNS:
    - Armazena informações textuais arbitrárias associadas a um domínio.
    - Extremamente flexível e usado por diversos protocolos modernos.

    USOS COMUNS:
    - SPF (Sender Policy Framework)
    - DKIM (DomainKeys Identified Mail)
    - DMARC
    - Verificações de domínio (Google, AWS, etc.)
    - Metadados customizados

    EXEMPLO:
    example.com. IN TXT "v=spf1 include:_spf.google.com ~all"

    INTERAÇÃO:
    - Normalmente consumido por aplicações, não por usuários finais
    - Pode coexistir com praticamente qualquer outro tipo de registro
    """

    def __init__(self, _id: int | None, _host: str, _text: str) -> None:
        self.id = _id
        self.host = _host
        self.text = _text

    def to_rr(self, ttl: int) -> RR:
        """
        Converte o TXT interno em um Resource Record DNS.

        No protocolo DNS, um TXT pode ser dividido em múltiplos segmentos
        de até 255 bytes, mas a biblioteca dnslib abstrai isso.
        """
        return RR(self.host, QTYPE.TXT, ttl=ttl, rdata=TXT(self.text))

    @classmethod
    def from_rr(cls, rr: RR) -> "TXT_Register":
        """
        Constrói o modelo a partir de um RR recebido.

        Importante:
        - TXT pode vir fragmentado em múltiplas partes
        - O resolver precisa recompor o texto completo
        """
        # TXT pode ter múltiplas strings
        text_parts: list[str] = []
        for part in rr.rdata.data:  # type: ignore
            if isinstance(part, bytes):
                text_parts.append(part.decode("utf-8"))
            else:
                text_parts.append(str(part))

        text = "".join(text_parts)

        return cls(_id=None, _host=str(rr.rname) if rr.rname else "", _text=text)

    def validate(self) -> tuple[bool, str]:
        """
        Validação semântica do registro TXT.

        Embora o DNS permita textos arbitrários, limites práticos
        são aplicados para evitar abuso e consumo excessivo de memória.
        """
        if not self.host:
            return False, "Host cannot be empty"
        if not self.text:
            return False, "Text cannot be empty"
        if len(self.text) > 65535:  # Limite prático para TXT
            return False, "Text too long (max 65535 chars)"

        return True, ""


class NS_Register(Base):
    """
    Registro DNS tipo NS (Name Server).

    FUNÇÃO NO DNS:
    - Define quais servidores são autoritativos para uma zona.
    - É a base do mecanismo de delegação do DNS.

    EXEMPLO:
    example.com. IN NS ns1.example.com.
    example.com. IN NS ns2.example.com.

    INTERAÇÃO:
    - Trabalha em conjunto com SOA
    - Normalmente acompanhado de registros A/AAAA (glue records)
    - Usado por resolvers para descobrir quem responde pela zona
    """

    def __init__(self, _id: int | None, _host: str, _nameserver: str) -> None:
        self.id = _id
        self.host = _host
        self.nameserver = _nameserver

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(self.host, QTYPE.NS, ttl=ttl, rdata=NS(self.nameserver))

    @classmethod
    def from_rr(cls, rr: RR) -> "NS_Register":
        """Cria instância a partir de Resource Record"""
        return cls(
            _id=None,
            _host=str(rr.rname) if rr.rname else "",
            _nameserver=str(rr.rdata.label),  # type: ignore
        )

    def validate(self) -> tuple[bool, str]:
        """Valida os dados do registro"""
        if not self.host:
            return False, "Host cannot be empty"
        if not self.nameserver:
            return False, "Nameserver cannot be empty"

        return True, ""


class SOA_Register(Base):
    """
    Registro DNS tipo SOA (Start of Authority).

    FUNÇÃO NO DNS:
    - Marca o início de uma zona DNS autoritativa.
    - Define parâmetros críticos de controle e sincronização da zona.

    EXEMPLO:
    example.com. IN SOA ns1.example.com. admin.example.com. (
        2024010101 ; serial
        3600       ; refresh
        600        ; retry
        1209600    ; expire
        300        ; minimum
    )

    CAMPOS IMPORTANTES:
    - mname: servidor mestre da zona
    - rname: responsável pela zona (email com '.' no lugar de '@')
    - serial: controle de versão da zona
    - refresh/retry/expire: usados em transferências de zona (AXFR)
    - minimum: TTL negativo (NXDOMAIN caching)

    INTERAÇÃO:
    - Trabalha junto com NS
    - Essencial para servidores autoritativos
    """

    def __init__(
        self,
        _id: int | None,
        _host: str,
        _mname: str,
        _rname: str,
        _serial: int,
        _refresh: int,
        _retry: int,
        _expire: int,
        _minimum: int,
    ) -> None:
        self.id = _id
        self.host = _host
        self.mname = _mname
        self.rname = _rname
        self.serial = _serial
        self.refresh = _refresh
        self.retry = _retry
        self.expire = _expire
        self.minimum = _minimum

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(
            self.host,
            QTYPE.SOA,
            ttl=ttl,
            rdata=SOA(
                mname=self.mname,
                rname=self.rname,
                times=(
                    self.serial,
                    self.refresh,
                    self.retry,
                    self.expire,
                    self.minimum,
                ),
            ),
        )

    @classmethod
    def from_rr(cls, rr: RR) -> "SOA_Register":
        """Cria instância a partir de Resource Record"""
        rdata = rr.rdata
        serial, refresh, retry, expire, minimum = rdata.times  # type: ignore

        return cls(
            _id=None,
            _host=str(rr.rname) if rr.rname else "",
            _mname=str(rdata.mname),  # type: ignore
            _rname=str(rdata.rname),  # type: ignore
            _serial=int(serial),
            _refresh=int(refresh),
            _retry=int(retry),
            _expire=int(expire),
            _minimum=int(minimum),
        )

    def validate(self) -> tuple[bool, str]:
        """Valida os dados do registro"""
        if not self.host:
            return False, "Host cannot be empty"
        if not self.mname:
            return False, "Master name server cannot be empty"
        if not self.rname:
            return False, "Responsible person cannot be empty"

        # Validações dos timers
        if self.serial < 0:
            return False, "Serial must be non-negative"
        if self.refresh < 0:
            return False, "Refresh must be non-negative"
        if self.retry < 0:
            return False, "Retry must be non-negative"
        if self.expire < 0:
            return False, "Expire must be non-negative"
        if self.minimum < 0:
            return False, "Minimum must be non-negative"

        return True, ""


class SRV_Register(Base):
    """
    Registro DNS tipo SRV (Service Locator).

    FUNÇÃO NO DNS:
    - Permite localizar serviços específicos dentro de um domínio.
    - Define host, porta e política de balanceamento.

    FORMATO DO NOME:
    _service._proto.example.com.

    EXEMPLO:
    _sip._tcp.example.com. IN SRV 10 60 5060 sipserver.example.com.

    CAMPOS:
    - priority: ordem de preferência (menor = mais prioritário)
    - weight: balanceamento entre registros de mesma prioridade
    - port: porta do serviço
    - target: host que oferece o serviço

    INTERAÇÃO:
    - Usado por clientes, não por browsers
    - Normalmente seguido por lookup A/AAAA do target
    """

    def __init__(
        self,
        _id: int | None,
        _host: str,
        _target: str,
        _port: int,
        _weight: int,
        _priority: int,
    ) -> None:
        self.id = _id
        self.host = _host
        self.target = _target
        self.port = _port
        self.weight = _weight
        self.priority = _priority

    def to_rr(self, ttl: int) -> RR:
        """Converte para Resource Record da dnslib"""
        return RR(
            self.host,
            QTYPE.SRV,
            ttl=ttl,
            rdata=SRV(
                target=self.target,
                port=self.port,
                weight=self.weight,
                priority=self.priority,
            ),
        )

    @classmethod
    def from_rr(cls, rr: RR) -> "SRV_Register":
        """Cria instância a partir de Resource Record"""
        return cls(
            _id=None,
            _host=str(rr.rname) if rr.rname else "",
            _target=str(rr.rdata.target),  # type: ignore
            _port=int(rr.rdata.port),  # type: ignore
            _weight=int(rr.rdata.weight),  # type: ignore
            _priority=int(rr.rdata.priority),  # type: ignore
        )

    def validate(self) -> tuple[bool, str]:
        """Valida os dados do registro"""
        if not self.host:
            return False, "Host cannot be empty"
        if not self.target:
            return False, "Target cannot be empty"

        # Validações dos campos numéricos
        if self.port < 0 or self.port > 65535:
            return False, "Port must be between 0 and 65535"
        if self.weight < 0 or self.weight > 65535:
            return False, "Weight must be between 0 and 65535"
        if self.priority < 0 or self.priority > 65535:
            return False, "Priority must be between 0 and 65535"

        return True, ""
