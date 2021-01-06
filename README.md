# File List Expander
Typically need to process bunch of files with versatility of how to get list of files to process? 
This is a simple library to avoid copy-pasting of your own code here and there.

### gets as input:
- python list of strings
- text file with file list and comments
- directory address
- wildcarded string
- one file address

### allows to:
- detect and remove directories
- exclude non-existing files
- various regexp filterings: (includes, matches, not-includes, not-matches)
- verbose process of matching

### Why to use it if I have sed/grep/ls and all those fancy GNU tools?
It's easier to incorporate those simple funcs into your own interface, than asking users to understand how to work with fancy tools.

### How to use it?
See [demo](demo.ipynb).

### U r doin' it wrong, hold my beer!
I will appreciate comments/points where to get similar result but better.
