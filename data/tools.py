jira_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_jira_tickets",
            "description": "Create structured Jira tickets from meeting action items",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string", "description": "Action-oriented title"},
                                "description": {"type": "string", "description": "Context and goal of the task"},
                                "acceptance_criteria": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of requirements to consider the task done"
                                },
                                "priority": {"type": "string", "enum": ["High", "Medium", "Low"]}
                            },
                            "required": ["summary", "description", "acceptance_criteria", "priority"]
                        }
                    }
                },
                "required": ["tickets"]
            }
        }
    }
]

email_tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_follow_up_email",
            "description": "Generate a structured follow-up email from meeting summary and action items",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Concise email subject line"
                    },
                    "recipients": {
                        "type": "string",
                        "description": "Who the email is addressed to (e.g. 'Team', 'All Attendees')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Main email body: brief meeting recap and key decisions"
                    },
                    "action_items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Action items formatted as 'Owner: Task (Deadline)'"
                    },
                    "closing": {
                        "type": "string",
                        "description": "Professional closing line"
                    }
                },
                "required": ["subject", "recipients", "body", "action_items", "closing"]
            }
        }
    }
]
