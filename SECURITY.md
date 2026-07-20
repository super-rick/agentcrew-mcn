# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in AgentCrew MCN, please **do not** open a public issue.

Instead, report it privately:
1. **Email**: Create a GitHub Security Advisory at [github.com/super-rick/agentcrew-mcn/security/advisories/new](https://github.com/super-rick/agentcrew-mcn/security/advisories/new)
2. Include a detailed description, steps to reproduce, and potential impact

We will respond within 48 hours and work with you on a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.5.x  | ✅ Active |
| v0.4.x  | ⚠️ Security fixes only |
| < v0.4  | ❌ End of life |

## Security Best Practices

- Never commit `.env` files or API keys to the repository
- Use environment variables for all credentials
- Review platform cookies before sharing — they grant full account access
- The Reviewer Agent is configurable — set your own sensitive word lists via config
