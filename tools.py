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