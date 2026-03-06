SCHEMA_NAME = "automations"

USER_RELATIONSHIPS = [
    {
        "name": "automations",
        "target": "Automation",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
    {
        "name": "api_keys",
        "target": "ApiKey",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
    {
        "name": "auto_executions",
        "target": "Execution",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
    {
        "name": "inbound_webhooks",
        "target": "WebhookInbound",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]