CodingChallenges JSON Parser
=============================

Project Description
-------------------

See the project description here 
https://codingchallenges.fyi/challenges/challenge-json-parser/

Key Takeaways
-------------

- JSON is a context free grammar
- JSON can be parsed with a recursive descent parser as done here
- A pushdown automaton would be a better approach (avoids recursion) 
  + needs a transition table and a stack
  + transitions are made based on the top of the stack and the current value
