# src/async_dns_resolver.py

import asyncio
import aiodns
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
from consts import DNSResolutionStatus

logger = logging.getLogger(__name__)


@dataclass
class DNSAnswer:
    """Wrapper para respostas DNS assíncronas"""
    host: str
    ttl: int
    priority: Optional[int] = None
    
    # Campos específicos por tipo
    address: Optional[str] = None  # A/AAAA
    target: Optional[str] = None  # CNAME/NS/SRV
    exchange: Optional[str] = None  # MX
    preference: Optional[int] = None  # MX
    text: Optional[str] = None  # TXT
    strings: Optional[List[bytes]] = None  # TXT
    
    # SOA fields
    mname: Optional[str] = None
    rname: Optional[str] = None
    serial: Optional[int] = None
    refresh: Optional[int] = None
    retry: Optional[int] = None
    expire: Optional[int] = None
    minimum: Optional[int] = None
    
    # SRV fields
    port: Optional[int] = None
    weight: Optional[int] = None


class AsyncDNSResolver:
    """
    Resolver DNS totalmente assíncrono usando aiodns (c-ares)
    Não bloqueia o event loop
    """
    
    def __init__(
        self, 
        nameservers: List[str],
        timeout: float = 5.0,
        tries: int = 2
    ):
        self.nameservers = nameservers
        self.timeout = timeout
        self.tries = tries
        
        # Cria resolver aiodns
        self.resolver = aiodns.DNSResolver(
            nameservers=nameservers,
            timeout=timeout,
            tries=tries
        )
    
    async def resolve(
        self, 
        qname: str, 
        qtype: str
    ) -> Tuple[Optional[List[DNSAnswer]], DNSResolutionStatus]:
        """
        Resolve query DNS de forma assíncrona
        
        Args:
            qname: Nome do domínio
            qtype: Tipo da query (A, AAAA, MX, etc)
            
        Returns:
            Tuple[Optional[List[DNSAnswer]], DNSResolutionStatus]
        """
        try:
            # Map query type to aiodns method
            resolver_method = self._get_resolver_method(qtype)
            
            if resolver_method is None:
                logger.error(f"Unsupported query type: {qtype}")
                return None, DNSResolutionStatus.INVALID_INPUT
            
            # Execute async query with timeout
            raw_result = await asyncio.wait_for(
                resolver_method(qname),
                timeout=self.timeout * self.tries
            )
            
            # Parse results
            answers = self._parse_result(raw_result, qtype)
            
            if not answers:
                logger.warning(f"No answers for {qname} ({qtype})")
                return None, DNSResolutionStatus.NO_ANSWER
            
            logger.info(f"Resolved {qname} ({qtype}): {len(answers)} answers")
            return answers, DNSResolutionStatus.SUCCESS
            
        except aiodns.error.DNSError as e:
            return self._handle_dns_error(qname, qtype, e)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout resolving {qname} ({qtype})")
            return None, DNSResolutionStatus.TIMEOUT
            
        except Exception as e:
            logger.error(
                f"Unexpected error resolving {qname} ({qtype}): {type(e).__name__} - {e}"
            )
            return None, DNSResolutionStatus.UNKNOWN_ERROR
    
    def _get_resolver_method(self, qtype: str):
        """Retorna o método apropriado do aiodns para o tipo de query"""
        methods = {
            'A': self.resolver.query,
            'AAAA': self.resolver.query,
            'MX': self.resolver.query,
            'CNAME': self.resolver.query,
            'TXT': self.resolver.query,
            'NS': self.resolver.query,
            'SOA': self.resolver.query,
            'SRV': self.resolver.query,
        }
        
        method = methods.get(qtype)
        if method and qtype in ['A', 'AAAA', 'MX', 'CNAME', 'TXT', 'NS', 'SOA', 'SRV']:
            # aiodns.query aceita qtype como argumento
            return lambda host: method(host, qtype)
        
        return None
    
    def _parse_result(self, raw_result, qtype: str) -> List[DNSAnswer]:
        """Converte resultado bruto do aiodns para DNSAnswer"""
        answers = []
        
        # aiodns retorna lista ou objeto único dependendo do tipo
        if not isinstance(raw_result, list):
            raw_result = [raw_result]
        
        for record in raw_result:
            try:
                answer = self._parse_single_record(record, qtype)
                if answer:
                    answers.append(answer)
            except Exception as e:
                logger.error(f"Error parsing record: {e}")
                continue
        
        return answers
    
    def _parse_single_record(self, record, qtype: str) -> Optional[DNSAnswer]:
        """Parse um único record baseado no tipo"""
        
        if qtype == 'A':
            return DNSAnswer(
                host=record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                address=record.host
            )
        
        elif qtype == 'AAAA':
            return DNSAnswer(
                host=record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                address=record.host
            )
        
        elif qtype == 'MX':
            return DNSAnswer(
                host=record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                exchange=record.host,
                preference=record.priority,
                priority=record.priority
            )
        
        elif qtype == 'CNAME':
            return DNSAnswer(
                host=record.cname if hasattr(record, 'cname') else record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                target=record.cname if hasattr(record, 'cname') else record.host
            )
        
        elif qtype == 'TXT':
            # aiodns retorna TXT como lista de strings
            text_data = record.text if hasattr(record, 'text') else str(record)
            return DNSAnswer(
                host='',
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                text=text_data,
                strings=[text_data.encode()] if isinstance(text_data, str) else [text_data]
            )
        
        elif qtype == 'NS':
            return DNSAnswer(
                host=record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                target=record.host
            )
        
        elif qtype == 'SOA':
            return DNSAnswer(
                host='',
                ttl=record.ttl if hasattr(record, 'ttl') else 3600,
                mname=record.nsname,
                rname=record.hostmaster,
                serial=record.serial,
                refresh=record.refresh,
                retry=record.retry,
                expire=record.expire,
                minimum=record.minttl
            )
        
        elif qtype == 'SRV':
            return DNSAnswer(
                host=record.host,
                ttl=record.ttl if hasattr(record, 'ttl') else 300,
                target=record.host,
                port=record.port,
                weight=record.weight,
                priority=record.priority
            )
        
        return None
    
    def _handle_dns_error(
        self, 
        qname: str, 
        qtype: str, 
        error: aiodns.error.DNSError
    ) -> Tuple[None, DNSResolutionStatus]:
        """Mapeia erros do aiodns para DNSResolutionStatus"""
        
        # aiodns error codes (c-ares)
        error_code = error.args[0] if error.args else 0
        
        # ARES_ENOTFOUND (1) ou ARES_ENODATA (4)
        if error_code in [1, 4]:
            logger.warning(f"Domain {qname} not found (NXDOMAIN)")
            return None, DNSResolutionStatus.NXDOMAIN
        
        # ARES_ETIMEOUT (12)
        elif error_code == 12:
            logger.error(f"Timeout resolving {qname}")
            return None, DNSResolutionStatus.TIMEOUT
        
        # ARES_ESERVFAIL (11)
        elif error_code == 11:
            logger.error(f"Server failure for {qname}")
            return None, DNSResolutionStatus.NO_NAMESERVERS
        
        else:
            logger.error(f"DNS error for {qname} ({qtype}): {error}")
            return None, DNSResolutionStatus.DNS_ERROR


# Função de compatibilidade com código antigo
async def resolve_externally(
    qname_str: str,
    rdtype: str,
    external_dns: List[str] = ["8.8.8.8", "1.1.1.1"]
) -> Tuple[Optional[List[DNSAnswer]], DNSResolutionStatus]:
    """
    Wrapper assíncrono compatível com interface antiga
    """
    resolver = AsyncDNSResolver(
        nameservers=external_dns,
        timeout=5.0,
        tries=2
    )
    
    return await resolver.resolve(qname_str, rdtype)
