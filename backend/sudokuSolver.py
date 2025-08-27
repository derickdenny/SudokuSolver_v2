def solve(board):
    n = len(board)
    row = -1
    col = -1
    empty_left = True

    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:
                row = i
                col = j
                empty_left = False
                break
        if not empty_left:
            break

    if empty_left:
        return True

    for num in range(1, 10):
        if is_safe(board, row, col, num):
            board[row][col] = num
            if solve(board):
                return True
            else:
                board[row][col] = 0
    return False

def is_safe(board, row, col, num):
    for x in range(len(board)):
        if board[row][x] == num:
            return False
    for x in range(len(board)):
        if board[x][col] == num:
            return False
    row_start = (row // 3) * 3
    col_start = (col // 3) * 3
    for i in range(row_start, row_start + 3):
        for j in range(col_start, col_start + 3):
            if board[i][j] == num:
                return False
    return True

def display(board):
    for row in board:
        for num in row:
            print(num, end=" ")
        print()
