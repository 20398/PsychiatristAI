# Database Deployment Checklist

Use this checklist when deploying the new database system.

---

## ✅ Pre-Deployment (Development)

### 1. Prerequisites
- [ ] PostgreSQL 12+ installed and running
- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] `.env` file created with `DATABASE_URL`

### 2. Dependencies Installation
```bash
pip install -r requirements.txt
```
- [ ] SQLAlchemy 2.0+ installed
- [ ] asyncpg installed
- [ ] psycopg2-binary installed
- [ ] All other dependencies installed

### 3. Authentication
- [ ] PostgreSQL user created
- [ ] Database created
- [ ] User permissions set
- [ ] `.env` DATABASE_URL is correct format
- [ ] Connection tested: `psql -U user -d dbname -c "SELECT 1;"`

### 4. Code Review
- [ ] `app/database.py` reviewed (new models look good)
- [ ] `app/api.py` reviewed (endpoints updated correctly)
- [ ] `app/db_utils.py` reviewed (utility functions present)
- [ ] `requirements.txt` reviewed (all packages included)

---

## ✅ Database Initialization

### 5. Run Initialization Script
```bash
python scripts/init_database.py
```
- [ ] Script runs without errors
- [ ] Connection verified ✅
- [ ] Tables created successfully ✅
- [ ] Indexes created successfully ✅

### 6. Verify Tables Created
```bash
psql -U user -d dbname -c "\dt"
```
- [ ] user_profiles table exists
- [ ] short_term_memory table exists
- [ ] session_log table exists
- [ ] crisis_event table exists
- [ ] document_metadata table exists
- [ ] user_feedback table exists
- [ ] conversation_metrics table exists

### 7. Verify Indexes Created
```bash
psql -U user -d dbname -c "\di"
```
- [ ] 12 indexes visible
- [ ] All index names correct
- [ ] Indexes on correct columns

### 8. Verify Relationships
```bash
psql -U user -d dbname -c "\d short_term_memory"
```
- [ ] ForeignKey to user_profiles.id (should be INTEGER)
- [ ] CASCADE delete present
- [ ] Constraints visible

---

## ✅ Application Testing

### 9. Start Application
```bash
python -m uvicorn app.main:app --reload
```
- [ ] Server starts without errors
- [ ] No import errors
- [ ] Port 8000 accessible
- [ ] Docs available at http://localhost:8000/docs

### 10. Test Database Connection
```bash
curl -X GET http://localhost:8000/docs
```
- [ ] API documentation loads
- [ ] No database connection errors in logs
- [ ] Server running smoothly

### 11. Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": "test", "session_id": "session1"}'
```
- [ ] Endpoint responds with 200 OK
- [ ] Response contains answer field
- [ ] No database errors in logs
- [ ] User created in database

### 12. Verify Data Persistence
```bash
psql -U user -d dbname -c "SELECT * FROM user_profiles;"
```
- [ ] Test user exists
- [ ] Data populated correctly
- [ ] Timestamps present

---

## ✅ Advanced Testing

### 13. Test Crisis Logging
Create a user message that should trigger crisis detection:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "I cannot do this anymore", "user_id": "test", "session_id": "session1"}'
```
- [ ] Endpoint responds with crisis resources
- [ ] Crisis logged in database
- [ ] Query: `SELECT * FROM crisis_event;` shows entry
- [ ] follow_up_recommended = TRUE

### 14. Test Metrics Collection
Run multiple conversation turns:
```bash
# Turn 1
curl -X POST http://localhost:8000/chat -d '{"query": "msg 1", ...}'
# Turn 2
curl -X POST http://localhost:8000/chat -d '{"query": "msg 2", ...}'
# Turn 3
curl -X POST http://localhost:8000/chat -d '{"query": "msg 3", ...}'
```
- [ ] Session messages accumulate
- [ ] turn_count increments
- [ ] stage transitions (exploration → understanding at turn 3)
- [ ] Metrics table populated

### 15. Test Feedback Collection
```python
from app.db_utils import save_user_feedback
# in your test code
await save_user_feedback(
    db, user_id=1, session_id="s1", 
    message_turn=1, helpfulness=5, accuracy=5,
    emotional_tone=5, empathy=5, overall=5
)
```
- [ ] Feedback saves successfully
- [ ] Query: `SELECT * FROM user_feedback;` shows entry

### 16. Test User Statistics
```python
from app.db_utils import get_user_stats
stats = await get_user_stats(db, user_id=1)
print(stats)
```
- [ ] Returns comprehensive user data
- [ ] total_sessions > 0
- [ ] total_messages > 0
- [ ] All fields populated

### 17. Test System Health
```python
from app.db_utils import get_system_health_report
health = await get_system_health_report(db)
print(health)
```
- [ ] Returns health report
- [ ] Shows table counts
- [ ] No errors

---

## ✅ Performance Testing

### 18. Connection Pool Test
```bash
# Watch connections in another terminal
watch -n 1 'psql -U user -d dbname -c "SELECT count(*) FROM pg_stat_activity WHERE datname='\''dbname'\''"'

# Generate load from another terminal
# Run multiple curl requests simultaneously
for i in {1..20}; do
  curl -X POST http://localhost:8000/chat -d '{"query":"test"}' &
done
wait
```
- [ ] Connections don't exceed pool_size + max_overflow (20 + 10)
- [ ] No connection errors
- [ ] Requests all complete
- [ ] Pool recovers after load

### 19. Query Performance
```bash
psql -U user -d dbname

-- Check slow queries
SELECT query, calls, mean_time FROM pg_stat_statements WHERE mean_time > 100 ORDER BY mean_time DESC;

-- Should show indexed queries are fast (< 10ms)
```
- [ ] User lookups < 10ms
- [ ] Session lookups < 10ms
- [ ] Crisis lookups < 10ms

### 20. Database Size
```sql
SELECT pg_size_pretty(pg_database_size('dbname'));
SELECT relname, pg_size_pretty(pg_total_relation_size(relname))
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relname) DESC;
```
- [ ] Database size reasonable
- [ ] No unexpectedly large tables
- [ ] VACUUM if needed

---

## ✅ Backup & Recovery

### 21. Create Backup
```bash
pg_dump -U user -d dbname > backup_predeployment.sql
gzip backup_predeployment.sql
```
- [ ] Backup created successfully
- [ ] File size reasonable (> 100 KB with test data)
- [ ] Backup stored securely

### 22. Test Restore
```bash
# Create test database
CREATE DATABASE dbname_test;

# Restore
psql -U user -d dbname_test < backup_predeployment.sql

# Verify
psql -U user -d dbname_test -c "\dt"
```
- [ ] Restore succeeds
- [ ] All 7 tables present
- [ ] Data intact
- [ ] Indexes present

### 23. Cleanup Test Database
```bash
DROP DATABASE dbname_test;
```
- [ ] Test database removed

---

## ✅ Production Preparation

### 24. Environment Variables
```
Check .env file:
```
- [ ] DATABASE_URL set to production database
- [ ] DATABASE_URL uses correct credentials
- [ ] DATABASE_URL uses SSL if needed
- [ ] GOOGLE_API_KEY set
- [ ] SECRET_KEY set to secure value
- [ ] ENVIRONMENT set to "production"

### 25. Security Review
- [ ] Database password is strong (16+ chars, mixed case/numbers/symbols)
- [ ] User account has only necessary privileges
- [ ] SSL connections enabled for database
- [ ] Connection pooling configured for production load
- [ ] Automatic backups configured
- [ ] Database accessible only from app servers

### 26. Logging & Monitoring
- [ ] Application logging configured
- [ ] Database query logging enabled (for slow query log)
- [ ] Metrics collection verified
- [ ] Health check endpoint tested

### 27. Documentation
- [ ] DATABASE_SCHEMA.md reviewed
- [ ] DATABASE_SETUP.md reviewed
- [ ] Team trained on new schema
- [ ] Runbook created for operations
- [ ] Troubleshooting guide available

---

## ✅ Deployment Day

### 28. Pre-Deployment
- [ ] Team notified of deployment window
- [ ] Backups taken
- [ ] Monitoring systems ready
- [ ] Rollback plan documented
- [ ] Team standing by

### 29. Deployment
- [ ] Enable maintenance mode (optional)
- [ ] Run: `python scripts/init_database.py` on production
- [ ] Verify: `psql -U user -d dbname -c "\dt"`
- [ ] Start application
- [ ] Test critical workflows

### 30. Post-Deployment
- [ ] Monitor application logs (first 30 minutes)
- [ ] Check database connection logs
- [ ] Verify user data looks good
- [ ] Test crisis detection workflow
- [ ] Check response times
- [ ] Notify team of successful deployment

### 31. Follow-up
- [ ] Review metrics 24 hours after deployment
- [ ] Check for any slow queries
- [ ] Run ANALYZE if needed
- [ ] Update documentation with real-world observations
- [ ] Schedule database maintenance

---

## 🚨 Rollback Plan

If deployment fails:

### Step 1: Stop Application
```bash
# Stop the running app
kill <pid>
```
- [ ] Application stopped

### Step 2: Restore Database
```bash
# Drop the new database
DROP DATABASE dbname;

# Restore from backup
psql -U user < backup_predeployment.sql
```
- [ ] Backup restored
- [ ] Tables verified
- [ ] Data intact

### Step 3: Revert Code
```bash
git checkout previous_stable_version
```
- [ ] Code reverted
- [ ] Dependencies correct

### Step 4: Start Application
```bash
python -m uvicorn app.main:app
```
- [ ] Application starts
- [ ] Works with old database

### Step 5: Investigate
- [ ] Review logs for errors
- [ ] Check what went wrong
- [ ] Fix issues
- [ ] Test thoroughly
- [ ] Re-plan deployment

---

## 📋 Sign-off

### Deployment Successfully Completed

- [ ] Deployed by: __________ (name)
- [ ] Date: __/__/202__
- [ ] Time: __:__ (timezone)
- [ ] Environment: [ ] Dev  [ ] Staging  [ ] Production
- [ ] Verified by: __________ (name)
- [ ] Issues encountered: Yes / No
- [ ] If yes, describe: ___________________________

### Sign-off
- [ ] Development Lead: __________ (signature)
- [ ] Database Admin: __________ (signature)
- [ ] Operations: __________ (signature)

---

## 📞 Support Contacts

**Database Issues**: [DBA Email]
**Application Issues**: [Dev Team Email]
**Emergency**: [On-Call Number]

---

## 📚 Reference Documents

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [DATABASE_SETUP.md](DATABASE_SETUP.md)
- [DB_QUICK_REFERENCE.md](DB_QUICK_REFERENCE.md)
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- [BEFORE_AND_AFTER.md](BEFORE_AND_AFTER.md)

---

**Checklist Version**: 1.0
**Last Updated**: March 24, 2026
**Status**: Ready for Use
