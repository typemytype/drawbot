import drawBot
drawBot.size(200, 200)
drawBot.cmykLinearGradient(
    (100, 100),                         # startPoint
    (200, 200),                         # endPoint
    [(1, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, .2)],    # cmyk colors
    [0, .2, 1]                          # locations
)
drawBot.rect(0, 0, 200, 200)
