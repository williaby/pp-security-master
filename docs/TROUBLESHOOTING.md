# PostgreSQL 17 Database Connection Troubleshooting Guide

This guide provides solutions for common database connection issues encountered during development setup.

## Quick Validation Commands

### Test Network Connectivity
```bash
# Test if PostgreSQL server is reachable on the network
timeout 5 nc -zv 192.168.1.16 5436
# Expected: "Connection to 192.168.1.16 5436 port [tcp/*] succeeded!"
```

### Test Database Connection
```bash
# Run the database connectivity test
poetry run python tests/test_db_connection.py
```

### Environment Variable Verification
```bash
# Check required environment variables
echo "Host: $POSTGRES_HOST, Port: $POSTGRES_PORT, User: $POSTGRES_USER, DB: $POSTGRES_DB"
```

## Common Issues and Solutions

### 1. Authentication Failed (`FATAL: password authentication failed`)

**Symptoms:**
```
Failed to connect with parameters: connection to server at "192.168.1.16", port 5436 failed: 
FATAL:  password authentication failed for user "pp_user"
```

**Root Cause:** Incorrect database credentials or user doesn't exist.

**Solutions:**
1. **Verify credentials in Unraid PostgreSQL container:**
   - Access Unraid web interface
   - Navigate to Docker containers
   - Check PostgreSQL 17 container environment variables
   - Verify `POSTGRES_USER` and `POSTGRES_PASSWORD` settings

2. **Reset PostgreSQL user credentials:**
   ```bash
   # Connect to container as postgres superuser
   docker exec -it postgresql17 psql -U postgres
   
   # Create/reset user
   CREATE USER pp_user WITH PASSWORD 'your_password_here';
   GRANT ALL PRIVILEGES ON DATABASE pp_master TO pp_user;
   ```

3. **Check password special characters:**
   - Passwords with special characters (`!@#$%^&*`) may need URL encoding
   - Test with a simple password first (alphanumeric only)

### 2. Connection Timeout or Refused

**Symptoms:**
```
Failed to connect: connection to server at "192.168.1.16", port 5436 failed: 
Connection refused or timeout
```

**Root Cause:** Network connectivity issues or PostgreSQL not running.

**Solutions:**
1. **Verify PostgreSQL container is running:**
   ```bash
   docker ps | grep postgres
   ```

2. **Check port configuration:**
   - Default PostgreSQL port: 5432
   - Verify Unraid container port mapping matches `.env` configuration

3. **Network connectivity test:**
   ```bash
   ping 192.168.1.16
   telnet 192.168.1.16 5436
   ```

### 3. Database Does Not Exist

**Symptoms:**
```
FATAL: database "pp_master" does not exist
```

**Solutions:**
1. **Create database in PostgreSQL:**
   ```bash
   # Connect as postgres superuser
   docker exec -it postgresql17 psql -U postgres
   
   # Create database
   CREATE DATABASE pp_master;
   GRANT ALL PRIVILEGES ON DATABASE pp_master TO pp_user;
   ```

2. **Verify database name in `.env` matches created database**

### 4. Invalid Connection URL Format

**Symptoms:**
```
Failed to connect with URL: invalid dsn: invalid percent-encoded token
```

**Root Cause:** Special characters in password not properly URL-encoded.

**Solutions:**
1. **Use individual environment variables instead of DATABASE_URL:**
   ```bash
   # In .env file, comment out DATABASE_URL and use:
   POSTGRES_HOST=192.168.1.16
   POSTGRES_PORT=5436
   POSTGRES_USER=pp_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=pp_master
   ```

2. **Properly encode DATABASE_URL if using:**
   ```python
   import urllib.parse
   password = urllib.parse.quote_plus("password!with@special#chars")
   ```

### 5. Module Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solutions:**
1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Verify Poetry environment:**
   ```bash
   poetry run pip list | grep psyco
   # Should show: psycopg2-binary
   ```

## Environment Configuration

### Required Environment Variables
```bash
# Database Connection (Option 1: Individual variables)
POSTGRES_HOST=192.168.1.16     # Your Unraid server IP
POSTGRES_PORT=5436             # PostgreSQL port (usually 5432)
POSTGRES_DB=pp_master          # Database name
POSTGRES_USER=pp_user          # Database user
POSTGRES_PASSWORD=your_password # Database password

# Database Connection (Option 2: Connection URL)
DATABASE_URL=postgresql://pp_user:password@192.168.1.16:5436/pp_master
```

### .env File Template
```bash
# Copy .env.example to .env and update values
cp .env.example .env
# Edit .env with your actual database credentials
```

## Database Server Requirements

### PostgreSQL 17 Container Configuration (Unraid)
- **Image:** `postgres:17` or `postgres:17-alpine`
- **Environment Variables:**
  - `POSTGRES_DB=pp_master`
  - `POSTGRES_USER=pp_user`
  - `POSTGRES_PASSWORD=secure_password_here`
- **Port Mapping:** `5436:5432` (or your preferred external port)
- **Persistent Storage:** `/mnt/user/appdata/pp_postgres/data:/var/lib/postgresql/data`

### Network Configuration
- Ensure Unraid server is accessible from development machine
- Check firewall rules on both client and server
- Verify Docker network configuration in Unraid

## Validation Checklist

Before proceeding with development, ensure:

- [ ] PostgreSQL 17 container is running in Unraid
- [ ] Network connectivity test passes (`nc -zv IP PORT`)
- [ ] Database user and database exist
- [ ] Environment variables are correctly set in `.env`
- [ ] Poetry dependencies are installed (`poetry install`)
- [ ] Database connection test passes (`poetry run python tests/test_db_connection.py`)

## Advanced Debugging

### Enable PostgreSQL Logging
1. **Modify postgresql.conf in container:**
   ```sql
   -- Enable connection logging
   log_connections = on
   log_disconnections = on
   log_statement = 'all'
   ```

2. **View PostgreSQL logs:**
   ```bash
   docker logs postgresql17
   ```

### Database Diagnostic Queries
```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'pp_master';

-- Verify user permissions
SELECT * FROM pg_roles WHERE rolname = 'pp_user';

-- List databases
\l

-- List users
\du
```

## Getting Help

If issues persist after following this guide:

1. **Check container logs:** `docker logs postgresql17`
2. **Verify Unraid Docker configuration**
3. **Test with a database GUI tool (DBeaver, pgAdmin) first**
4. **Document specific error messages for support**

## Security Notes

- Never commit actual database credentials to version control
- Use strong passwords for database users
- Regularly update PostgreSQL to latest security patches
- Configure proper network security (firewall, VPN) for production