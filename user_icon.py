import hashlib as hl
import colorsys as cs
import sys

def gen_icon(uname):
    H = map(ord, hl.sha256(uname).digest())
    C = reduce(lambda x, y: x^y, H) / 255.0 / 2.0
    rgb = "rgb"+str(tuple(int(255*c) for c in cs.hsv_to_rgb(C, 0.7, 0.95)))
    rgb_inv = "rgb"+str(tuple(int(255*c) for c in cs.hsv_to_rgb(C+0.5, 0.2, 0.45)))
    L = [ch%2 for ch in H]
    #Single axis symmetry
    P = [L[:7],L[7:14],L[14:21],L[21:],L[14:21],L[7:14],L[:7]]
    #Double axis symmetry
    #P = [L[:4]+L[2::-1],
    #     L[4:8]+L[6:3:-1],
    #     L[8:12]+L[10:7:-1],
    #     L[12:16]+L[14:11:-1],
    #     L[8:12]+L[10:7:-1],
    #     L[4:8]+L[6:3:-1],
    #     L[:4]+L[2::-1]]
    svg = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 90 90" preserveAspectRatio="xMinYMin meet">'
    svg += '<rect width="90" height="90" rx="10" ry="10" fill="'+rgb_inv+'"/>'
    rect = '<rect width="10" height="10" x="{x}" y="{y}" fill="{color}" shape-rendering="crispEdges"/>'
    for i in xrange(7):
        for j in xrange(7):
            if P[j][i] == 1:
                svg += rect.format(x=(j+1)*10, y=(i+1)*10, color=rgb)
    svg+='</svg>'
    return svg
