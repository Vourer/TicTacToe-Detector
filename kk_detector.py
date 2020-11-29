import numpy as np
import cv2

def rearange_contours(contours):
    # sortowanie konturów względem pola, jakie pokrywają
    new_contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)
    for i, cont in enumerate(new_contours):
        if cv2.contourArea(cont) < 100:
            new_contours = new_contours[:i]
            break
    return new_contours


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


def process_image(img_path, scale):
    image = cv2.imread(img_path)
    height, width = int(image.shape[0]*scale), int(image.shape[1]*scale)
    #print(image.shape)
    image = cv2.resize(image, (width, height))
    rgb_image = image.copy()
    gray = 255 - cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(gray, (5,5), sigmaX=width//300)
    image = auto_canny(image)
    k = np.ones((2,2))
    image = cv2.dilate(image, kernel=k, iterations=1)
    #image2 = cv2.erode(image, kernel=k, iterations=1)

    cont_image = rgb_image.copy()  # do obrazu z konturami
    rect_image = rgb_image.copy()  # do obrazu z prostokątami
    bin_image = np.uint8((gray > 130) * 255)  # czarno-białe do sprawdzania
    #mask = np.zeros((height, width), np.uint8)  # drugie czarno-białe, pomocnicze
    #mask[:, :] = 255

    contours, hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = rearange_contours(contours)
    boards = 1
    while True:
        if cv2.contourArea(contours[boards]) > 0.75*cv2.contourArea(contours[boards-1]):
            boards += 1
        else:
            break
    for i, cont in enumerate(contours):
        cv2.drawContours(cont_image, cont, -1, (0, 255, 0), 2)
        peri = cv2.arcLength(cont, True)
        approx = cv2.approxPolyDP(cont, 0.02*peri, True)
        x, y, w, h = cv2.boundingRect(approx)
        if i < boards:
            cv2.rectangle(rect_image, (x,y), (x+w, y+h), (0,255,0), 2)
            continue
        #cv2.rectangle(rect_image, (x,y), (x+w, y+h), (0,0,255), 2)
        # wylicz średni kolor środka zaznaczenia (0.3w, 0.3h)
        avg = np.mean(bin_image[int(y+0.35*h):int(y+0.65*h), int(x+0.35*w):int(x+0.65*w)])
        if avg > 50:
            cv2.putText(rect_image, "x", (x+4, y+3), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 2)
        else:
            cv2.putText(rect_image, "o", (x+4, y+3), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 2)
        bin_image[int(y+0.35*h):int(y+0.65*h), int(x+0.35*w):int(x+0.65*w)] = 128

    #out = stack_images(0.5, [[cont_image, bin_image, rect_image], ])
    out = stack_images(0.5, [[rgb_image, cont_image], [bin_image, rect_image]])
    return out #rect_image


def main():
    img_paths = ['Images/m01.jpg', 'Images/m02.jpg',
                 'Images/s01.jpg', 'Images/s02.jpg']
    outer=[]
    single = ['Images/s02.jpg']
    for i, path in enumerate(single):
        img_out = process_image(path, 0.25)
        outer.append(img_out)
        cv2.imshow(f'Output image {i+1}', img_out)
    #cv2.imshow('text', stack_images(0.7, (outer[:2],outer[2:])))
    cv2.waitKey(0)


if __name__=='__main__':
    main()