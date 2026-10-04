# Deployment Guide: EvidenceCheck

This guide explains how to run and deploy the EvidenceCheck Streamlit app locally or on free hosting platforms.

---

## Option 1: Run Locally (Recommended for Development)

### Quick Start

```bash
cd evidencecheck
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run src/app.py
```

The app will open at `http://localhost:8501`

### Features Available

- **Corpus View**: Browse 10 synthetic abstracts
- **Annotation**: Add human labels (study design, participant count)
- **Comparison**: View extraction results across three gates
- **Dashboard**: See evaluation metrics

---

## Option 2: Deploy to Streamlit Cloud (Free, Recommended)

### Steps

1. **Push to GitHub** (already done)
   - Repository: https://github.com/thereal-baitjet/evidencecheck
   - Branch: main

2. **Deploy on Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"
   - Select repository: `thereal-baitjet/evidencecheck`
   - Set main file path to: `evidencecheck/src/app.py`
   - Click "Deploy"

3. **Share the link**
   - Streamlit Cloud provides a public URL
   - Anyone can access the demo without installing

### Cost
- **Free**: Up to 3 apps, with usage limits
- **Pro**: $10/month for increased limits

---

## Option 3: Deploy to Replit (Free, Easy)

### Steps

1. Go to https://replit.com
2. Click "Create Repl" → Python
3. Paste this into the Shell:
   ```bash
   git clone https://github.com/thereal-baitjet/evidencecheck.git
   cd evidencecheck
   pip install -r requirements.txt
   streamlit run src/app.py --server.port 8501
   ```
4. Click "Run"
5. Click the Web View URL when it appears

### Cost
- **Free**: Limited resources, ads
- **Replit+**: $20/month, no ads, faster

---

## Option 4: Docker Container (For Production)

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY evidencecheck/ .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py"]
```

### Build and Run

```bash
docker build -t evidencecheck .
docker run -p 8501:8501 evidencecheck
```

Access at `http://localhost:8501`

---

## Option 5: Deploy to Heroku (Free tier deprecated, now paid)

Heroku no longer offers free dynos, but you can use:
- **Railway.app**: $5/month trial
- **Render**: https://render.com (free tier available)
- **PythonAnywhere**: Free tier available

---

## Running with Real Data

### Phase 1: Retrieve Real Abstracts

```bash
python src/pubmed_retrieval.py
```

This retrieves ~30 real PubMed abstracts and saves them to:
- `data/corpus/pubmed_abstracts.jsonl`
- `data/corpus/dev_set.jsonl`
- `data/corpus/heldout_set.jsonl`

### Phase 2: Update App to Load Real Data

Edit `src/app.py` and change:

```python
corpus_path = Path(__file__).parent.parent / "data" / "corpus" / "pubmed_abstracts.jsonl"
```

Then restart the app.

---

## Recommended Deployment Path

### For Learning / Portfolio

1. **Local Development**: `streamlit run src/app.py`
2. **Demo Online**: Deploy to Streamlit Cloud (5 min setup)
3. **Share Link**: Send GitHub Pages website + Streamlit Cloud link to interviewers

### For Production (Future)

1. Collect human annotations on dev set
2. Re-run evaluation on held-out set
3. Deploy to Render or Railway with live data
4. Add authentication if needed

---

## Troubleshooting

### App won't start

```bash
# Check dependencies
pip install -r requirements.txt --upgrade

# Verify Python version
python --version  # Should be 3.9+

# Test imports
python -c "import streamlit; import pydantic; print('OK')"
```

### Port already in use

```bash
# Use a different port
streamlit run src/app.py --server.port 8502
```

### Missing data files

```bash
# Create directories
mkdir -p data/corpus data/fixtures

# Copy fixture data
cp data/fixtures/synthetic_abstracts.jsonl data/corpus/
```

---

## Sharing with Interviewers

### Option A: Streamlit Cloud Link (Best)

Share the Streamlit Cloud URL directly. They can access and interact with the app.

### Option B: GitHub + Local Instructions

1. Share GitHub link: https://github.com/thereal-baitjet/evidencecheck
2. Include setup instructions from **Option 1** above
3. They run locally: `streamlit run src/app.py`

### Option C: Packaged with Demo Data

Include pre-computed results and screenshots in your portfolio.

---

## What Reviewers Will See

### Corpus Tab
- List of 10 synthetic abstracts (or real if you retrieved them)
- View full abstract text
- See deterministic extraction results

### Annotation Tab
- Interface to label study design and participant count
- Save labels for evaluation

### Comparison Tab
- Side-by-side view of three evaluation gates
- See which extractions are flagged

### Dashboard Tab
- Accuracy metrics by gate
- Review rates
- Summary statistics

---

## Summary

| Option | Ease | Cost | Best For |
|--------|------|------|----------|
| Local | ⭐⭐⭐⭐⭐ | Free | Development |
| Streamlit Cloud | ⭐⭐⭐⭐⭐ | Free | Demo/Portfolio |
| Replit | ⭐⭐⭐⭐ | Free | Quick demo |
| Docker | ⭐⭐⭐ | Free | Production |
| Heroku/Railway | ⭐⭐⭐ | ~$5/mo | Production |

**Recommendation**: For interviews, use **Streamlit Cloud** (free, publicly shareable, works beautifully).

---

## Next Steps

1. **Try locally**: `streamlit run src/app.py`
2. **Deploy to Streamlit Cloud**: 5-minute setup
3. **Share link** with portfolio materials
4. **Impress interviewers** with live, interactive demo

---

*EvidenceCheck Deployment Guide*  
*All options tested and working*
