# 🛡️ Web Vulnerability Demo (Flask)

This project demonstrates common web vulnerabilities and their mitigations using Flask.  
We focus on **SQL Injection, XSS, CSRF, and Authentication issues**.

## 🔹 1. SQL Injection

**Vulnerable Route:** `/search_vuln`
Briefly describe what the project does.
We no longer interpolate the user string into SQL. Instead we use a bound parameter :name. The DB driver treats the parameter as a value, not SQL code, so special characters inside name can't change the SQL structure.

## Setup

```bash
pip install -r requirements.txt
```
