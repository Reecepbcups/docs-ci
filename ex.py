# given some bash file, parse it. if the line ends with multiple line chars it it's a special function, then parse it properly and smush into 1 line


import re
from typing import List

key_words = ["if", "function"]

def load_file(file) -> List[str]:
    with open(file, 'r') as f:
        return f.readlines()
\
comment_regex = r'''
    ^                           # Start of line
    (                           # Group 1: Everything before the comment
        [^#"']*                 # Any chars except #, ", or '
        (                       # Group 2: All string contents
            (["'])              # Group 3: Quote character (single or double)
            (?:                 # Non-capturing group
                (?!\3)          # Not the same quote that opened the string
                .               # Any character
                |               # OR
                \\.             # Escaped character
            )*?                 # As few as possible
            \3                  # Matching closing quote
            [^#"']*             # Any chars except #, ", or '
        )*                      # Zero or more strings
    )                           # End of Group 1
    (\s*\#.*)$                  # Group 4: The comment (if exists)
'''

def find_comments(code):
    return re.findall(comment_regex, code, re.VERBOSE)

# cleans up the file and returns back the list of lines
def handle_initial_cleanup(content: str) -> List[str]:
    output = []
    for line in [line.strip() for line in content]:
        if len(line) == 0: continue
        if line.startswith('''#!'''): # shebang
            continue
        if line.startswith("#"):
            continue

        if "#" in line:
            matches = find_comments(line)
            if matches:
                for match in matches:
                    print(f"Found comment in: {line}")
                    comment = match[-1]
                    if len(comment) > 1:
                        print(f"\tComment: {comment}")
                        line = line.split("#")[0]
            # else:
            #     print(f"No comment found in: {line}")


        output.append(line)

    return output

def handle_re_merge(content: List[str]) -> str:
    output = ""
    for line in content:
        startedFunctionFind = False
        line = line.strip()

        if startedFunctionFind and "}" in line:
            startedFunctionFind = False
            output += f"{line}; "
            continue

        # if line starts with if, then we need to merge it with the next line(s) until fi
        if line.startswith("if"):
            if line.endswith("then"):
                output += f"{line} "
                continue
        elif line.startswith("else"):
            output += f"{line} "
            continue
        elif "function " in line and "{" in line:
            startedFunctionFind = True
            output += f"{line} "
            continue



        output += f"{line}; "

    return output.strip()


file_lines = load_file("ex.bash")

import shlex

# use shlex to put the file_lines into 1 single line
print(shlex.join(file_lines))

# cleaned_lines = handle_initial_cleanup(loaded_file)
# print(cleaned_lines)

# merged =  handle_re_merge(cleaned_lines)
# print(f"\n\n{merged=}")
