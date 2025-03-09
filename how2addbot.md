# How to Add a New Bot

## Directory Structure

```
app/
├── config/
│   ├── diamond-hands-config.yaml
│   ├── aoe2-wizard-config.yaml
│   ├── badener-config.yaml
│   └── [new-bot]-config.yaml
├── knowledge/
│   ├── diamond-hands.yaml
│   ├── aoe2-wizard.yaml
│   ├── badener.yaml
│   └── [new-bot].yaml
```

## Adding a New Bot

1. Create a new configuration file in the `app/config/` directory named `[your-bot-id]-config.yaml`. 
   Follow this template:

```yaml
id: "your-bot-id"
title: "Your Bot Title"
description: "A description of what your bot does and knows."
base_prompt: >
  Detailed instructions for your bot's personality and behavior.
  This becomes the system prompt for the AI.
  Write multiple lines as needed.
examples:
  - "Example question 1?"
  - "Example question 2?"
  - "Example question 3?"
chat_path: "/your-bot-id/"
```

2. Optionally, create a knowledge file in `app/knowledge/` named `[your-bot-id].yaml` with additional information your bot should know:

```yaml
topics:
  topic_name:
    info: "Specific information about this topic"
    details:
      - "Detail 1"
      - "Detail 2"
  another_topic:
    info: "Information about another topic"
```

3. Restart the application, and your new bot will be automatically loaded and available in the interface.

## Configuration Options

| Field | Description |
|-------|-------------|
| id | Unique identifier for the bot (used in URLs and file names) |
| title | Display name shown in the UI |
| description | Short description of the bot's capabilities |
| base_prompt | System prompt that defines the bot's personality |
| examples | List of example prompts shown as buttons |
| chat_path | URL path where the chat interface is mounted |

## Notes

- The bot ID should be URL-friendly (no spaces or special characters)
- Make sure the ID matches between the config file name and the ID field inside
- The knowledge file is optional but follows the same naming convention