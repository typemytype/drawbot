# set a gradient as the fill color
linearGradient(
    (100, 100),                         # startPoint
    (200, 200),                         # endPoint
    [(1, 0, 0), (0, 0, 1), (0, 1, 0)],  # colors
    [0, .2, 1]                          # locations
    )
# draw a rectangle
rect(100, 100, 100, 100)