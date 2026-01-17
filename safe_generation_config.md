# Safe Generation Configuration

## Conservative Settings to Avoid Rate Limits

### Current Gemini Flash Free Tier Limits:
- **15 RPM** (requests per minute)
- **1 million TPM** (tokens per minute)
- **1,500 RPD** (requests per day)

### Recommended Safe Settings:

**Option 1: Ultra-Conservative (Free Tier)**
- Workers: 8
- RPM: 10 (well below 15 limit)
- Daily limit: ~14,400 requests
- Speed: ~600 tasks/hour

**Option 2: Moderate (If you have Tier 1)**
- Workers: 32
- RPM: 100 (if you have paid tier)
- Daily limit: higher
- Speed: ~6,000 tasks/hour

**Option 3: Very Safe (Recommended for Free)**
- Workers: 4
- RPM: 8
- Daily limit: ~11,520 requests
- Speed: ~480 tasks/hour
- Least likely to trigger blocks

### Generation Command (Ultra-Conservative):
```bash
taskpedia -o task_hierarchy generate \
  -n 80000 \
  --workers 4 \
  --rpm 8 \
  --save-interval 50
```

### What I'll Monitor:
- Rate limit errors
- 429 responses (too many requests)
- Automatic exponential backoff on errors
- Progress every 500 tasks

### Safety Features Built-In:
✅ Automatic retry with exponential backoff
✅ Rate limiter prevents burst requests
✅ Graceful handling of quota errors
✅ Can stop/resume anytime (progress saved)
