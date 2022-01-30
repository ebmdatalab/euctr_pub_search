# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + trusted=true
import schemdraw
from schemdraw import flow

# + trusted=true
with schemdraw.Drawing() as d:
    d += flow.Box(w=10, h=1.5).label('Registered Trials on the EUCTR\n(N=38,566)')
    d += flow.Arrow('down', l=4).at((5,-.75))
    d += flow.Arrow('right').at((5,-2.75))
    d += flow.Box(w=6, h=2).label('Not Authorised \n(n=20)\nMissing Date Info\n(n=729)')
    d += flow.Box(w=5, h=1).label('n=37,817').at((2.5,-5.2))
    d += flow.Line('down', l=1).at((5, -5.7))
    d += flow.Arrow(l=3).theta(-45).at((5,-6.7))
    d += flow.Box(w=6, h=2).label('Inferred Completion Date\n(n=16,051)').at((5.8,-8.8))
    d += flow.Arrow(l=3).theta(225).at((5,-6.7))
    d += flow.Box(w=6, h=2).label('Extracted Completion Date\n(n=21,766)').at((4.2,-8.8))
    d += flow.Line('down', l=2).at((1.3, -10.8))
    d += flow.Arrow('left', l=1)
    d += flow.Box(w=5.5, h=1.5).label('Completed <24 Months\n(n=2,548)')
    d += flow.Line('down', l=2).at((9, -10.8))
    d += flow.Arrow('right', l=1)
    d += flow.Box(w=5.5, h=1.5).label('Completed <24 Months\n(n=7,992)')
    
    d += flow.Arrow('left', l=1).at((1.3, -15))
    d += flow.Box(w=5.5, h=1.5).label('Not Sampled\n(n=19,071)')
    d += flow.Arrow('down', l=1).at((-2.5, -15.8))
    
    d += flow.Arrow('right', l=1).at((9, -15))
    d += flow.Box(w=5.5, h=1.5).label('Not Sampled\n(n=7,706)')
    d += flow.Arrow('down', l=1).at((12.8, -15.8))
    
    d += flow.Line('down', l=4).at((9, -12.8))
    d += flow.Box(w=4.5, h=1.5).label('Inferred Included\n(n=353)')
    d += flow.Line('down', l=4).at((1.3, -12.8))
    d += flow.Box(w=4.5, h=1.5).label('Extracted Included\n(n=147)')
    
    #Extracted Replaced
    d += flow.Arrow('left', l=1).at((-1, -17.2))
    d += flow.Arrow('right', l=1).at((-2, -18))
    d += flow.Box(w=3, h=1.5).label('Replaced\n(n=14)').at((-5, -17.55))
    
    #Inferred Replaced
    d += flow.Arrow('right', l=1).at((11.3, -17.2))
    d += flow.Arrow('left', l=1).at((12.3, -18))
    d += flow.Box(w=3, h=1.5).label('Replaced\n(n=5)').at((15.3, -17.55))
    
    #Final
    d += flow.Arrow(l=3).theta(-45).at((1.3,-18.3))
    d += flow.Arrow(l=3).theta(225).at((9,-18.3))
    d += flow.Box(w=5, h=1.5).label('Final Sample\n(n=500)').at((7.7,-20.5))
# -




