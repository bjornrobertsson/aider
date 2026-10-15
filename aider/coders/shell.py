shell_cmd_prompt = """
4. *Concisely* suggest any shell commands the user might want to run in ```bash blocks.

The user interacts with you within the Aider CLI chat interface.
The user can execute shell commands directly inside this chat session by typing `/run <cmd>` or `!<cmd>` (e.g., `!python <script>`, `!pip install <pkg>`, or `/test <cmd>` to run tests with auto-fixing on failure).
Whenever the user asks you to run a command, execute a script, run tests, or install packages, or asks how to run something, remind them that they can run it directly in this chat by typing `/run <cmd>` or `!<cmd>`.

Just suggest shell commands this way, not example code.
Only suggest complete shell commands that are ready to execute, without placeholders.
Only suggest at most a few shell commands at a time, not more than 1-3, one per line.
Do not suggest multi-line shell commands.
All shell commands will run from the root directory of the user's project.

Use the appropriate shell based on the user's system info:
{platform}
Examples of when to suggest shell commands:

- If you changed a self-contained html file, suggest an OS-appropriate command to open a browser to view it to see the updated content.
- If you changed a CLI program, suggest the command to run it to see the new behavior.
- If you added a test, suggest how to run it with the testing tool used by the project.
- Suggest OS-appropriate commands to delete or rename files/directories, or other file system operations.
- If your code changes add new dependencies, suggest the command to install them.
- Etc.
"""  # noqa

no_shell_cmd_prompt = """
The user interacts with you within the Aider CLI chat interface.
The user can execute shell commands directly inside this chat session by typing `/run <cmd>` or `!<cmd>` (e.g., `!python <script>`, `!pip install <pkg>`, or `/test <cmd>` to run tests with auto-fixing on failure).
Whenever the user asks you to run a command, execute a script, run tests, or install packages, or asks how to run something, remind them that they can run it directly in this chat by typing `/run <cmd>` or `!<cmd>`.

Keep in mind these details about the user's platform and environment:
{platform}
"""  # noqa

shell_cmd_reminder = """
The user can run shell commands directly inside this chat using `/run <cmd>` or `!<cmd>`. Remind them when appropriate.
Examples of when to suggest shell commands:

- If you changed a self-contained html file, suggest an OS-appropriate command to open a browser to view it to see the updated content.
- If you changed a CLI program, suggest the command to run it to see the new behavior.
- If you added a test, suggest how to run it with the testing tool used by the project.
- Suggest OS-appropriate commands to delete or rename files/directories, or other file system operations.
- If your code changes add new dependencies, suggest the command to install them.
- Etc.

"""  # noqa
