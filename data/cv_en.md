# Natalia Vegman — Senior AI Automation Consultant & IT Architect

## Professional Summary
A Results-driven Systems Analyst and IT Architect with 19 years of hands-on experience in Information Technology, Data Warehouse (DWH) design, and complex project management. Specializing in AI Consulting, production-ready multimodal intelligence systems (RAG, Vision, STT/TTS), Low-Rank Adaptation Fine-Tuning (LoRA), and end-to-end business process orchestration (n8n, Python, API integrations).

Expert at translating high-level business pain points into rigorous technical requirements. Proven track record of architecting secure, resilient pipelines that seamlessly connect legacy SaaS/PMS/CRM platforms, relational databases, and Large Language Models (LLMs). Operating as a registered Sole Proprietor (possessing Kazakhstan e-Resident status for streamlined international B2B contracting and payments).

## Core Technical Stack & Tools
* **Languages & Frameworks:** Python (FastAPI, SQLAlchemy 2.0, Alembic, pandas).
* **Databases & Vector Storage:** PostgreSQL, ChromaDB, FAISS, Docker, Docker Compose.
* **Automation & Web Scraping:** n8n, Playwright, Selenium Webdriver (headless browser automation with anti-bot bypass capabilities).
* **AI & Machine Learning:** OpenAI API (GPT-4o/Vision), Sber GigaChat API, Anthropic Claude, Hugging Face ecosystem (Transformers, PEFT/LoRA, TRL, BitsAndBytes for 4-bit quantization), Yandex SpeechKit (STT for native OGG OPUS streaming).
* **Enterprise SaaS & CRM:** Bnovo PMS, Bitrix24, AmoCRM, Russian Federal Service for Veterinary and Phytosanitary Surveillance registries ("Cerberus", VetIS.API, FGIS "Mercury").

## Selected Professional Experience & Core Projects

### 1. Enterprise Data Warehouse Architecture & Analytics Platform ("Quotas_analytic")
* **Role:** Lead Data Engineer & IT Architect.
* **Context:** Redesigned and migrated a highly distributed data pipeline. The existing system relied on independent Python ETL scripts writing to flat CSVs and Notion databases, which caused critical performance degradation as data scaled. The business required robust relational connections to track fishing quota distributions.
* **Implementation:** Designed and deployed a centralized production Data Warehouse (DWH) leveraging PostgreSQL, styled entirely via SQLAlchemy 2.0 declarative mappings and maintained by Alembic database migrations. Engineered advanced "Quota Transfer" business logic to dynamically calculate the actual fish catch owner by cross-referencing vessel time-charter records. Integrated the UN Comtrade Data API to ingest international market prices by HS codes, and automated live vessel port approach logs by parsing AMP registries. Re-routed Notion to act strictly as a Read-Only frontend dashboard updated asynchronously via the Notion API. Orchestrated the entire workflow via an enterprise n8n engine deployed on an independent cloud VPS.

### 2. Multimodal AI Assistant & Hospitality Automation Pipeline ("Nebo AI Assistant")
* **Role:** Backend Developer & IT Architect.
* **Context:** Automated the intake, technical diagnosis, and resolution routing of room repair incidents and guest FAQs across a premium apart-hotel network ("5 Nebo" and "47 Nebo"), significantly reducing staff workload.
* **Implementation:** Built an asynchronous ASGI application on FastAPI natively integrated with the Bnovo PMS API. Deployed a hybrid RAG system using ChromaDB vector collections and Sber's GigaChat model, utilizing customized prompts for specialized "Staff" and "Guest" session modes. Integrated a Computer Vision module (GPT-4o / GigaChat Vision) to extract hardware failure data from images sent by guests or housekeepers, auto-generating urgent maintenance tickets in the hotel CRM. Embedded Yandex SpeechKit to asynchronously process and transcribe native Telegram voice messages (OGG OPUS encoding) directly in-memory, avoiding high server CPU usage.
* **Security & DevOps:** Containerized the entire backend stack via Docker Compose. Implemented request validation by validating incoming Telegram Webhook headers against a secure `X-Telegram-Bot-Api-Secret-Token`. Implemented an infrastructure-wide Feature Flag / Kill Switch (`MAINTENANCE_MODE`) to toggle a fallback screen during technical windows, and enforced strict database isolation via Row-Level Security (RLS).

### 3. International Multimodal Competitor Intelligence System
* **Role:** Full-Stack AI Engineer.
* **Context:** Built an intelligence-gathering application targeting global maritime satcom integrators (VSAT, LEO: Starlink Maritime, OneWeb) to map field engineering hubs, SLAs, and technical equipment distribution networks (e.g., Elcome, Tototheo, AST).
* **Implementation:** Developed a native desktop application for macOS using PyQt6. Built an automated background crawler using Selenium Webdriver running in a hardened headless Chrome instance (spoofing User-Agents and disabling default automation flags to bypass Cloudflare/bot protections) to scrape competitor partner pages and interactive maps. Ingested raw structural page text, embedded PDF brochures, and layout screenshots directly into OpenAI's GPT-4o model at `temperature=0`, explicitly enforcing a JSON response format (`response_format={"type": "json_object"}`) to prevent hallucination. The pipeline outputs structured intelligence snapshots tracking competitive advantages and regional risks, saved locally in PostgreSQL and outputted as automated snapshots. Maintained and packaged the code via PyInstaller into a clean standalone `.app` bundle.

### 4. R&D Case Study: Local LLM Style Fine-Tuning (Parameter-Efficient Fine-Tuning)
* **Role:** AI Research Engineer.
* **Context:** Created a proof-of-concept pipeline to enable 100% data privacy for high-profile hotel guests by executing model inference locally, while custom-tailoring the LLM's Tone of Voice (ToV) to emulate a luxury 5-star concierge service.
* **Implementation:** Provisioned an isolated Hugging Face training pipeline within a Google Colab T4 GPU instance. Loaded a base open-source Russian foundation model (`ai-forever/rugpt3large_based_on_gpt2`) and compressed its weights using 4-bit quantization via `BitsAndBytesConfig` to minimize VRAM utilization. Configured a LoRA adapter (`LoraConfig`, r=8, alpha=16) targeted directly at the model's multi-head attention layers (`c_attn`). Successfully trained the model using Hugging Face's `trl` library (`SFTTrainer` and `SFTConfig`) against a curated instruction dataset. Saved the resulting LoRA adapter and initialized local hardware inference using `PeftModel` wrappers. Published a technical post-mortem analysis detailing the behavior of baseline text-generation models and the technical mitigations for underfitting.
