# Natalia Vegman — Senior AI Automation Consultant & IT Architect

## Professional Summary

Software engineer by education, IT professional by 19 years of practice. Started her career at Murmansk Shipping Company — one of Russia's largest maritime transport companies — progressing from engineer to Head of the entire IT & Telecommunications Service, managing a department of ~40 people. The team built a proprietary ERP from scratch, implemented SAP, 1C, Company Media, and administered an on-premises data center.

Seven years ago Natalia relocated to Saint Petersburg and pivoted to project-based AI consulting — translating the same systems-thinking discipline she applied to enterprise IT into production-ready AI architectures for modern businesses.

Today she specializes in: multimodal LLM pipelines (RAG, Vision, STT/TTS), enterprise Data Warehouse design, end-to-end business process automation, and AI agent orchestration. She operates as a registered Sole Proprietor with Kazakhstan e-Resident status for smooth international B2B contracting.

A personal interest in genealogy led to the MyFamilyTree side project — a FastAPI backend for importing and querying GEDCOM family-tree archives.

## Core Technical Stack & Tools

* **Languages & Frameworks:** Python (FastAPI, SQLAlchemy 2.0, Alembic, pandas, Flask, PyQt6).
* **Databases & Vector Storage:** PostgreSQL, ChromaDB, FAISS, Docker, Docker Compose.
* **Automation & Web Scraping:** Playwright, Selenium Webdriver (headless with anti-bot bypass), BeautifulSoup.
* **AI & Machine Learning:** OpenAI API (GPT-4o/Vision), Anthropic Claude API, Google Gemini API (2.5 Flash/Pro), Sber GigaChat API, OpenRouter (multi-provider LLM routing with automatic fallback), Hugging Face ecosystem (Transformers, PEFT/LoRA, TRL, BitsAndBytes for 4-bit quantization), Yandex SpeechKit (STT/TTS), fal.ai (Virtual Try-On / image generation).
* **AI Agents & Orchestration:** Hermes (Python agent framework), OpenClaw (Node.js gateway), MCP (Model Context Protocol), multi-agent domain routing, Shared State protocols, n8n (workflow orchestration).
* **Enterprise SaaS & CRM:** Bnovo PMS, Bitrix24, AmoCRM, Russian Federal Service registries (Cerberus / VetIS.API / FGIS Mercury), SAP, 1C, Company Media.
* **Genealogy & Standards:** GEDCOM file format, family-tree graph modeling.

## Selected Professional Experience & Projects

### 1. Fisheries DWH & Analytics Platform ("ships_analytic")
* **Role:** Lead Data Engineer & IT Architect.
* **Context:** Migrated a fragmented Python ETL ecosystem (flat CSVs + Notion) to a centralized relational DWH as data volume caused critical performance degradation. The business required robust cross-references to track fishing quota distributions across vessel time-charter contracts.
* **Implementation:** Designed and deployed a PostgreSQL DWH styled entirely via SQLAlchemy 2.0 declarative mappings and maintained by Alembic migrations. Engineered advanced "Quota Transfer" business logic to dynamically calculate the actual fish-catch owner by cross-referencing vessel charter records. Integrated the UN Comtrade Data API for international market prices by HS code, and automated live vessel port-approach logs by parsing AMP registries. Re-routed Notion to act as a read-only dashboard updated asynchronously via the Notion API. Orchestrated the full pipeline via n8n deployed on a dedicated cloud VPS.
* **GitHub:** https://github.com/natavegman/ships_analytic

### 2. Multimodal AI Assistant & Hospitality Automation ("Nebo AI Assistant")
* **Role:** Backend Developer & IT Architect.
* **Context:** Automated the intake, technical diagnosis, and resolution routing of room repair incidents and guest FAQs across a premium apart-hotel network ("5 Nebo" / "47 Nebo"), significantly reducing staff workload.
* **Implementation:** Built an async ASGI application on FastAPI natively integrated with the Bnovo PMS API. Deployed a hybrid RAG system using ChromaDB + GigaChat, with specialized prompts for "Staff" and "Guest" session modes. Integrated a Computer Vision module (GPT-4o / GigaChat Vision) to extract hardware failure data from guest photos and auto-generate maintenance tickets in the hotel CRM. Embedded Yandex SpeechKit to asynchronously transcribe Telegram voice messages (OGG OPUS) in-memory, avoiding server CPU overhead.
* **Security & DevOps:** Docker Compose containerization, Telegram webhook validation via X-Telegram-Bot-Api-Secret-Token, MAINTENANCE_MODE Feature Flag / Kill Switch, Row-Level Security (RLS) on the database.

### 3. Competitor Monitoring System (Fishing Industry)
* **Role:** Full-Stack AI Engineer.
* **Context:** Built a competitor intelligence application targeting fishing industry companies to map their operational presence, service capabilities, and technical equipment distribution.
* **Implementation:** Developed a native macOS desktop application using PyQt6. Built an automated background crawler using Selenium Webdriver in a hardened headless Chrome instance (User-Agent spoofing, automation flags disabled to bypass bot protections) to scrape competitor pages and interactive maps. Ingested raw page text, embedded PDFs, and layout screenshots into GPT-4o at temperature=0, enforcing JSON response format to prevent hallucination. Outputs structured competitor snapshots with risk assessments, stored in PostgreSQL. Packaged via PyInstaller into a standalone .app bundle.

### 4. R&D: Local LLM Style Fine-Tuning (LoRA / PEFT)
* **Role:** AI Research Engineer.
* **Context:** Proof-of-concept to enable 100% data privacy for hotel VIP guests by running inference locally while custom-tailoring the LLM's Tone of Voice to emulate a luxury 5-star concierge service.
* **Implementation:** Provisioned a Hugging Face training pipeline on a Google Colab T4 GPU. Loaded a Russian foundation model (ai-forever/rugpt3large_based_on_gpt2) with 4-bit quantization (BitsAndBytesConfig). Configured a LoRA adapter (r=8, alpha=16) targeting multi-head attention layers. Trained using trl SFTTrainer + SFTConfig against a curated hotel instruction dataset. Saved the LoRA adapter and validated local inference via PeftModel. Published a post-mortem on underfitting behavior and mitigations.

### 5. Multi-Agent Consulting System (Internal R&D)
* **Role:** AI Systems Architect & Lead Engineer.
* **Context:** Designed and deployed a production-ready multi-agent system to automate AI consulting operations — research, development, design, and strategic analysis.
* **Implementation:** Four-agent hierarchical architecture on Hermes (Python) + OpenClaw (Node.js) with Telegram as the interface. Orchestrator agent receives tasks, identifies the relevant domain from a library of 7 business contexts, and delegates to specialized subagents: researcher, developer, designer. Engineered a domain routing engine and Shared State protocol for structured inter-agent result exchange without direct coupling. Multi-provider LLM routing via OpenRouter with automatic fallback across Claude, Gemini, and GPT. All agents deployed as persistent systemd services with autostart and hot-swap configuration.

### 6. Personal HR Agent — This Portfolio Site
* **Role:** Full-Stack AI Engineer.
* **Context:** Built a bilingual AI-powered portfolio site where visitors can chat with an HR agent persona that answers questions about Natalia's skills, experience, and collaboration terms in EN or RU based on the visitor's browser language.
* **Implementation:** Static frontend (vanilla HTML/CSS/JS) hosted on GitHub Pages with a custom domain (vegman.dev). FastAPI backend on a VPS with FAISS vector search over CV and FAQ documents. Embeddings generated with OpenAI text-embedding-3-small; retrieval filtered by language. nginx reverse proxy + Let's Encrypt (HTTPS). Deployed via a self-contained bash script (systemd + certbot).
* **GitHub:** https://github.com/natavegman/portfolio-site

### 7. Smart Style Bot
* **Role:** Full-Stack AI Engineer.
* **Context:** Telegram AI-stylist that analyzes a user's wardrobe and suggests outfits for any occasion, with a Virtual Try-On feature showing how garments look on the user's photo.
* **Implementation:** Gemini Vision analyzes wardrobe photos and classifies items. Outfit recommendations generated by LLM with context about the occasion. fal.ai (Fashn model) applies Virtual Try-On to show clothes on the user's actual photo. Recommends purchases from Russian marketplaces. PostgreSQL stores wardrobe catalog per user.
* **GitHub:** https://github.com/natavegman/Smart-Style-Bot

### 8. Birthday Photo Album — svetlana70
* **Role:** Frontend Developer & Automation Engineer.
* **Context:** Created an interactive web photo album as a gift for a 70th-birthday celebration — five life chapters (Childhood, Youth, Family, Career, Today) with animated portrait cards, background music, and ~200 photos.
* **Implementation:** Pure vanilla JS, zero frameworks. Python script auto-imported and compressed photos from iCloud, organizing them by chapter. Deployed on GitHub Pages.
* **GitHub:** https://github.com/natavegman/svetlana70-album

### 9. VK Post Generator ("Maya" — AI Biohacking Coach)
* **Role:** Full-Stack Developer & Prompt Engineer.
* **Context:** Flask web app that generates branded VK community posts in the voice of "Maya" — an AI biohacking coach persona with a strict Tone of Voice guideline.
* **Implementation:** GigaChat generates posts strictly matching the ToV brief. BeautifulSoup scrapes reference content from URLs provided by the editor. Editorial favorites saved to database for future reference.
* **GitHub:** https://github.com/natavegman/site-generation-post

### 10. MyFamilyTree
* **Role:** Backend Developer.
* **Context:** Personal genealogy platform — a side project driven by genuine interest in family history research and document digitization.
* **Implementation:** FastAPI backend that imports GEDCOM family-tree files, parses person records and family relationships into a PostgreSQL database via SQLAlchemy, and serves REST endpoints for searching people and attaching archival documents (birth certificates, photos, emigration records) to family records. Docker Compose for local development.
* **GitHub:** https://github.com/natavegman/MyFamilyTree
