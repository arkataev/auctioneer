def snake_to_camel(snake_str: str) -> str:
    """Converts snake_case_word into CamelCaseWord. Look Mam, No Regex!"""
    stack = []
    for word in snake_str.split('_'):
        if stack and stack[-1].isupper():
            stack.append(word.lower())
        stack.append(word.capitalize())
    return ''.join(stack)


def camel_to_snake(camel_str: str) -> str:
    """Converts CamelCaseString to snake_case_string"""
    stack = []
    for char in camel_str:
        if stack and char.isupper():
            stack.append('_')
        stack.append(char.lower())
    return ''.join(stack)
