import json
from typing import Any


def normalize_text(text: Any) -> str:
    """
    Normalizes text by converting to lowercase and replacing accented characters.

    Args:
        text: Any input that can be converted to string

    Returns:
        str: Normalized text in lowercase without accents
    """
    if text is None:
        return text

    text = str(text).lower()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }
    for accented, normal in replacements.items():
        text = text.replace(accented, normal)
    return text


def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


def run_demo_loop(
    client, starting_agent, context_variables=None, stream=False, debug=False
) -> None:
    client = client
    print(
        """
        💻 Departamento de Gestion de Base de Datos 💻 
          
        Funcionalidades:
          -Consultar, agregar, actualizar y eliminar productos en su base de datos ⚙️.

        (Escriba 'Salir' para terminar la conversacion 👋.)
          """
    )
    print("")
    messages = []
    agent = starting_agent

    while True:
        user_input = input("\033[90mUsuario\033[0m: ")
        messages.append({"role": "user", "content": user_input})
        if user_input.lower() == "salir":
            break
        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        if stream:
            response = process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        messages.extend(response.messages)
        agent = response.agent
