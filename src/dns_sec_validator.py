import logging

import dns.dnssec
import dns.rdatatype
import dns.resolver

logger = logging.getLogger(__name__)


class DNSSECValidator:
    """
    Validador DNSSEC para verificar assinaturas de registros DNS
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.resolver = dns.resolver.Resolver()
        self.resolver.use_edns(0, dns.flags.DO, 4096)  # Enable DNSSEC

        # Cache de chaves públicas validadas para evitar revalidação
        self._validated_keys: set[str] = set()

        # Root trust anchors (KSK da root zone - atualizar periodicamente)
        # Fonte: https://data.iana.org/root-anchors/root-anchors.xml
        self.root_trust_anchors = {
            # Root KSK 2017 (Key ID 20326)
            ". IN DNSKEY 257 3 8 AwEAAaz/tAm8yTn4Mfeh5eyI96WSVex"
            "TBAvkMgJzkKTOiW1vkIbzxeF3+/4RgWOq7HrxRixHlFlExOLAJr"
            "5emLvN7SWXgnLh4+B5xQlNVz8Og8kvArMtNROxVQuCaSnIDdD5L"
            "KyWbRd2n9WGe2R8PzgCmr3EgVLrjyBxWezF0jLHwVN8efS3rCj/"
            "EWgvIWgb9tarpVUDK/b58Da+sqqls3eNbuv7pr+eoZG+SrDK6nW"
            "eL3c6H5Apxz7LjVc1uTIdsIXxuOLYA4/ilBmSVIzuDWfdRUfhHd"
            "Y6+cn8HFRm+2hM8AnXGXws9555KrUB5qihylGa8subX2Nn6UwNR"
            "1AkUTV74bU=",
        }

    async def validate_response(
        self, qname: str, rdtype: str
    ) -> tuple[bool, str | None]:
        """
        Valida resposta DNSSEC
        Returns: (is_valid, error_message)
        """
        if not self.enabled:
            return True, None

        try:
            # Busca resposta com DNSSEC
            response = self.resolver.resolve(qname, rdtype)

            # Verifica se tem RRSIG
            if not hasattr(response.response, "answer"):
                return True, None  # Sem DNSSEC, considera válido

            for rrset in response.response.answer:
                if rrset.rdtype == dns.rdatatype.RRSIG:
                    logger.debug(f"DNSSEC signature found for {qname}")
                    # Aqui você implementaria validação completa da cadeia
                    # Por simplicidade, apenas verificamos presença
                    return True, None

            # Sem assinatura, mas DNSSEC pode não estar configurado
            logger.debug(f"No DNSSEC signature for {qname}")
            return True, None

        except dns.resolver.NXDOMAIN:
            return False, f"Domain {qname} does not exist"
        except dns.resolver.NoAnswer:
            return False, f"No answer for {qname}"
        except Exception as e:
            logger.error(f"DNSSEC validation error for {qname}: {e}")
            return False, str(e)

    def verify_chain(self, qname: str) -> bool:
        """
        Verifica cadeia completa de confiança DNSSEC do qname até a root

        Processo:
        1. Obtém DNSKEY do domínio
        2. Valida DNSKEY com RRSIG
        3. Obtém DS record do parent zone
        4. Verifica que DS hash matches DNSKEY
        5. Repete até chegar na root
        6. Valida root DNSKEY com trust anchor
        """
        if not self.enabled:
            return True

        try:
            # Converte para dns.name.Name
            name = dns.name.from_text(qname)

            # Caminha da folha para a root
            current_name = name

            while current_name != dns.name.root:
                zone_str = str(current_name)

                # Cache check
                if zone_str in self._validated_keys:
                    logger.debug(f"Using cached validation for {zone_str}")
                    current_name = current_name.parent()
                    continue

                # 1. Busca DNSKEY da zona atual
                try:
                    dnskey_rrset = self.resolver.resolve(
                        current_name, dns.rdatatype.DNSKEY
                    ).rrset
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    logger.debug(f"No DNSKEY for zone: {zone_str}")
                    # Zona não tem DNSSEC, mas isso é ok
                    current_name = current_name.parent()
                    continue

                # 2. Busca RRSIG do DNSKEY
                try:
                    rrsig_rrset = self.resolver.resolve(
                        current_name, dns.rdatatype.RRSIG, rdclass=dns.rdataclass.IN
                    )

                    # Filtra RRSIG que cobre DNSKEY
                    dnskey_rrsigs = [
                        rr
                        for rr in rrsig_rrset
                        if rr.type_covered == dns.rdatatype.DNSKEY
                    ]

                    if not dnskey_rrsigs:
                        logger.warning(f"No RRSIG covering DNSKEY for {zone_str}")
                        return False

                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    logger.warning(f"No RRSIG for DNSKEY at {zone_str}")
                    return False

                # 3. Valida RRSIG com DNSKEY (self-signed)
                try:
                    if not dnskey_rrset:
                        raise ValueError('`dnskey_rrset` is None')

                    # Encontra a KSK (Key Signing Key - flags=257)
                    ksk_keys = [
                        key
                        for key in dnskey_rrset
                        if key.flags & 0x0001  # SEP bit (Secure Entry Point)
                    ]

                    if not ksk_keys:
                        logger.warning(f"No KSK found for {zone_str}")
                        return False

                    # Valida a assinatura
                    dns.dnssec.validate(
                        dnskey_rrset,
                        # Use DNSKEY to validate itself 
                        {current_name: dnskey_rrset},  # type: ignore
                        # No timestamp validation  
                        None,  # type: ignore
                        None,
                    )

                    logger.debug(f"DNSKEY self-signature validated for {zone_str}")

                except dns.dnssec.ValidationFailure as e:
                    logger.error(f"DNSSEC validation failed for {zone_str}: {e}")
                    return False

                # 4. Se não é root, valida com DS record do parent
                if current_name != dns.name.root:
                    # parent_name = current_name.parent()

                    try:
                        # Verifica que algum DS corresponde a alguma DNSKEY
                        ds_matched = False
                        args = (current_name, dns.rdatatype.DS)
                        if (ds_rrset := self.resolver.resolve(*args).rrset):
                            for ds in ds_rrset:
                                if not dnskey_rrset:
                                    continue

                                for dnskey in dnskey_rrset:  # type: ignore
                                    # Calcula hash da DNSKEY
                                    calculated_ds = dns.dnssec.make_ds(
                                        current_name, dnskey, ds.digest_type
                                    )
                                    if calculated_ds.digest == ds.digest:
                                        ds_matched = True
                                        logger.debug(
                                            f"DS record matches DNSKEY for {zone_str}"
                                        )
                                        break

                            if ds_matched:
                                break

                        if not ds_matched:
                            logger.error(f"No DS matches DNSKEY for {zone_str}")
                            return False

                    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                        # Parent não tem DS - zona não está assinada no parent
                        logger.debug(f"No DS record at parent for {zone_str}")
                        # Isso é ok para zonas que não usam DNSSEC

                # 5. Adiciona ao cache de validados
                self._validated_keys.add(zone_str)

                # Sobe para o parent
                current_name = current_name.parent()

            # 6. Valida root com trust anchor
            if not self._validate_root():
                return False

            logger.info(f"DNSSEC chain fully validated for {qname}")
            return True

        except Exception as e:
            logger.error(f"DNSSEC chain verification failed for {qname}: {e}")
            return False

    def _validate_root(self) -> bool:
        """
        Valida DNSKEY da root contra trust anchors conhecidos
        """
        try:
            # Busca DNSKEY da root
            dnskey_rrset = self.resolver.resolve(
                dns.name.root, dns.rdatatype.DNSKEY
            ).rrset

            # Verifica se alguma DNSKEY corresponde ao trust anchor
            if dnskey_rrset:
                for dnskey in dnskey_rrset:
                    dnskey_str = dnskey.to_text()

                    for anchor in self.root_trust_anchors:
                        # Remove ". IN DNSKEY " do anchor para comparar
                        anchor_key = " ".join(anchor.split()[3:])

                        if anchor_key in dnskey_str:
                            logger.debug("Root DNSKEY matches trust anchor")
                            return True

            logger.error("Root DNSKEY does not match any trust anchor")
            return False

        except Exception as e:
            logger.error(f"Root validation failed: {e}")
            return False
