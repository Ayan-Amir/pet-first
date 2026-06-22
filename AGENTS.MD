# 🛡️ ORGANIZATION-WIDE ENGINEERING STANDARDS

> These standards apply to **ALL repositories** in the organization.
> PR-Agent will use these as binding rules when reviewing code.

---

## 1. CODE INTEGRITY & TYPE SAFETY

- **Strict Typing:** Avoid `Any`. Use proper types. If `TypedDict(total=False)`, use `Optional` for optional fields.
- **No Assumptions:** Never assume a key exists in a dictionary. Use `.get()` with defaults or check presence first.
- **Type Consistency:** Ensure function signatures, return types, and variable types are consistent across the codebase.
- **Null Safety:** Always handle potential `None` values. Check before dereferencing.

---

## 2. SECURITY ZERO TRUST

- **Sanitize All Input:** All external input (User, API, DB, LLM output) is malicious until proven otherwise.
- **Secrets Management:** Never commit secrets to Git. Use Environment Variables or secure vaults.
- **Authentication & Authorization:** Always verify user identity and permissions before granting access.
- **SQL Injection Prevention:** Use parameterized queries or ORMs. Never concatenate user input into SQL.
- **XSS Prevention:** Sanitize and escape all user-generated content before rendering.
- **Logging Safety:** Never log sensitive data (passwords, tokens, PII, credit cards).

---

## 3. ERROR HANDLING & RESILIENCE

- **Fail Gracefully:** Never let the app crash on bad input. Catch exceptions and return meaningful errors.
- **Validate External Data:** Always validate data from APIs, files, and LLM responses before use.
- **Defensive Programming:** Assume external services can fail. Implement retries and fallbacks.
- **Meaningful Error Messages:** Log errors with sufficient context for debugging.
- **Circuit Breakers:** For external service calls, implement timeouts and circuit breakers.

---

## 4. CODE QUALITY & MAINTAINABILITY

- **DRY Principle:** Don't Repeat Yourself. Extract common logic into reusable functions.
- **Single Responsibility:** Each function/class should do one thing well.
- **Clear Naming:** Use descriptive names for variables, functions, and classes.
- **Comments for Why, Not What:** Code should be self-documenting. Comments explain intent and reasoning.
- **Avoid Deep Nesting:** Keep complexity low. Refactor deeply nested logic.
- **Magic Numbers:** Use named constants instead of hardcoded values.

---

## 5. TESTING & QUALITY ASSURANCE

- **Test Critical Paths:** All business-critical logic must have tests.
- **Edge Cases:** Test boundary conditions, empty inputs, and error paths.
- **Integration Tests:** Test external integrations with mocks or test environments.
- **No Broken Tests:** Never commit code that breaks existing tests.

---

## 6. PERFORMANCE & SCALABILITY

- **Avoid N+1 Queries:** Batch database queries when possible.
- **Cache Strategically:** Cache expensive computations and external API calls.
- **Lazy Loading:** Don't load data until it's needed.
- **Pagination:** Use pagination for large datasets.
- **Indexing:** Ensure database queries use proper indexes.

---

## 7. API & INTEGRATION STANDARDS

- **RESTful Design:** Use proper HTTP methods (GET, POST, PUT, DELETE) and status codes.
- **Versioning:** Version your APIs to allow backward compatibility.
- **Rate Limiting:** Implement rate limits to prevent abuse.
- **Idempotency:** Ensure POST/PUT operations are idempotent where appropriate.
- **Input Validation:** Validate all API inputs at the boundary.

---

## 8. DOCUMENTATION

- **API Documentation:** Document all public APIs with request/response examples.
- **README Updates:** Keep README current with setup and usage instructions.
- **Configuration:** Document all environment variables and configuration options.

---

## 9. ZERO TOLERANCE FOR BUGS

- **No Silent Failures:** Always log errors and alert on critical failures.
- **Data Integrity:** Validate data integrity at boundaries (API, DB, file I/O).
- **Regression Prevention:** Add tests for every bug fix to prevent recurrence.
- **Monitoring:** Implement monitoring and alerting for production issues.

---

## 10. DJANGO-SPECIFIC STANDARDS

- **Model Design:** Use appropriate field types. Never use `TextField` for constrained data (use `CharField` with `max_length`).
- **Migrations:** Always generate and review migrations after model changes. Never edit existing migrations in production.
- **QuerySet Optimization:** Use `select_related()` for ForeignKey/OneToOne, `prefetch_related()` for ManyToMany/reverse ForeignKey.
- **Database Transactions:** Use `@atomic` decorator for operations that must be atomic.
- **Views & ViewSets:** Use class-based views/viewsets for consistency. Always add permission classes.
- **Serializers:** Validate all input data through serializers. Never trust raw request data.
- **URL Patterns:** Use `name` parameter for all URL patterns. Use `reverse()` instead of hardcoded URLs.
- **Admin Configuration:** Register all models with customized admin classes for better UX.
- **Signals:** Use signals sparingly. Prefer explicit method calls for better clarity.
- **Raw SQL:** Avoid raw SQL. If necessary, use parameterized queries with `params` argument.
- **Settings Management:** Use environment variables for sensitive data. Never commit secrets.
- **CSRF Protection:** Ensure CSRF middleware is enabled. Use `@csrf_exempt` only for specific API endpoints with proper justification.

---

**Priority:** These standards are non-negotiable. Code reviews should catch violations before merge.
