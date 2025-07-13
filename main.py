#!/usr/bin/env python3

from tausch import Tausch, TauschError
import subprocess

try:
    # provides extended input() method with
    # e.g. history
    import readline
except:
    pass  # readline not available

if __name__ == "__main__":
    var = {"hello": 42, "world": 69, "cond": True, "ncond": False}
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
