from __future__ import annotations

from datetime import datetime


def render_dpa_md(*, generated_at: datetime, vendor: dict) -> str:
    """Generate a GDPR Art. 28-compliant DPA template (Danish/English bilingual).

    This is a template with fill-in placeholders. The vendor must review,
    complete, and sign before issuing to customers.
    """
    company = vendor.get("company_name") or "[VIRKSOMHEDSNAVN / COMPANY NAME]"
    cvr = vendor.get("cvr_number") or "[CVR-NUMMER / CVR NUMBER]"
    address = vendor.get("address") or "[ADRESSE / ADDRESS]"
    officer_name = vendor.get("security_officer_name") or "[NAVN / NAME]"
    officer_title = vendor.get("security_officer_title") or "[TITEL / TITLE]"
    scope = vendor.get("pack_scope") or "[BESKRIV YDELSE / DESCRIBE SERVICE]"
    date_str = generated_at.strftime("%d-%m-%Y")

    lines = []

    lines.append("# Databehandleraftale / Data Processing Agreement\n")
    lines.append("> **SKABELON** — Gennemse, udfyld og underskriv inden udstedelse til kunder.\n")
    lines.append("> **TEMPLATE** — Review, complete, and sign before issuing to customers.\n\n")
    lines.append(f"Genereret (UTC): {generated_at.isoformat()}Z  \n")
    lines.append(f"Skabelonversion: 1.0  \n\n")

    lines.append("---\n\n")

    lines.append("## 1. Parter / Parties\n\n")
    lines.append("**Dataansvarlig / Data Controller:**  \n")
    lines.append("[Kundens virksomhedsnavn] / [Customer company name]  \n")
    lines.append("[Kundens adresse] / [Customer address]  \n")
    lines.append("[Kundens CVR-nummer] / [Customer CVR number]  \n\n")
    lines.append("**Databehandler / Data Processor:**  \n")
    lines.append(f"{company}  \n")
    lines.append(f"CVR: {cvr}  \n")
    lines.append(f"{address}  \n\n")

    lines.append("## 2. Formål og genstand / Purpose and subject matter\n\n")
    lines.append(
        "Databehandleren behandler personoplysninger på vegne af den dataansvarlige "
        "i forbindelse med levering af følgende ydelse:\n\n"
    )
    lines.append(f"> {scope}\n\n")
    lines.append(
        "The Processor processes personal data on behalf of the Controller "
        "in connection with the delivery of the above service.\n\n"
    )

    lines.append("## 3. Varighed / Duration\n\n")
    lines.append(
        "Aftalen gælder så længe Databehandleren behandler personoplysninger på vegne af den "
        "Dataansvarlige, og ophører automatisk ved kontraktens ophør eller tidligere skriftlig opsigelse.  \n"
    )
    lines.append(
        "The Agreement remains in force for as long as the Processor processes personal data on behalf "
        "of the Controller, and terminates automatically upon termination of the main contract "
        "or earlier written notice.\n\n"
    )

    lines.append("## 4. Behandlingens karakter / Nature of processing\n\n")
    lines.append("Arten af behandling: [f.eks. lagring, analyse, videregivelse] / ")
    lines.append("Nature of processing: [e.g., storage, analysis, disclosure]  \n")
    lines.append("Typer af personoplysninger: [f.eks. navn, e-mail, IP-adresse] / ")
    lines.append("Types of personal data: [e.g., name, email, IP address]  \n")
    lines.append("Kategorier af registrerede: [f.eks. slutbrugere, medarbejdere] / ")
    lines.append("Categories of data subjects: [e.g., end users, employees]  \n\n")

    lines.append("## 5. Databehandlerens forpligtelser / Processor obligations (GDPR Art. 28)\n\n")
    lines.append("Databehandleren forpligter sig til at:\n\n")
    lines.append(
        "- Behandle personoplysninger udelukkende efter dokumenterede instrukser fra den Dataansvarlige "
        "(GDPR Art. 28(3)(a)).  \n"
    )
    lines.append(
        "- Sikre, at personer med adgang til personoplysningerne har påtaget sig tavshedspligt "
        "(Art. 28(3)(b)).  \n"
    )
    lines.append(
        "- Gennemføre passende tekniske og organisatoriske sikkerhedsforanstaltninger "
        "i overensstemmelse med GDPR Art. 32 (Art. 28(3)(c)).  \n"
    )
    lines.append(
        "- Ikke anvende underdatabehandlere uden forudgående skriftlig godkendelse fra den Dataansvarlige "
        "(Art. 28(2) og Art. 28(3)(d)).  \n"
    )
    lines.append(
        "- Bistå den Dataansvarlige med opfyldelse af den registreredes rettigheder "
        "(Art. 28(3)(e)).  \n"
    )
    lines.append(
        "- Bistå den Dataansvarlige med opfyldelse af forpligtelserne i Art. 32–36 "
        "(sikkerhed, brud, DPIA, forudgående høring) (Art. 28(3)(f)).  \n"
    )
    lines.append(
        "- Slette eller returnere alle personoplysninger ved aftalens ophør (Art. 28(3)(g)).  \n"
    )
    lines.append(
        "- Stille al dokumentation til rådighed, der er nødvendig for at påvise overholdelse, "
        "og bidrage til og muliggøre tilsyn (Art. 28(3)(h)).  \n\n"
    )
    lines.append(
        "The Processor agrees to process personal data solely on documented instructions from the Controller, "
        "ensure confidentiality obligations, implement appropriate security measures (Art. 32), "
        "not engage sub-processors without prior written authorisation, assist with data subject rights, "
        "assist with obligations under Art. 32–36, delete or return all personal data upon termination, "
        "and make available all information necessary to demonstrate compliance.\n\n"
    )

    lines.append("## 6. Underdatabehandlere / Sub-processors\n\n")
    lines.append(
        "Databehandleren anvender på tidspunktet for aftalens indgåelse følgende godkendte underdatabehandlere:  \n\n"
    )
    lines.append("| Underdatabehandler | Land | Behandlingsformål |\n")
    lines.append("|---|---|---|\n")
    lines.append("| [Navn] | [Land] | [Formål] |\n\n")
    lines.append(
        "The Processor uses the following approved sub-processors at the time of agreement:  \n"
        "*(Complete the table above — list all sub-processors including cloud providers, "
        "monitoring tools, analytics, and support tools.)*\n\n"
    )

    lines.append("## 7. Sikkerhedsforanstaltninger / Security measures (GDPR Art. 32)\n\n")
    lines.append(
        "Databehandleren har implementeret mindst følgende tekniske og organisatoriske foranstaltninger:  \n\n"
    )
    lines.append("- Kryptering af personoplysninger under transport (TLS 1.2+) og i hvile (AES-256 eller tilsvarende).  \n")
    lines.append("- Adgangsstyring og mindst privilegium-princippet.  \n")
    lines.append("- Regelmæssig backup og dokumenteret restore-test.  \n")
    lines.append("- Hændelseshåndteringsplan (IR-plan) med definerede eskaleringskanaler.  \n")
    lines.append("- Regelmæssig sårbarhedsscanning og patch-management.  \n")
    lines.append("- Medarbejdertræning i datasikkerhed (mindst årligt).  \n\n")
    lines.append(
        "Security measures include: encryption in transit and at rest, access control, "
        "regular backup and tested restore, incident response plan, vulnerability scanning, "
        "and annual security awareness training.\n\n"
    )

    lines.append("## 8. Overførsler til tredjelande / Transfers to third countries\n\n")
    lines.append(
        "Personoplysninger overføres [ikke til / til følgende] lande uden for EU/EØS:  \n"
        "[Beskriv overførselsgrundlag, f.eks. Standardkontraktbestemmelser (SCC) vedtaget af Europa-Kommissionen]  \n\n"
    )
    lines.append(
        "Personal data [is not transferred to / is transferred to the following] countries outside the EU/EEA:  \n"
        "[Describe transfer mechanism, e.g., Standard Contractual Clauses (SCCs) adopted by the European Commission]\n\n"
    )

    lines.append("## 9. Databredbrud / Personal data breaches\n\n")
    lines.append(
        "Databehandleren underretter uden unødigt ophold og senest inden 24 timer den Dataansvarlige, "
        "hvis Databehandleren konstaterer et brud på persondatasikkerheden.  \n\n"
    )
    lines.append(
        "The Processor shall notify the Controller without undue delay and within 24 hours of becoming "
        "aware of a personal data breach.\n\n"
    )

    lines.append("## 10. Underskrift / Signature\n\n")
    lines.append(f"Dato / Date: {date_str}  \n\n")
    lines.append(f"**Databehandler / Processor:** {company}  \n")
    lines.append(f"Navn / Name: {officer_name}  \n")
    lines.append(f"Titel / Title: {officer_title}  \n")
    lines.append("Underskrift / Signature: ________________________________  \n\n")
    lines.append("**Dataansvarlig / Controller:** [Kundens virksomhedsnavn]  \n")
    lines.append("Navn / Name: ________________________________  \n")
    lines.append("Titel / Title: ________________________________  \n")
    lines.append("Underskrift / Signature: ________________________________  \n\n")

    lines.append("---\n\n")
    lines.append(
        "*Denne skabelon er vejledende og er ikke juridisk rådgivning. "
        "Søg altid juridisk bistand, inden aftalen underskrives og udstedes til kunder. "
        "Datatilsynets vejledning: [datatilsynet.dk](https://www.datatilsynet.dk)*\n\n"
    )
    lines.append(
        "*This template is indicative and does not constitute legal advice. "
        "Always seek legal counsel before signing and issuing to customers. "
        "Danish DPA guidance: [datatilsynet.dk](https://www.datatilsynet.dk)*\n"
    )

    return "".join(lines)
