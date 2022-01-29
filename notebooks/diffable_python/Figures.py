# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import schemdraw
from schemdraw import flow

with schemdraw.Drawing() as d:
    d += flow.Box(w=10, h=1.5).label('Registered Trials on the EUCTR\n(N=38,566)')
    d += flow.Arrow('down', l=4).at((5,-.75))
    d += flow.Arrow('right').at((5,-2.75))
    d += flow.Box(w=6, h=1.5).label('Not Authorised \n(n=20)')
    d += flow.Box(w=6, h=1).label('n=38,546').at((2,-5.2))
    d += flow.Line('down', l=2).at((5, -5.7))
    d += flow.Arrow('right')
    d += flow.Box(w=6, h=2).label('Missing date info\n(n=729)')
    d += flow.Arrow(l=3).theta(-45).at((5,-7.7))
    d += flow.Box(w=6, h=2).label('Inferred Completion Date\n(n=16,051)').at((5.8,-9.8))
    d += flow.Arrow(l=3).theta(225).at((5,-7.7))
    d += flow.Box(w=6, h=2).label('Extracted Completion Date\n(n=21,766)').at((4.2,-9.8))
    d += flow.Line('down', l=2).at((1.3, -11.8))
    d += flow.Arrow('left', l=1)
    d += flow.Box(w=4, h=1.3).label('Not Sampled\n(n=21,413)')
    d += flow.Line('down', l=2).at((9, -11.8))
    d += flow.Arrow('right', l=1)
    d += flow.Box(w=4, h=1.3).label('Not Sampled\n(n=15,904)')
    d += flow.Arrow(l=4).theta(-45).at((1.3,-13.8))
    d += flow.Arrow(l=4).theta(225).at((9,-13.8))
    d += flow.Box(w=5, h=2).label('Final Sample\n(n=500)').at((7.7,-16.6)).label('\nExtracted = 353\nInferred = 147\nReplaced During Searches = 19', loc='bottom')




