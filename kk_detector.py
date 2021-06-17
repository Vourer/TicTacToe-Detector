import numpy as np
import cv2
from more_itertools import sort_together
import board as brd
import middle_cell as mdc


def rearange(contours, hierarchy):
    # lepsze sortowanie konturów (razem z hieratchiami) względem pola, jakie pokrywają
    areas = [cv2.contourArea(c) for c in contours]
    new_cont, new_hier = sort_together([contours, hierarchy[0], areas], key_list=(2,), reverse=True)[:2]
    for i, cont in enumerate(new_cont):
        if cv2.contourArea(cont) < 100:
            new_cont = new_cont[:i]
            new_hier = new_hier[:i]
            break
    return new_cont, new_hier


def stack_images(scale, img_array):
    # łączenie kilku obrazów w jeden duży
    rows = len(img_array)
    cols = len(img_array[0])
    rows_available = isinstance(img_array[0], list)
    width = img_array[0][0].shape[1]
    height = img_array[0][0].shape[0]
    if rows_available:
        for x in range (0, rows):
            for y in range(0, cols):
                if img_array[x][y].shape[:2] == img_array[0][0].shape[:2]:
                    img_array[x][y] = cv2.resize(img_array[x][y], (0, 0), None, scale, scale)
                else:
                    img_array[x][y] = cv2.resize(img_array[x][y], (img_array[0][0].shape[1], img_array[0][0].shape[0]), None, scale, scale)
                if len(img_array[x][y].shape) == 2: img_array[x][y]= cv2.cvtColor(img_array[x][y], cv2.COLOR_GRAY2BGR)
        image_blank = np.zeros((height, width, 3), np.uint8)
        hor = [image_blank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(img_array[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if img_array[x].shape[:2] == img_array[0].shape[:2]:
                img_array[x] = cv2.resize(img_array[x], (0, 0), None, scale, scale)
            else:
                img_array[x] = cv2.resize(img_array[x], (img_array[0].shape[1], img_array[0].shape[0]), None, scale, scale)
            if len(img_array[x].shape) == 2:
                img_array[x] = cv2.cvtColor(img_array[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(img_array)
        ver = hor
    return ver


def auto_canny(image, sigma=0.33):
    # filtr Canny z automatycznym dobieraniem threshold'ów
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    return edged


def process_image(img_path, num, scale, stacked_output=False):
    print(f"------------ IMAGE #{num+1} ------------")
    # prygotowanie obrazu do rozpoznawania
    image = cv2.imread(img_path)
    height, width = int(image.shape[0]*scale), int(image.shape[1]*scale)
    image = cv2.resize(image, (width, height))
    rgb_image = image.copy()
    gray = 255 - cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), sigmaX=width//300)
    image = auto_canny(gray)
    k = np.ones((2,2))
    image = cv2.dilate(image, kernel=k, iterations=1)

    cont_image = rgb_image.copy()  # do obrazu z konturami
    rect_image = rgb_image.copy()  # do obrazu z prostokątami
    board_image = rgb_image.copy()
    bin_image = np.uint8((gray > 130) * 255)  # czarno-białe do sprawdzania

    contours, hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours, new_hierarchy = rearange(contours, hierarchy)

    num_boards = 1
    board_list = []
    # kontury posortowane od największego do najmniejszego - pierwsze z brzegu powinny być kontury szachownic
    while num_boards <= len(contours):
        if cv2.contourArea(contours[num_boards]) > 0.7 * cv2.contourArea(contours[num_boards - 1]):
            num_boards += 1
        else:
            break

    # znajdywanie środkowych pól
    middle_cells = []
    all_contours, all_hierarchies = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    all_contours, all_hierarchies = rearange(all_contours, all_hierarchies)
    for i, acont in enumerate(all_contours):
        # kontury środkowych pól zajmują (zwykle) największą powierzchnię, zaraz po planszach
        # a że w tym trybie RETR każdy kontur występuje dwa razy, trzeba pominąć dwukrotną liczbę plansz
        if 2*num_boards <= i <= 5*num_boards:
            cv2.drawContours(cont_image, acont, -1, (255, 0, 0), 2)
            perimeter = cv2.arcLength(acont, True)
            approx = cv2.approxPolyDP(acont, 0.025 * perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)  # koordynaty wierzchołków prostokąta obejmującego środek
            (cx, cy), radius = cv2.minEnclosingCircle(acont)  # współrzędne środka i promień koła obejmującego środek
            cx, cy = (int(cx), int(cy))
            mid = mdc.MiddleCell(bin_image[y:y+h, x:x+w], center=(cx,cy), coords=(x,w,y,h))
            middle_cells.append(mid)

    # obsługa plansz oraz pozostałych, zewnętrznych zaznaczeń/symboli
    for i, cont in enumerate(contours):
        cv2.drawContours(cont_image, cont, -1, (0, 255, 0), 2)

        cv2.drawContours(board_image, cont, -1, (0, 255, 0), 2)
        perimeter = cv2.arcLength(cont, True)
        approx = cv2.approxPolyDP(cont, 0.025*perimeter, True)
        x, y, w, h = cv2.boundingRect(approx)  # koordynaty wierzchołków prostokąta obejmującego zaznaczenie
        (cx, cy), radius = cv2.minEnclosingCircle(cont)  # współrzędne środka i promień koła obejmującego zaznaczenie
        cx, cy = (int(cx), int(cy))
        r = int(radius)

        if i < num_boards:
            # obrysuj i podpisz planszę
            cv2.rectangle(rect_image, (x,y), (x+w, y+h), (255,255,0), 2)
            cv2.rectangle(board_image, (x+int(0.3*w), y+int(0.3*h)), (x+int(0.7*w), y+int(0.7*h)), (255, 255, 0), 2)
            cv2.putText(rect_image, f'{i+1}', (x + 4, y + 3), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            new_board = brd.Board(board_img=rgb_image[y:y+h,x:x+w], center=(cx,cy), coords=(x,w,y,h))
            board_list.append(new_board)
            # znajdź i oznacz środkowe pole planszy
            for mid in middle_cells:
                cell_x, cell_y = mid.center
                if new_board.contains_cont(cell_x, cell_y, k=0.4):
                    new_board.update_middle(mid.symbol)
                    cv2.circle(rect_image, (cell_x, cell_y), int(mid.w//2), (0, 255, 255), 2)
                    cv2.putText(rect_image, mid.symbol, (mid.xmin + 4, mid.ymin + 3), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    break
            continue

        for board in board_list:
            if board.contains_cont(cx, cy):
                cv2.circle(rect_image, (cx, cy), r, (0, 255, 0), 2)
                # wylicz średni kolor środka zaznaczenia (wymiary: 0.3h x 0.3w)
                avg = np.mean(bin_image[int(y+0.35*h):int(y+0.65*h), int(x+0.35*w):int(x+0.65*w)])
                if avg > 60:
                    symbol = 'x'
                else:
                    symbol = 'o'
                cv2.putText(rect_image, symbol, (x + 4, y + 3), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                bin_image[int(y+0.35*h):int(y+0.65*h), int(x+0.35*w):int(x+0.65*w)] = 128
                board.update_cells(cx, cy, symbol)

    for i, b in enumerate(board_list):
        print(b, f"\nBoard #{i+1}")
        b.check_outcome()

    if stacked_output:
        return stack_images(0.5, [[image, cont_image], [bin_image, rect_image]])
    else:
        return rect_image


def main():
    img_paths = ['Images/k01.jpg', 'Images/k02.jpg',
                 'Images/k03.jpg', 'Images/k04.jpg',
                 'Images/k05.jpg', 'Images/k06.jpg']
    outer=[]
    single = ['Images/s01.jpg']
    for i, path in enumerate(img_paths):
        img_out = process_image(path, i, 0.25)
        outer.append(img_out)
        cv2.imshow(f'Output image {i+1}', img_out)
    cv2.waitKey(0)


if __name__=='__main__':
    main()
