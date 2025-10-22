### AI Act Risk Assessment Report

- Generated at: 2025-10-22 13:39:28Z
- System: TalentScreen AI
- Identified as AI: True

### 1. Identificazione del sistema di IA
NLP and ML-based system that screens resumes and ranks candidates for interview shortlisting.

- Techniques: NLP, machine learning
- Domain: recruitment
- Use cases: candidate screening, resume parsing, ranking
- Inputs: CV text, structured candidate profiles
- Outputs: scores, ranked list
- Human-in-the-loop: True
- Autonomous decision making: False

### 2. Classificazione del rischio
- Category: HIGH
- Reasoning: Domain and/or use case matches Annex III high-risk areas.

### 3. Valutazione dell'impatto sui diritti fondamentali (FRIA)
- Overall: HIGH
- Non Discrimination: high — Historical bias in hiring data
- Privacy: medium — PII present and processed
- Autonomy: low

### 4. Analisi del ciclo di vita del rischio
- Design: Personal data processed; GDPR alignment and DPIA may be required.
- Training: Dataset representativeness uncertain; potential performance disparity across subgroups.
- Validation: Bias and fairness not evaluated; potential discriminatory outcomes.
- Post-market: Model drift and data shifts may degrade performance over time.

### 5. Adozione di misure di mitigazione
- TECHNICAL: Conduct bias and fairness evaluation: Assess disparate impact across protected attributes; document metrics and remediation. (ref: AI Act Art. 10, ISO/IEC 23894)
- TECHNICAL: Improve dataset representativeness: Augment datasets to cover relevant demographics and contexts; document provenance. (ref: AI Act Art. 10)
- ORGANIZATIONAL: Establish risk management system: Documented, continuous process covering identification, analysis, mitigation, and monitoring. (ref: AI Act Art. 9)
- ORGANIZATIONAL: Maintain technical documentation: Comprehensive documentation of system, datasets, tests, and controls. (ref: AI Act Art. 11)
- ORGANIZATIONAL: Data minimization and DPIA: Conduct DPIA and minimize retention of PII (ref: GDPR Art. 5, AI Act Art. 10)

### 6. Documentazione tecnica
- Provide a Technical Documentation Pack including: system description, architecture, datasets, security measures, risk evaluation, test and validation results. (AI Act Art. 11)

### 7. Sistema di gestione del rischio continuo
- Establish continuous monitoring, anomaly detection, and periodic reviews. Configure alerts for unexpected behaviors. Document retraining and change management.

### 8. Valutazione della conformità (ex-ante)
- Risk management system (Art. 9)
- Data governance and management (Art. 10)
- Technical documentation (Art. 11)
- Record-keeping and logging (Art. 12)
- Transparency to users (Art. 13)
- Human oversight (Art. 14)
- Accuracy, robustness, cybersecurity (Art. 15)
- Quality management system (Art. 17)
- Conformity assessment (ex-ante)
- CE marking and declaration of conformity
- Registration in EU high-risk database

### 9. Registrazione nel database europeo
- Required: Yes

---

References: AI Act (Reg. UE 2024/1689), NIST AI RMF, ISO/IEC 23894.