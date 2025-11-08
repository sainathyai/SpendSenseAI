# SpendSenseAI - Deployment Architecture

## 🏗️ Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet Users                            │
└────────────────────┬─────────────────┬──────────────────────────┘
                     │                 │
          ┌──────────▼─────────┐      │
          │   Route 53 DNS     │      │
          │  sainathyai.com    │      │
          └──────────┬─────────┘      │
                     │                 │
     ┌───────────────┼─────────────────┼────────────────┐
     │               │                 │                 │
     ▼               ▼                 ▼                 ▼
┌─────────┐   ┌──────────┐      ┌──────────┐    ┌──────────────┐
│  user.  │   │operator. │      │   api.   │    │ ACM Certs    │
│spendsense│  │spendsense│      │spendsense│    │  (SSL/TLS)   │
│  ai...  │   │  ai...   │      │  ai...   │    │  Wildcard    │
└────┬────┘   └────┬─────┘      └────┬─────┘    └──────────────┘
     │             │                  │
     │             │                  │
     ▼             ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                      AWS Cloud (us-east-1)                       │
│                                                                  │
│  ┌────────────────────────┐      ┌──────────────────────────┐  │
│  │   AWS Amplify          │      │  Elastic Beanstalk       │  │
│  │                        │      │                          │  │
│  │  ┌─────────────────┐  │      │  ┌────────────────────┐  │  │
│  │  │ User Dashboard  │  │      │  │ Classic Load       │  │  │
│  │  │                 │  │      │  │ Balancer (ELB)     │  │  │
│  │  │ • React + Vite  │  │      │  │                    │  │  │
│  │  │ • dist-user/    │  │      │  │ • HTTPS (443)      │  │  │
│  │  │ • Branch:       │  │      │  │ • HTTP (80)        │  │  │
│  │  │   user-deploy   │  │      │  └────────┬───────────┘  │  │
│  │  └─────────────────┘  │      │           │              │  │
│  │                        │      │           ▼              │  │
│  │  ┌─────────────────┐  │      │  ┌────────────────────┐  │  │
│  │  │ Operator Dash   │  │      │  │ EC2 Instance(s)    │  │  │
│  │  │                 │  │      │  │                    │  │  │
│  │  │ • React + Vite  │  │      │  │ • Python 3.11      │  │  │
│  │  │ • dist/         │  │      │  │ • FastAPI + Uvicorn│  │  │
│  │  │ • Branch:       │  │      │  │ • Auto-scaling     │  │  │
│  │  │   operator-deploy│ │      │  │ • Health checks    │  │  │
│  │  └─────────────────┘  │      │  └────────┬───────────┘  │  │
│  │                        │      │           │              │  │
│  │  ┌─────────────────┐  │      │           ▼              │  │
│  │  │ CloudFront CDN  │  │      │  ┌────────────────────┐  │  │
│  │  │                 │  │      │  │ SQLite Database    │  │  │
│  │  │ • Global cache  │  │      │  │                    │  │  │
│  │  │ • HTTPS         │  │      │  │ • /var/app/data/   │  │  │
│  │  │ • Custom domains│  │      │  │ • Auto-seeded      │  │  │
│  │  └─────────────────┘  │      │  │ • 190 customers    │  │  │
│  │                        │      │  │ • 6000+ transactions│ │  │
│  └────────────────────────┘      │  └────────────────────┘  │  │
│                                   │                          │  │
│  ┌────────────────────────┐      │  ┌──────────────────────┐  │
│  │  AWS Secrets Manager   │◄─────┼──│  IAM Roles          │  │
│  │                        │      │  │                      │  │
│  │  • OpenAI API Key      │      │  │  • EB Service Role   │  │
│  │  • openai/sainathyai   │      │  │  • Amplify Role      │  │
│  └────────────────────────┘      │  └──────────────────────┘  │
│                                   │                             │
└───────────────────────────────────────────────────────────────┘
```

---

## 🌐 Domain & DNS Architecture

### Route 53 Configuration

**Hosted Zone:** `sainathyai.com` (Zone ID: `Z0882306KADD7M9CEUFD`)

**DNS Records:**

| Record | Type | Target | Purpose |
|--------|------|--------|---------|
| `user.spendsenseai.sainathyai.com` | CNAME | CloudFront distribution | User Dashboard |
| `operator.spendsenseai.sainathyai.com` | CNAME | CloudFront distribution | Operator Dashboard |
| `api.spendsenseai.sainathyai.com` | A (Alias) | ELB (Classic Load Balancer) | Backend API |

### SSL/TLS Certificates

**Provider:** AWS Certificate Manager (ACM)

**Certificate:** `*.spendsenseai.sainathyai.com` (Wildcard)

**Validation:** DNS (via Route 53 CNAME)

**Applied To:**
- Classic Load Balancer (backend)
- CloudFront distributions (frontend)

---

## 🖥️ Backend Architecture

### AWS Elastic Beanstalk

**Application Name:** `spendsenseai`  
**Environment Name:** `spendsenseai-env`  
**Platform:** Python 3.11 running on 64bit Amazon Linux 2023  
**Region:** us-east-1

### Infrastructure Components

#### Load Balancer
- **Type:** Classic Load Balancer (ELB)
- **Name:** `awseb-e-3-AWSEBLoa-18B00FYRRKVDC`
- **Listeners:**
  - HTTPS (443) → HTTP (8000) to EC2 instances
  - HTTP (80) → HTTP (8000) to EC2 instances
- **SSL Certificate:** ACM wildcard cert
- **Health Check:** `/health` endpoint
- **Security Group:** 
  - Inbound: 443 (HTTPS), 80 (HTTP) from 0.0.0.0/0
  - Outbound: All traffic

#### EC2 Instances
- **Instance Type:** t3.small
- **OS:** Amazon Linux 2023
- **Python:** 3.11
- **Application:** FastAPI with Uvicorn ASGI server
- **Auto-scaling:** Configured (min: 1, max: 4)
- **Deployment:** Rolling updates

#### Application Structure
```
/var/app/current/
├── application.py          # EB entry point
├── ui/
│   └── api.py             # FastAPI app
├── ingest/                # Data loading
├── features/              # Feature engineering
├── personas/              # Persona assignment
├── recommend/             # Recommendation engine
├── guardrails/            # Consent & eligibility
├── eval/                  # A/B testing & cost tracking
└── data/
    ├── processed/         # CSV data files
    │   ├── accounts.csv
    │   ├── transactions.csv
    │   └── liabilities.csv
    └── spendsense.db      # SQLite database (/var/app/data/)
```

### Environment Variables

```bash
SPENDSENSE_DB_PATH=/var/app/data/spendsense.db
ENABLE_LLM=true
USE_AWS_SECRETS=true
AWS_REGION=us-east-1
```

### Deployment Process

**Command:** `eb deploy spendsenseai-env`

**Process:**
1. Create application version archive (ZIP)
2. Upload to S3
3. Deploy to Elastic Beanstalk environment
4. Run `.platform/hooks/` scripts
5. Restart application server
6. Health check validation

**Files Included:**
- All Python source code
- `requirements.txt` (dependencies)
- `Procfile` (start command)
- `.ebignore` (exclusion rules)
- `data/processed/*.csv` (seed data)

**Files Excluded** (via `.ebignore`):
- `frontend/` directory
- `data/raw/`
- `data/spendsense.db` (local dev DB)
- `node_modules/`
- Documentation files

### Database Architecture

**Type:** SQLite  
**Location:** `/var/app/data/spendsense.db`  
**Size:** ~50MB  
**Auto-seeding:** Yes (on first startup if empty)

**Tables:**
- `accounts` (190 records)
- `transactions` (6000+ records)
- `credit_card_liabilities` (185 records)
- `decision_traces` (audit logs)
- `consent` (consent tracking)
- `experiments` (A/B testing)
- `cost_tracking` (LLM usage)

**Startup Process:**
1. Check if database exists
2. Create tables if missing
3. If empty, seed from CSV files in `data/processed/`
4. Verify data integrity

---

## 🎨 Frontend Architecture

### AWS Amplify

**Region:** us-east-1

### User Dashboard

**App Name:** `spendsenseai-user`  
**App ID:** `d2yncedb4tyu2y`  
**Branch:** `user-deploy`  
**Domain:** `user.spendsenseai.sainathyai.com`

**Build Configuration:**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build:user
  artifacts:
    baseDirectory: frontend/dist-user
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

**Environment Variables:**
```
VITE_API_BASE_URL=https://api.spendsenseai.sainathyai.com
```

**Build Command:** `npm run build:user`  
**Output Directory:** `dist-user/`  
**Entry Point:** `index-user.html` → `index.html`

### Operator Dashboard

**App Name:** `spendsenseai-operator`  
**App ID:** `dvukd3zjye01u`  
**Branch:** `operator-deploy`  
**Domain:** `operator.spendsenseai.sainathyai.com`

**Build Configuration:**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build:operator
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

**Environment Variables:**
```
VITE_API_BASE_URL=https://api.spendsenseai.sainathyai.com
```

**Build Command:** `npm run build:operator`  
**Output Directory:** `dist/`  
**Entry Point:** `index.html`

### CloudFront Distribution

**Features:**
- Global edge caching
- HTTPS enforcement
- Custom domain support
- SPA routing support (404 → index.html)

**Rewrite Rules:**
```json
[
  {
    "source": "/<*>",
    "target": "/index.html",
    "status": "404-200"
  }
]
```

### Deployment Process

**Trigger:** Git push to `operator-deploy` or `user-deploy` branch

**Process:**
1. Webhook triggers Amplify build
2. Clone repository
3. Install dependencies (`npm ci`)
4. Run build command
5. Deploy to S3
6. Invalidate CloudFront cache
7. Update domain routing

**Build Duration:** ~3-5 minutes

---

## 🔐 Security Architecture

### Authentication & Authorization

**Current:** Open access (demo mode)

**Production Recommendations:**
- Implement OAuth 2.0 for user authentication
- JWT tokens for API access
- Role-based access control (RBAC)
- API rate limiting

### Data Security

**In Transit:**
- HTTPS/TLS 1.2+ for all connections
- ACM-managed certificates (auto-renewal)

**At Rest:**
- SQLite database in EC2 ephemeral storage
- For production: Migrate to RDS with encryption

**Secrets Management:**
- AWS Secrets Manager for OpenAI API key
- IAM role-based access (no hardcoded credentials)
- Automatic key rotation support

### Network Security

**Backend:**
- Security groups restrict inbound to 80/443
- No SSH access (use AWS Systems Manager)
- Private subnets for database (if using RDS)

**Frontend:**
- CloudFront restricts access methods
- HTTPS-only delivery
- No direct S3 bucket access

---

## 📊 Monitoring & Logging

### Elastic Beanstalk Monitoring

**CloudWatch Metrics:**
- Request count
- Response time (avg, p99)
- HTTP status codes (2xx, 4xx, 5xx)
- Instance CPU/Memory
- Database connections

**Logs:**
- Application logs: `/var/log/eb-engine.log`
- Web server logs: `/var/log/nginx/`
- Access logs: CloudWatch Logs

**Health Checks:**
- Target: `/health` endpoint
- Interval: 30 seconds
- Timeout: 5 seconds
- Healthy threshold: 3 consecutive successes

### Amplify Monitoring

**Build Logs:**
- Real-time build output
- Error tracking
- Build duration metrics

**Deployment Status:**
- Branch status (live/building/failed)
- Last deployment timestamp
- Build number tracking

---

## 🔄 Deployment Workflows

### Git Branching Strategy

```
main (protected)
├── operator-deploy (auto-deploys to Operator Dashboard)
└── user-deploy (auto-deploys to User Dashboard)
```

### Backend Deployment

```bash
# From any branch (usually main)
git add .
git commit -m "Feature: description"
git push origin main

# Deploy to Elastic Beanstalk
eb deploy spendsenseai-env
```

### Frontend Deployment

**Operator Dashboard:**
```bash
# Merge changes to operator-deploy
git checkout operator-deploy
git merge main
git push origin operator-deploy

# Amplify auto-deploys
```

**User Dashboard:**
```bash
# Merge changes to user-deploy
git checkout user-deploy
git merge main
git push origin user-deploy

# Amplify auto-deploys
```

---

## 💰 Cost Estimates

### AWS Costs (Monthly)

| Service | Resource | Cost |
|---------|----------|------|
| Elastic Beanstalk | EC2 t3.small (1 instance) | ~$15 |
| Classic Load Balancer | ELB | ~$18 |
| Amplify | 2 apps, ~10 builds/month | ~$2 |
| Route 53 | Hosted zone + queries | ~$1 |
| CloudFront | Data transfer (minimal) | ~$1 |
| ACM | SSL certificates | Free |
| **Total** | | **~$37/month** |

### External Costs

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI API | ~190 users, ~1 call/user/week | ~$5-10/month |

**Total Estimated Cost:** ~$42-47/month

---

## 🚀 Scalability Considerations

### Current Capacity

- **Users:** 190 (demo)
- **Concurrent Requests:** ~50-100
- **Response Time:** <2s average
- **Database Size:** 50MB

### Scaling Options

**Horizontal Scaling:**
- Elastic Beanstalk auto-scaling (current: 1-4 instances)
- CloudFront handles CDN scaling automatically

**Vertical Scaling:**
- Upgrade to t3.medium or t3.large if needed
- More memory for larger datasets

**Database Scaling:**
- Migrate to RDS PostgreSQL/MySQL for production
- Read replicas for analytics queries
- Separate OLTP and OLAP workloads

---

## 🔧 Maintenance & Operations

### Routine Tasks

**Daily:**
- Monitor health dashboard
- Check error logs
- Review API metrics

**Weekly:**
- Review cost reports
- Check security patches
- Analyze user patterns

**Monthly:**
- Database backups
- Certificate expiry checks (auto-renewed)
- Performance optimization review

### Disaster Recovery

**Backup Strategy:**
- Database: Export CSV nightly (not yet implemented)
- Code: Git repository (source of truth)
- Infrastructure: Infrastructure as Code (Terraform/CloudFormation)

**Recovery Time Objective (RTO):** 1 hour  
**Recovery Point Objective (RPO):** 24 hours

---

## 📈 Future Enhancements

### Infrastructure
- [ ] Migrate to RDS for database
- [ ] Add Redis for caching
- [ ] Implement WAF for API protection
- [ ] Add CloudWatch alarms
- [ ] Set up automated backups

### Security
- [ ] Implement user authentication (OAuth)
- [ ] Add API key management
- [ ] Enable AWS GuardDuty
- [ ] Implement audit logging
- [ ] Add DDoS protection

### Performance
- [ ] Add Redis caching layer
- [ ] Optimize database queries
- [ ] Implement query result caching
- [ ] Add CDN for static assets
- [ ] Compress API responses

---

## 📞 Support & Troubleshooting

### Common Issues

**Backend Health Red:**
```bash
# Check logs
aws elasticbeanstalk describe-events --application-name spendsenseai --environment-name spendsenseai-env --max-items 20

# Check EC2 instance logs
eb ssh
tail -f /var/log/eb-engine.log
```

**Frontend Not Building:**
```bash
# Check Amplify build logs in console
aws amplify list-apps --region us-east-1

# Trigger manual rebuild
aws amplify start-job --app-id <app-id> --branch-name <branch> --job-type RELEASE
```

**SSL Certificate Issues:**
```bash
# Check certificate status
aws acm list-certificates --region us-east-1
aws acm describe-certificate --certificate-arn <arn>
```

---

**Architecture designed for reliability, built for scale.**

