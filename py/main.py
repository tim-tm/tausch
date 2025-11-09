#!/usr/bin/env python3

from tausch import Tausch, TauschError
import subprocess

try:
    # provides extended input() method with
    # e.g. history
    import readline
except:
    pass  # readline not available

matches = []
var = {"hello": 42, "world": 69, "cond": True, "ncond": False}


def cmpl(text, state):
    global matches

    if state == 0:
        if text:
            matches = [v for v in var if v and v.startswith(text)]
        else:
            matches = var[:]

    try:
        return matches[state]
    except IndexError:
        return None


if __name__ == "__main__":
    readline.set_completer(cmpl)
    readline.parse_and_bind("tab: complete")

    print(f"Available variables: {var}")
    tausch = Tausch(var)
    while True:
        statement = input("> ")
        if statement.lower() == "exit":
            break

        try:
            result, root_node = tausch.eval(statement)
            print(f"Result: {result}")
            print("-- Tree start --")
            print(root_node.to_ascii())
            print("-- Tree end --")
        except TauschError as e:
            print(f"Failed at {e.location}: {e.message}")
            if e.suggestion:
                print(f"Suggestion: {e.suggestion}")
