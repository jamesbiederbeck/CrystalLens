<div align="center">

# CrystalLens — Personal Privacy & OSINT Tool

**Take control of your digital footprint before others do.**

CrystalLens helps you discover what information about you is publicly available online, identify privacy risks, and take action to protect yourself. In an age where your social media history can be used against you — whether by stalkers, doxxers, or hostile actors — this tool empowers you to audit your own digital presence and mitigate potential threats.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made with Flask](https://img.shields.io/badge/Made%20with-Flask-000?logo=flask&logoColor=white)](#)
[![LLM: Ollama](https://img.shields.io/badge/LLM-Ollama-0b2a2a.svg)](#)
[![LLM: Gemini](https://img.shields.io/badge/LLM-Gemini-4285F4.svg)](#)

Privacy-first social media analysis — run locally with Ollama or use Gemini. You control your data.

</div>

## 🎯 Project Vision

This project transforms surveillance technology into a tool for personal empowerment. Instead of helping employers and intelligence agencies monitor individuals, CrystalLens helps **you** monitor yourself — before others do.

### What This Tool Does:
- **Discovers leaked PII**: Finds phone numbers, addresses, emails, and other personal information you may have inadvertently shared
- **Identifies compromising content**: Flags posts that could be used as kompromat or to damage your reputation
- **Detects privacy risks**: Highlights patterns of oversharing, location tracking, and other operational security concerns
- **Provides actionable recommendations**: Suggests specific posts to delete or make private

### Why This Matters:
In today's world, your online history can be weaponized against you. Whether you're concerned about:
- Stalkers and harassers finding personal information
- Past posts being taken out of context
- Doxxing and privacy violations
- Employment or social consequences from old content

...CrystalLens gives you the tools to protect yourself proactively.


## ✨ Features
- **Profile Management**: Track multiple social media accounts you want to audit
- **Automated Scraping**: Fetch your public posts from Twitter/Facebook via Apify
- **AI-Powered Analysis**: Uses LLMs (local or cloud) to identify privacy risks
- **Privacy Risk Categories**:
  - Leaked PII (phone numbers, addresses, emails, etc.)
  - Compromising content and kompromat risks
  - Location tracking and patterns
  - Oversharing of personal information
  - Content that could damage your reputation
- **Actionable Reports**: Detailed findings with specific post citations and deletion recommendations
- **Data Control**: Run completely offline with Ollama, or use Gemini for faster analysis
- **Export Options**: PDF and CSV exports for your records



## 🚀 Quickstart (Dev)
1) Create a venv and install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Configure `.env`
```bash
cp .env.example .env
# APIFY_API_TOKEN=... (required for scraping social media)
# OLLAMA_API_URL=http://localhost:11434 (for local privacy)
# OLLAMA_MODEL=llama3.1:8b (or qwen2.5:7b-instruct)
# GOOGLE_API_KEY=... (optional, for faster Gemini analysis)
# ANALYSIS_PROVIDER=ollama|gemini
```
3) Seed an admin account
```bash
python scripts/seed_admin.py
```
4) Run the application
```bash
python run.py
# Open http://127.0.0.1:5000
```

## ⚙️ Configuration
- `DATABASE_URL`: PostgreSQL in production (SQLite for dev is fine)
- `APIFY_API_TOKEN`: Required for scraping social media platforms
- `OLLAMA_API_URL`, `OLLAMA_MODEL`: For local, private LLM analysis
- `GOOGLE_API_KEY`: For faster cloud-based Gemini analysis (optional)
- Set your provider in Settings or via `ANALYSIS_PROVIDER`

## 🤖 Analysis Providers
- **Ollama (local)**: Complete privacy — your data never leaves your machine
  - Run `ollama serve`, then `ollama pull llama3.1:8b` (or `qwen2.5:7b-instruct`)
  - Best for sensitive personal data you don't want to share with any cloud service
- **Gemini (cloud)**: Faster analysis with better JSON formatting
  - Enter `GOOGLE_API_KEY` in Settings; click "Test Gemini"
  - Consider privacy implications of sending data to Google

## 🔒 Privacy & Security
- **Your data stays yours**: Run completely offline with Ollama
- **No telemetry**: We don't track you or send your data anywhere
- **API keys in `.env`**: Never committed to version control
- **Audit logs**: Track all actions for accountability
- **Open source**: Inspect the code and verify what it does

## 🗺️ Roadmap
- Enhanced PII detection (credit cards, SSNs, etc.)
- Pattern analysis for location tracking
- Integration with more social platforms
- Automated content deletion workflows
- Mobile app for on-the-go audits
- More LLM providers (OpenAI, Claude, local models)

## 🤝 Contributing
PRs welcome. Please open issues first for major changes. Keep secrets out of commits.

## ⚠️ Disclaimer
This tool is designed for personal use to audit your own social media accounts and protect your privacy. 
Do not use it to analyze others without their explicit consent. 
Always comply with local laws, regulations, and platform Terms of Service.
Use responsibly and ethically.

## 📄 License
MIT — see `LICENSE`.
