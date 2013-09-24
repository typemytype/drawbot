# set a gradient as the fill color
radialGradient(
    (100, 100),                         # startPoint
    (200, 200),                         # endPoint
    [(1, 0, 0), (0, 0, 1), (0, 1, 0)],  # colors
    [0, .2, 1],                         # locations
    0,                                  # startRadius
    100                                 # endRadius
    )
# draw a rectangle
rect(100, 100, 100, 100)