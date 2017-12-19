import drawBot
drawBot.size(200, 200)
drawBot.linearGradient(
    (100, 100),                         # startPoint
    (200, 200),                         # endPoint
    [(1, 0, 0), (0, 0, 1), (0, 1, 0)],  # colors
    [0, .2, 1]                          # locations
)
drawBot.rect(0, 0, 200, 200)
