# n8n AB Testing Workflow

This workflow orchestrates the complete AB testing lifecycle using the 4 agents.

## Setup

### 1. Start the API Server

```bash
cd experimentation-agent
uvicorn src.testing_agent.api.app:app --reload --port 8000
```

The API will start at http://localhost:8000

### 2. Verify API is Running

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status":"healthy","version":"0.1.0","service":"AB Testing Agent API"}
```

### 3. Import Workflow into n8n

1. Open your n8n instance (http://localhost:5678)
2. Click "Add workflow" → "Import from File"
3. Select [ab_test_workflow.json](ab_test_workflow.json)
4. The workflow will be imported with all nodes connected

## Workflow Steps

```
Manual Trigger → Generate Hypothesis → Design Experiment → Analyze Results → Make Decision → Notify
```

### Node Descriptions

1. **Manual Trigger** - Start the workflow with a business goal
2. **Generate Hypothesis** - POST to `/api/v1/hypothesis/generate`
3. **Design Experiment** - POST to `/api/v1/design/create` with the hypothesis
4. **Analyze Results** - POST to `/api/v1/analysis/analyze` with sample data
5. **Make Decision** - POST to `/api/v1/decision/make` based on analysis
6. **Notify Results** - Send results to Slack (optional - configure your Slack credentials)

## Testing the Workflow

### Input Data

When you execute the workflow, provide:

```json
{
  "business_goal": "Increase checkout conversion rate by improving button visibility"
}
```

### Expected Flow

1. **Hypothesis Agent** generates a testable hypothesis
2. **Design Agent** creates experiment design with sample sizes
3. **Analysis Agent** analyzes mock conversion data
4. **Decision Agent** makes ship/no-ship recommendation
5. **Notification** sent with results

## API Endpoints

All endpoints are at `http://localhost:8000/api/v1/`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/hypothesis/generate` | POST | Generate hypothesis |
| `/design/create` | POST | Design experiment |
| `/analysis/analyze` | POST | Analyze results |
| `/decision/make` | POST | Make decision |

## Testing with curl

### Generate Hypothesis

```bash
curl -X POST http://localhost:8000/api/v1/hypothesis/generate \
  -H "Content-Type: application/json" \
  -d '{
    "business_goal": "Increase conversion rate",
    "context": {}
  }'
```

### View API Docs

Interactive API documentation: http://localhost:8000/docs

## Customization

- **Modify sample data**: Edit the "Analyze Results" node to use your actual experiment data
- **Add authentication**: Uncomment API key middleware in app.py
- **Change notification**: Replace Slack node with Email, Discord, or any other notification method

## Troubleshooting

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
python3.11 -m uvicorn ab_testing_agent.api.app:app --port 8001
```

**Import errors:**
```bash
# Reinstall package
pip3 install -e .
```

**CORS errors in n8n:**
- CORS is already configured for `allow_origins=["*"]`
- If issues persist, check n8n is running on localhost

## Next Steps

1. Connect to your actual experiment data source
2. Add data validation and error handling
3. Set up monitoring and logging
4. Deploy API to production server
5. Configure proper authentication
