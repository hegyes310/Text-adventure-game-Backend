import random

def board_setup(rows, cols, num_mines):
    board = [[' ' for _ in range(cols)] for _ in range(rows)]
    mine_locations = random.sample(range(rows * cols), num_mines)

    for mine_location in mine_locations:
        row = mine_location // cols
        col = mine_location % cols
        board[row][col] = 'X'

    return board

def print_board(board, revealed):
    header = "   " + " ".join(str(i) for i in range(len(board[0])))
    print(header)
    print("  +" + "---" * len(board[0]) + "-+")
    for i, row in enumerate(board):
        line = str(i) + " | " + " | ".join(cell if revealed[i][j] else ' ' for j, cell in enumerate(row)) + " |"
        print(line)
    print("  +" + "---" * len(board[0]) + "-+")

def count_adjacent_mines(board, row, col):
    count = 0
    for i in range(max(0, row - 1), min(row + 2, len(board))):
        for j in range(max(0, col - 1), min(col + 2, len(board[0]))):
            if board[i][j] == 'X':
                count += 1
    return count

def reveal_square(board, revealed, row, col):
    if revealed[row][col]:
        return
    revealed[row][col] = True

    if board[row][col] == 'X':
        print("Game Over! You hit a mine.")
        print_board(board, revealed)
        exit()

    mine_count = count_adjacent_mines(board, row, col)

    if mine_count == 0:
        for i in range(max(0, row - 1), min(row + 2, len(board))):
            for j in range(max(0, col - 1), min(col + 2, len(board[0]))):
                reveal_square(board, revealed, i, j)
    else:
        board[row][col] = str(mine_count)

def main():
    rows = 8
    cols = 8
    num_mines = 10

    board = board_setup(rows, cols, num_mines)
    revealed = [[False for _ in range(cols)] for _ in range(rows)]

    while True:
        print_board(board, revealed)

        row = int(input("Enter row (0 to {}): ".format(rows - 1)))
        col = int(input("Enter column (0 to {}): ".format(cols - 1)))

        if row < 0 or row >= rows or col < 0 or col >= cols:
            print("Invalid input. Please enter valid row and column.")
            continue

        reveal_square(board, revealed, row, col)

        if all(all(revealed[i][j] or board[i][j] == 'X' for j in range(cols)) for i in range(rows)):
            print("Congratulations! You've cleared the minefield.")
            break

if __name__ == "__main__":
    main()